from __future__ import annotations

from argparse import ArgumentParser, Namespace
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from backend.config import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_MA_WINDOWS,
    DEFAULT_RETRY_COUNT,
    DEFAULT_SCHEDULER_INTERVAL_MINUTES,
    FetchOptions,
)
from backend.fetcher import build_default_fetcher
from backend.models import REFRESH_SOURCE_CLI, RUN_STATUS_SUCCESS, RefreshRun, SchedulerSettings
from backend.repository import SQLiteTrendRepository


def parse_args() -> Namespace:
    parser = ArgumentParser(description='抓取真实趋势数据并写入 sqlite')
    parser.add_argument('--database', default=str(DEFAULT_DATABASE_PATH), help='sqlite 文件路径')
    parser.add_argument('--export-json', default='', help='可选：额外导出一份 JSON 文件')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = SQLiteTrendRepository(
        database_path=Path(args.database),
        default_scheduler=SchedulerSettings(
            enabled=False,
            interval_minutes=DEFAULT_SCHEDULER_INTERVAL_MINUTES,
        ),
        now_provider=datetime.now,
    )
    repository.initialize()
    dataset = build_default_fetcher().build_dataset(default_fetch_options())
    repository.save_dataset(dataset)
    repository.save_refresh_run(
        RefreshRun(
            source=REFRESH_SOURCE_CLI,
            status=RUN_STATUS_SUCCESS,
            started_at=dataset['updatedAt'],
            finished_at=dataset['updatedAt'],
        ),
    )
    if args.export_json:
        export_dataset(args.export_json, dataset)
    default_view_key = dataset['defaultViewKey']
    item_count = len(dataset['views'][default_view_key]['items'])
    print(f"sqlite 数据已更新，最新数据日期 {dataset['latestDataDate']}，共 {item_count} 个指数")


def default_fetch_options() -> FetchOptions:
    return FetchOptions(
        history_limit=DEFAULT_HISTORY_LIMIT,
        lookback_days=DEFAULT_LOOKBACK_DAYS,
        ma_windows=DEFAULT_MA_WINDOWS,
        retry_count=DEFAULT_RETRY_COUNT,
    )


def export_dataset(output_path: str, dataset: dict) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
