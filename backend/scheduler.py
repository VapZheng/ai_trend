from __future__ import annotations

from datetime import datetime, timedelta
from threading import Event, Thread
from typing import Callable

from .errors import ConflictError
from .models import REFRESH_SOURCE_SCHEDULER, RefreshRun

SCHEDULER_POLL_SECONDS = 1


class RefreshScheduler:
    def __init__(
        self,
        repository,
        service,
        interval_seconds: int,
        now_provider: Callable[[], datetime],
    ) -> None:
        self._repository = repository
        self._service = service
        self._interval_seconds = interval_seconds
        self._now_provider = now_provider
        self._next_run_at: str | None = None
        self._stop_event = Event()
        self._thread = Thread(target=self._run_loop, daemon=True, name='trend-refresh-scheduler')

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=3)

    def get_next_run_at(self) -> str | None:
        self._next_run_at = calculate_next_run_at(
            self._repository.get_last_run(),
            self._interval_seconds,
            self._now_provider,
            self._service.is_refreshing,
        )
        return self._next_run_at

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._run_once()
            self._stop_event.wait(SCHEDULER_POLL_SECONDS)

    def _run_once(self) -> None:
        self._next_run_at = calculate_next_run_at(
            self._repository.get_last_run(),
            self._interval_seconds,
            self._now_provider,
            self._service.is_refreshing,
        )
        if self._next_run_at is None:
            return

        if self._next_run_at > self._now_provider().strftime('%Y-%m-%d %H:%M:%S'):
            return

        try:
            self._service.refresh_dataset(REFRESH_SOURCE_SCHEDULER)
        except ConflictError:
            return
        except Exception:
            return
        self._next_run_at = calculate_next_run_at(
            self._repository.get_last_run(),
            self._interval_seconds,
            self._now_provider,
            self._service.is_refreshing,
        )


def calculate_next_run_at(
    last_run: RefreshRun | None,
    interval_seconds: int,
    now_provider: Callable[[], datetime],
    is_refreshing: bool,
) -> str | None:
    if is_refreshing:
        return None
    if last_run is None:
        return now_provider().strftime('%Y-%m-%d %H:%M:%S')
    base_time = last_run.finished_at or last_run.started_at
    next_run_time = datetime.strptime(base_time, '%Y-%m-%d %H:%M:%S')
    next_run_time += timedelta(seconds=interval_seconds)
    return next_run_time.strftime('%Y-%m-%d %H:%M:%S')
