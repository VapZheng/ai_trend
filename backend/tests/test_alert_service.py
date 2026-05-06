from __future__ import annotations

import unittest

from backend.alert_service import evaluate_any_ma_no_alerts
from backend.models import ALERT_RULE_ANY_MA_NO, TrendAlertState


def build_dataset_with_statuses(
    ma5_status: str,
    ma20_status: str,
    ma5_changed_at: str = '2026-05-06',
    ma20_changed_at: str = '2026-05-05',
) -> dict:
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
                        'code': '000001',
                        'name': '上证指数',
                        'status': ma5_status,
                        'close': 3120.55,
                        'critical': 3130.0,
                        'statusChangedAt': ma5_changed_at,
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
                        'code': '000001',
                        'name': '上证指数',
                        'status': ma20_status,
                        'close': 3120.55,
                        'critical': 3200.0,
                        'statusChangedAt': ma20_changed_at,
                    }
                ],
            },
        },
    }


def build_alert_state(
    is_active: bool,
    active_windows: tuple[str, ...],
    last_entered_at: str = '2026-05-06 09:50:00',
) -> TrendAlertState:
    return TrendAlertState(
        rule_key=ALERT_RULE_ANY_MA_NO,
        code='000001',
        is_active=is_active,
        active_windows=active_windows,
        last_entered_at=last_entered_at,
        last_notified_at=None,
        updated_at='2026-05-06 09:50:00',
    )


class EvaluateAnyMaNoAlertTests(unittest.TestCase):
    def test_initial_snapshot_does_not_trigger_notification(self) -> None:
        dataset = build_dataset_with_statuses(
            ma5_status='NO',
            ma20_status='YES',
            ma5_changed_at='2026-05-06',
            ma20_changed_at='2026-05-01',
        )

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={},
            refreshed_at='2026-05-06 10:00:00',
        )

        self.assertEqual([], result.entered_codes)
        self.assertEqual([], result.triggered_items)
        self.assertEqual(('ma5',), result.upserted_states[0].active_windows)

    def test_triggers_yes_to_no_transition(self) -> None:
        state = build_alert_state(is_active=False, active_windows=())
        dataset = build_dataset_with_statuses(ma5_status='NO', ma20_status='YES')

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={'000001': state},
            refreshed_at='2026-05-06 10:10:00',
        )

        self.assertEqual(['000001'], result.entered_codes)
        self.assertEqual(['ma5 YES->NO'], result.triggered_items[0].change_labels)
        self.assertEqual(('ma5',), result.triggered_items[0].changed_windows)
        self.assertEqual('2026-05-06', result.triggered_items[0].status_started_at)
        self.assertEqual([], result.exited_codes)
        self.assertEqual(('ma5',), result.upserted_states[0].active_windows)

    def test_triggers_no_to_yes_transition(self) -> None:
        state = build_alert_state(is_active=True, active_windows=('ma20',))
        dataset = build_dataset_with_statuses(ma5_status='YES', ma20_status='YES')

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={'000001': state},
            refreshed_at='2026-05-06 10:20:00',
        )

        self.assertEqual(['000001'], result.exited_codes)
        self.assertEqual(['ma20 NO->YES'], result.triggered_items[0].change_labels)
        self.assertFalse(result.upserted_states[0].is_active)
        self.assertEqual((), result.upserted_states[0].active_windows)

    def test_keeps_item_without_retriggering_when_statuses_do_not_change(self) -> None:
        state = build_alert_state(is_active=True, active_windows=('ma20',))
        dataset = build_dataset_with_statuses(ma5_status='YES', ma20_status='NO')

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={'000001': state},
            refreshed_at='2026-05-06 10:10:00',
        )

        self.assertEqual([], result.entered_codes)
        self.assertEqual([], result.triggered_items)
        self.assertEqual([], result.exited_codes)
        self.assertEqual(('ma20',), result.upserted_states[0].active_windows)

    def test_merges_multiple_window_changes_into_single_trigger(self) -> None:
        state = build_alert_state(is_active=True, active_windows=('ma5',))
        dataset = build_dataset_with_statuses(ma5_status='YES', ma20_status='NO')

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={'000001': state},
            refreshed_at='2026-05-06 10:20:00',
        )

        self.assertEqual(['000001'], result.entered_codes)
        self.assertEqual(
            ['ma5 NO->YES', 'ma20 YES->NO'],
            result.triggered_items[0].change_labels,
        )
        self.assertEqual(('ma5', 'ma20'), result.triggered_items[0].changed_windows)

    def test_raises_when_required_view_missing(self) -> None:
        dataset = build_dataset_with_statuses(ma5_status='NO', ma20_status='YES')
        del dataset['views']['ma20']

        with self.assertRaises(ValueError):
            evaluate_any_ma_no_alerts(
                dataset=dataset,
                existing_states={},
                refreshed_at='2026-05-06 10:00:00',
            )


if __name__ == '__main__':
    unittest.main()
