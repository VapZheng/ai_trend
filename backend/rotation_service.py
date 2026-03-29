from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Callable

from .config import FetchOptions
from .errors import ConflictError, ValidationError
from .models import RUN_STATUS_FAILED, RUN_STATUS_SUCCESS, RefreshRun
from .rotation_fetcher import build_rotation_dataset, normalize_code, resolve_rotation_target
from .rotation_models import SectorRotationPayload

REFRESH_SOURCE_MANUAL = 'manual'


class SectorRotationService:
    def __init__(
        self,
        fetch_options: FetchOptions,
        now_provider: Callable[[], datetime],
        repository,
    ) -> None:
        self._fetch_options = fetch_options
        self._now_provider = now_provider
        self._repository = repository
        self._refresh_lock = Lock()

    def build_payload(self) -> SectorRotationPayload:
        return SectorRotationPayload(
            dataset=self._repository.load_latest_dataset(),
            is_refreshing=self.is_refreshing,
            last_run=self._repository.get_last_run(),
            targets=tuple(self._repository.load_targets()),
        )

    @property
    def is_refreshing(self) -> bool:
        return self._refresh_lock.locked()

    def add_target(self, code: str) -> None:
        normalized_code = normalize_code(code)
        if self._repository.load_target(normalized_code):
            raise ValidationError(f'{normalized_code} 已在当前配置中')
        self._repository.add_target(resolve_rotation_target(normalized_code))

    def remove_target(self, code: str) -> None:
        normalized_code = normalize_code(code)
        if not self._repository.remove_target(normalized_code):
            raise ValidationError(f'{normalized_code} 不在当前配置中')
        if len(self._repository.load_targets()) == 0:
            self._repository.delete_datasets()

    def refresh_dataset(self, source: str = REFRESH_SOURCE_MANUAL) -> None:
        if not self._refresh_lock.acquire(blocking=False):
            raise ConflictError('当前已有板块轮动采集任务正在执行，请稍后重试')

        started_at = self._format_now()
        try:
            dataset = build_rotation_dataset(self._load_targets(), self._fetch_options, self._now_provider)
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

    def _load_targets(self):
        targets = self._repository.load_targets()
        if len(targets) == 0:
            raise ValidationError('请先在“代码配置”里添加至少一个板块或指数代码')
        return targets

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
