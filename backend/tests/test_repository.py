from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from backend.models import ALERT_RULE_ANY_MA_NO, TrendAlertState
from backend.repository import SQLiteTrendRepository


class SQLiteTrendRepositoryAlertStateTests(unittest.TestCase):
    def test_persists_and_reads_alert_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = SQLiteTrendRepository(
                database_path=Path(temp_dir) / 'trends.db',
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
            )
            repository.initialize()

            repository.upsert_alert_state(
                TrendAlertState(
                    rule_key=ALERT_RULE_ANY_MA_NO,
                    code='000001',
                    is_active=True,
                    active_windows=('ma5',),
                    last_entered_at='2026-05-06 10:00:00',
                    last_notified_at=None,
                    updated_at='2026-05-06 10:00:00',
                )
            )

            states = repository.list_alert_states(ALERT_RULE_ANY_MA_NO)

            self.assertTrue(states['000001'].is_active)
            self.assertEqual(('ma5',), states['000001'].active_windows)

    def test_marks_notified_timestamp_for_multiple_codes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = SQLiteTrendRepository(
                database_path=Path(temp_dir) / 'trends.db',
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
            )
            repository.initialize()

            for code in ('000001', '399006'):
                repository.upsert_alert_state(
                    TrendAlertState(
                        rule_key=ALERT_RULE_ANY_MA_NO,
                        code=code,
                        is_active=True,
                        active_windows=('ma5',),
                        last_entered_at='2026-05-06 10:00:00',
                        last_notified_at=None,
                        updated_at='2026-05-06 10:00:00',
                    )
                )

            repository.mark_alerts_notified(
                rule_key=ALERT_RULE_ANY_MA_NO,
                codes=['000001', '399006'],
                notified_at='2026-05-06 10:05:00',
            )

            states = repository.list_alert_states(ALERT_RULE_ANY_MA_NO)

            self.assertEqual('2026-05-06 10:05:00', states['000001'].last_notified_at)
            self.assertEqual('2026-05-06 10:05:00', states['399006'].last_notified_at)


if __name__ == '__main__':
    unittest.main()
