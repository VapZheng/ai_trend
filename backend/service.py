from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Callable

from .config import DEFAULT_AUTO_REFRESH_INTERVAL_SECONDS
from .config import FetchOptions
from .errors import ConflictError, ValidationError
from .models import AutoRefreshState, DashboardPayload, RefreshRun
from .models import RUN_STATUS_FAILED, RUN_STATUS_SUCCESS


class TrendDashboardService:
    def __init__(
        self,
        fetcher,
        repository,
        fetch_options: FetchOptions,
        now_provider: Callable[[], datetime],
    ) -> None:
        self._fetcher = fetcher
        self._repository = repository
        self._fetch_options = fetch_options
        self._now_provider = now_provider
        self._refresh_lock = Lock()

    def build_dashboard(self, next_run_at: str | None) -> DashboardPayload:
        return DashboardPayload(
            auto_refresh=AutoRefreshState(
                interval_seconds=DEFAULT_AUTO_REFRESH_INTERVAL_SECONDS,
                next_run_at=next_run_at,
            ),
            dataset=self._repository.load_latest_dataset(),
            last_run=self._repository.get_last_run(),
            is_refreshing=self.is_refreshing,
        )

    @property
    def is_refreshing(self) -> bool:
        return self._refresh_lock.locked()

    def refresh_dataset(self, source: str) -> None:
        if not self._refresh_lock.acquire(blocking=False):
            raise ConflictError('当前已有采集任务正在执行，请稍后重试')

        started_at = self._format_now()
        try:
            dataset = self._fetcher.build_dataset(self._fetch_options)
        except Exception as error:
            self._save_failed_run(source, started_at, error)
            raise
        else:
            self._repository.save_dataset(dataset)
            self._repository.save_refresh_run(
                RefreshRun(
                    source=source,
                    status=RUN_STATUS_SUCCESS,
                    started_at=started_at,
                    finished_at=self._format_now(),
                ),
            )
        finally:
            self._refresh_lock.release()

    def _format_now(self) -> str:
        return self._now_provider().strftime('%Y-%m-%d %H:%M:%S')

    def _save_failed_run(self, source: str, started_at: str, error: Exception) -> None:
        self._repository.save_refresh_run(
            RefreshRun(
                source=source,
                status=RUN_STATUS_FAILED,
                started_at=started_at,
                finished_at=self._format_now(),
                error_message=str(error),
            ),
        )
