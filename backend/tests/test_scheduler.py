from __future__ import annotations

from datetime import datetime
import unittest

from backend.models import RefreshRun
from backend.scheduler import calculate_next_run_at


class CalculateNextRunAtTests(unittest.TestCase):
    def test_first_run_before_beijing_window_starts(self) -> None:
        now = datetime(2026, 4, 13, 0, 30, 0)

        next_run_at = calculate_next_run_at(
            last_run=None,
            interval_seconds=10,
            now_provider=lambda: now,
            is_refreshing=False,
        )

        self.assertEqual('2026-04-13 01:00:00', next_run_at)

    def test_first_run_inside_beijing_window_uses_current_time(self) -> None:
        now = datetime(2026, 4, 13, 2, 15, 0)

        next_run_at = calculate_next_run_at(
            last_run=None,
            interval_seconds=10,
            now_provider=lambda: now,
            is_refreshing=False,
        )

        self.assertEqual('2026-04-13 02:15:00', next_run_at)

    def test_first_run_after_beijing_window_moves_to_next_day(self) -> None:
        now = datetime(2026, 4, 13, 8, 0, 0)

        next_run_at = calculate_next_run_at(
            last_run=None,
            interval_seconds=10,
            now_provider=lambda: now,
            is_refreshing=False,
        )

        self.assertEqual('2026-04-14 01:00:00', next_run_at)

    def test_interval_after_window_end_moves_to_next_day_start(self) -> None:
        now = datetime(2026, 4, 13, 7, 16, 0)
        last_run = RefreshRun(
            source='scheduler',
            status='success',
            started_at='2026-04-13 07:14:59',
            finished_at='2026-04-13 07:15:10',
        )

        next_run_at = calculate_next_run_at(
            last_run=last_run,
            interval_seconds=10,
            now_provider=lambda: now,
            is_refreshing=False,
        )

        self.assertEqual('2026-04-14 01:00:00', next_run_at)

    def test_overdue_run_inside_window_executes_immediately(self) -> None:
        now = datetime(2026, 4, 13, 2, 0, 0)
        last_run = RefreshRun(
            source='scheduler',
            status='failed',
            started_at='2026-04-13 01:30:00',
            finished_at='2026-04-13 01:30:05',
            error_message='timeout',
        )

        next_run_at = calculate_next_run_at(
            last_run=last_run,
            interval_seconds=10,
            now_provider=lambda: now,
            is_refreshing=False,
        )

        self.assertEqual('2026-04-13 02:00:00', next_run_at)


if __name__ == '__main__':
    unittest.main()
