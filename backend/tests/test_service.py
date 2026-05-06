from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

from backend.alert_service import AnyMaNoAlertService
from backend.config import FetchOptions
from backend.models import RUN_STATUS_FAILED, RUN_STATUS_SUCCESS
from backend.notifiers.wecom import WeComNotifier
from backend.repository import SQLiteTrendRepository
from backend.service import TrendDashboardService


def build_dataset(ma5_status: str, ma20_status: str) -> dict:
    return {
        'updatedAt': '2026-05-06 10:00:00',
        'latestDataDate': '2026-05-06',
        'defaultViewKey': 'ma20',
        'viewOrder': ['ma5', 'ma20'],
        'views': {
            'ma5': {
                'key': 'ma5',
                'label': '5日均线',
                'latestDataDate': '2026-05-06',
                'maWindow': 5,
                'items': [
                    {
                        'rank': 1,
                        'code': '000001',
                        'name': '上证指数',
                        'status': ma5_status,
                        'dayChangePct': 0.5,
                        'close': 3120.55,
                        'critical': 3130.0,
                        'deviationRate': -0.003,
                        'statusChangedAt': '2026-05-06',
                        'intervalGainPct': -1.2,
                        'trendStrength': '偏弱',
                        'history': [],
                    }
                ],
            },
            'ma20': {
                'key': 'ma20',
                'label': '20日均线',
                'latestDataDate': '2026-05-06',
                'maWindow': 20,
                'items': [
                    {
                        'rank': 1,
                        'code': '000001',
                        'name': '上证指数',
                        'status': ma20_status,
                        'dayChangePct': 0.5,
                        'close': 3120.55,
                        'critical': 3200.0,
                        'deviationRate': -0.025,
                        'statusChangedAt': '2026-05-05',
                        'intervalGainPct': -2.3,
                        'trendStrength': '偏弱',
                        'history': [],
                    }
                ],
            },
        },
    }


class StubFetcher:
    def __init__(self, dataset: dict) -> None:
        self._dataset = dataset

    def build_dataset(self, _options: FetchOptions) -> dict:
        return self._dataset


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_markdown(self, content: str) -> None:
        self.messages.append(content)


class FailingNotifier:
    def send_markdown(self, _content: str) -> None:
        raise RuntimeError('wecom down')


class WeComNotifierTests(unittest.TestCase):
    def test_send_markdown_raises_when_webhook_missing(self) -> None:
        notifier = WeComNotifier(webhook_url='')

        with self.assertRaises(ValueError):
            notifier.send_markdown('hello')

    def test_send_markdown_posts_expected_payload(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured['url'] = str(request.url)
            captured['payload'] = json.loads(request.content.decode('utf-8'))
            return httpx.Response(200, json={'errcode': 0, 'errmsg': 'ok'})

        notifier = WeComNotifier(
            webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test',
            client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
        )

        notifier.send_markdown('hello')

        self.assertEqual(
            'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test',
            captured['url'],
        )
        self.assertEqual(
            {'msgtype': 'markdown', 'markdown': {'content': 'hello'}},
            captured['payload'],
        )


class TrendDashboardServiceAlertTests(unittest.TestCase):
    def test_refresh_dataset_builds_initial_snapshot_without_sending_notification(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = build_repository(Path(temp_dir))
            notifier = RecordingNotifier()
            service = TrendDashboardService(
                fetcher=StubFetcher(build_dataset(ma5_status='NO', ma20_status='NO')),
                repository=repository,
                fetch_options=build_fetch_options(),
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
                alert_service=AnyMaNoAlertService(),
                notifier=notifier,
            )

            service.refresh_dataset('scheduler')

            self.assertEqual([], notifier.messages)
            self.assertEqual(RUN_STATUS_SUCCESS, repository.get_last_run().status)
            states = repository.list_alert_states('any_ma_no')
            self.assertIsNone(states['000001'].last_notified_at)

    def test_refresh_dataset_sends_single_summary_for_status_transitions(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = build_repository(Path(temp_dir))
            repository.upsert_alert_state(build_state(active_windows=()))
            notifier = RecordingNotifier()
            service = TrendDashboardService(
                fetcher=StubFetcher(build_dataset(ma5_status='NO', ma20_status='YES')),
                repository=repository,
                fetch_options=build_fetch_options(),
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
                alert_service=AnyMaNoAlertService(),
                notifier=notifier,
            )

            service.refresh_dataset('scheduler')

            self.assertEqual(1, len(notifier.messages))
            self.assertIn('ma5 YES->NO', notifier.messages[0])
            self.assertEqual(RUN_STATUS_SUCCESS, repository.get_last_run().status)
            states = repository.list_alert_states('any_ma_no')
            self.assertEqual('2026-05-06 10:00:00', states['000001'].last_notified_at)

    def test_refresh_dataset_records_failed_run_when_notification_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = build_repository(Path(temp_dir))
            repository.upsert_alert_state(build_state(active_windows=()))
            service = TrendDashboardService(
                fetcher=StubFetcher(build_dataset(ma5_status='NO', ma20_status='YES')),
                repository=repository,
                fetch_options=build_fetch_options(),
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
                alert_service=AnyMaNoAlertService(),
                notifier=FailingNotifier(),
            )

            with self.assertRaises(RuntimeError):
                service.refresh_dataset('scheduler')

            self.assertEqual(RUN_STATUS_FAILED, repository.get_last_run().status)
            states = repository.list_alert_states('any_ma_no')
            self.assertIsNone(states['000001'].last_notified_at)
            self.assertIsNotNone(repository.load_latest_dataset())


def build_repository(root_path: Path) -> SQLiteTrendRepository:
    repository = SQLiteTrendRepository(
        database_path=root_path / 'trends.db',
        now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
    )
    repository.initialize()
    return repository


def build_fetch_options() -> FetchOptions:
    return FetchOptions(history_limit=60, lookback_days=240, ma_windows=(5, 20), retry_count=3)


def build_state(active_windows: tuple[str, ...]) -> object:
    from backend.models import ALERT_RULE_ANY_MA_NO, TrendAlertState

    return TrendAlertState(
        rule_key=ALERT_RULE_ANY_MA_NO,
        code='000001',
        is_active=len(active_windows) > 0,
        active_windows=active_windows,
        last_entered_at='2026-05-06 09:55:00',
        last_notified_at=None,
        updated_at='2026-05-06 09:55:00',
    )


if __name__ == '__main__':
    unittest.main()
