from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .fetcher import DailyPoint, IndexTarget, build_trend_item, rank_items
from .models import RefreshRun, TrendDataset

LEGACY_DATASET_WINDOWS = (5, 20)

SCHEMA_STATEMENTS = (
    '''
    CREATE TABLE IF NOT EXISTS trend_datasets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      updated_at TEXT NOT NULL,
      latest_data_date TEXT NOT NULL,
      payload TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS refresh_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      error_message TEXT
    )
    ''',
)


class SQLiteTrendRepository:
    def __init__(
        self,
        database_path: Path,
        now_provider: Callable[[], datetime],
    ) -> None:
        self._database_path = database_path
        self._now_provider = now_provider

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            self._migrate_legacy_datasets(connection)

    def load_latest_dataset(self) -> TrendDataset | None:
        query = 'SELECT payload FROM trend_datasets ORDER BY id DESC LIMIT 1'
        with self._connect() as connection:
            row = connection.execute(query).fetchone()
        return None if row is None else json.loads(row['payload'])

    def save_dataset(self, dataset: TrendDataset) -> None:
        created_at = self._now_provider().strftime('%Y-%m-%d %H:%M:%S')
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO trend_datasets (updated_at, latest_data_date, payload, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (
                    dataset['updatedAt'],
                    dataset['latestDataDate'],
                    json.dumps(dataset, ensure_ascii=False),
                    created_at,
                ),
            )

    def save_refresh_run(self, refresh_run: RefreshRun) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO refresh_runs (source, status, started_at, finished_at, error_message)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    refresh_run.source,
                    refresh_run.status,
                    refresh_run.started_at,
                    refresh_run.finished_at,
                    refresh_run.error_message,
                ),
            )

    def get_last_run(self) -> RefreshRun | None:
        query = '''
            SELECT source, status, started_at, finished_at, error_message
            FROM refresh_runs
            ORDER BY id DESC
            LIMIT 1
        '''
        with self._connect() as connection:
            row = connection.execute(query).fetchone()
        if row is None:
            return None
        return RefreshRun(
            source=row['source'],
            status=row['status'],
            started_at=row['started_at'],
            finished_at=row['finished_at'],
            error_message=row['error_message'],
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _migrate_legacy_datasets(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute('SELECT id, payload FROM trend_datasets').fetchall()
        for row in rows:
            payload = json.loads(row['payload'])
            if 'views' in payload:
                continue

            migrated_dataset = migrate_legacy_dataset(payload)
            connection.execute(
                '''
                UPDATE trend_datasets
                SET latest_data_date = ?, payload = ?
                WHERE id = ?
                ''',
                (
                    migrated_dataset['latestDataDate'],
                    json.dumps(migrated_dataset, ensure_ascii=False),
                    row['id'],
                ),
            )


def migrate_legacy_dataset(payload: dict[str, Any]) -> TrendDataset:
    legacy_items = payload.get('items')
    if not isinstance(legacy_items, list):
        raise ValueError('旧版数据集缺少 items 字段，无法迁移到多均线结构')

    latest_data_date = payload['latestDataDate']
    views = {
        'ma5': build_legacy_view(legacy_items, 5, latest_data_date),
        'ma20': build_legacy_view(legacy_items, 20, latest_data_date),
    }

    return {
        'updatedAt': payload['updatedAt'],
        'latestDataDate': latest_data_date,
        'defaultViewKey': 'ma20',
        'viewOrder': [f'ma{window}' for window in LEGACY_DATASET_WINDOWS],
        'views': views,
    }


def build_legacy_view(legacy_items: list[dict[str, Any]], window: int, latest_data_date: str) -> dict[str, Any]:
    items = rank_items([clone_legacy_item(item) for item in legacy_items]) if window == 20 else build_legacy_ma_items(legacy_items, window)
    return {
        'key': f'ma{window}',
        'label': f'{window}日均线',
        'latestDataDate': latest_data_date,
        'maWindow': window,
        'items': items,
    }


def build_legacy_ma_items(legacy_items: list[dict[str, Any]], window: int) -> list[dict[str, Any]]:
    items = [
        build_trend_item(
            target=IndexTarget(code=item['code'], name=item['name'], secid=item['code']),
            points=[DailyPoint(date=point['date'], close=point['close']) for point in item['history']],
            ma_window=window,
            history_limit=len(item['history']),
        )
        for item in legacy_items
    ]
    return rank_items(items)


def clone_legacy_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        'history': [dict(point) for point in item['history']],
    }
