from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict


class TrendHistoryPoint(TypedDict):
    date: str
    close: float
    critical: float
    status: str


class TrendItemPayload(TypedDict):
    rank: int
    code: str
    name: str
    status: str
    dayChangePct: float
    close: float
    critical: float
    deviationRate: float
    statusChangedAt: str
    intervalGainPct: float
    trendStrength: str
    history: list[TrendHistoryPoint]


class TrendDatasetView(TypedDict):
    key: str
    label: str
    latestDataDate: str
    maWindow: int
    items: list[TrendItemPayload]


class TrendDataset(TypedDict):
    updatedAt: str
    latestDataDate: str
    defaultViewKey: str
    viewOrder: list[str]
    views: dict[str, TrendDatasetView]

REFRESH_SOURCE_CLI = 'cli'
REFRESH_SOURCE_SCHEDULER = 'scheduler'
RUN_STATUS_FAILED = 'failed'
RUN_STATUS_SUCCESS = 'success'


@dataclass(frozen=True)
class AutoRefreshState:
    interval_seconds: int
    next_run_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'intervalSeconds': self.interval_seconds,
            'nextRunAt': self.next_run_at,
        }


@dataclass(frozen=True)
class RefreshRun:
    source: str
    status: str
    started_at: str
    finished_at: str | None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'source': self.source,
            'status': self.status,
            'startedAt': self.started_at,
            'finishedAt': self.finished_at,
            'errorMessage': self.error_message,
        }


@dataclass(frozen=True)
class DashboardPayload:
    auto_refresh: AutoRefreshState
    dataset: TrendDataset | None
    last_run: RefreshRun | None
    is_refreshing: bool

    def to_dict(self) -> dict[str, Any]:
        auto_refresh_payload = self.auto_refresh.to_dict()
        auto_refresh_payload['isRunning'] = self.is_refreshing
        auto_refresh_payload['lastRunAt'] = self.last_run.finished_at if self.last_run else None
        return {
            'autoRefresh': auto_refresh_payload,
            'dataset': self.dataset,
            'lastRun': self.last_run.to_dict() if self.last_run else None,
            'isRefreshing': self.is_refreshing,
        }
