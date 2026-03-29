from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATABASE_PATH = 'data/trends.db'
DEFAULT_HISTORY_LIMIT = 60
DEFAULT_HOST = '0.0.0.0'
DEFAULT_LOOKBACK_DAYS = 240
DEFAULT_MA_WINDOWS = (5, 20)
DEFAULT_MA_WINDOW = 20
DEFAULT_AUTO_REFRESH_INTERVAL_SECONDS = 10
DEFAULT_PORT = 8000
DEFAULT_RETRY_COUNT = 3
REQUEST_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class FetchOptions:
    history_limit: int
    lookback_days: int
    ma_windows: tuple[int, ...]
    retry_count: int


@dataclass(frozen=True)
class AppConfig:
    auto_refresh_interval_seconds: int
    database_path: Path
    fetch_options: FetchOptions
    host: str
    port: int
    static_dir: Path | None


def load_app_config(
    static_dir: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> AppConfig:
    return AppConfig(
        auto_refresh_interval_seconds=DEFAULT_AUTO_REFRESH_INTERVAL_SECONDS,
        database_path=Path(os.getenv('TREND_DB_PATH', DEFAULT_DATABASE_PATH)),
        fetch_options=FetchOptions(
            history_limit=parse_int_env('TREND_HISTORY_LIMIT', DEFAULT_HISTORY_LIMIT),
            lookback_days=parse_int_env('TREND_LOOKBACK_DAYS', DEFAULT_LOOKBACK_DAYS),
            ma_windows=parse_ma_windows_env('TREND_MA_WINDOWS', DEFAULT_MA_WINDOWS),
            retry_count=parse_int_env('TREND_RETRY_COUNT', DEFAULT_RETRY_COUNT),
        ),
        host=host or os.getenv('TREND_HOST', DEFAULT_HOST),
        port=port or parse_int_env('TREND_PORT', DEFAULT_PORT),
        static_dir=resolve_static_dir(static_dir),
    )


def parse_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == '':
        return default
    return int(raw_value)


def parse_ma_windows_env(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == '':
        return default

    values = tuple(int(part.strip()) for part in raw_value.split(',') if part.strip())
    return values or default


def resolve_static_dir(static_dir: str | None) -> Path | None:
    if static_dir == '':
        return None

    if static_dir is None:
        default_dir = Path('dist')
        return default_dir if default_dir.exists() else None

    return Path(static_dir)
