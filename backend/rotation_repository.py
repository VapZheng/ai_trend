from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from .models import RefreshRun, TrendDataset
from .rotation_models import RotationTarget

SCHEMA_STATEMENTS = (
    '''
    CREATE TABLE IF NOT EXISTS sector_rotation_targets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      code TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      quote_id TEXT NOT NULL,
      security_type_name TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS sector_rotation_datasets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      updated_at TEXT NOT NULL,
      latest_data_date TEXT NOT NULL,
      payload TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS sector_rotation_refresh_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      error_message TEXT
    )
    ''',
)


class SQLiteRotationRepository:
    def __init__(
        self,
        database_path: Path,
        default_targets: Sequence[RotationTarget],
        now_provider: Callable[[], datetime],
    ) -> None:
        self._database_path = database_path
        self._default_targets = tuple(default_targets)
        self._now_provider = now_provider

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            should_seed_targets = not self._table_exists(connection, 'sector_rotation_targets')
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            if should_seed_targets:
                self._seed_default_targets(connection)

    def load_targets(self) -> list[RotationTarget]:
        query = '''
            SELECT code, name, quote_id, security_type_name
            FROM sector_rotation_targets
            ORDER BY id ASC
        '''
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
        return [self._build_target(row) for row in rows]

    def load_target(self, code: str) -> RotationTarget | None:
        query = '''
            SELECT code, name, quote_id, security_type_name
            FROM sector_rotation_targets
            WHERE code = ?
        '''
        with self._connect() as connection:
            row = connection.execute(query, (code,)).fetchone()
        return None if row is None else self._build_target(row)

    def add_target(self, target: RotationTarget) -> None:
        timestamp = self._format_now()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO sector_rotation_targets (
                  code, name, quote_id, security_type_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    target.code,
                    target.name,
                    target.quote_id,
                    target.security_type_name,
                    timestamp,
                    timestamp,
                ),
            )

    def remove_target(self, code: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                'DELETE FROM sector_rotation_targets WHERE code = ?',
                (code,),
            )
        return cursor.rowcount > 0

    def load_latest_dataset(self) -> TrendDataset | None:
        query = 'SELECT payload FROM sector_rotation_datasets ORDER BY id DESC LIMIT 1'
        with self._connect() as connection:
            row = connection.execute(query).fetchone()
        return None if row is None else json.loads(row['payload'])

    def save_dataset(self, dataset: TrendDataset) -> None:
        created_at = self._format_now()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO sector_rotation_datasets (updated_at, latest_data_date, payload, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (
                    dataset['updatedAt'],
                    dataset['latestDataDate'],
                    json.dumps(dataset, ensure_ascii=False),
                    created_at,
                ),
            )

    def delete_datasets(self) -> None:
        with self._connect() as connection:
            connection.execute('DELETE FROM sector_rotation_datasets')

    def save_refresh_run(self, refresh_run: RefreshRun) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO sector_rotation_refresh_runs (
                  source, status, started_at, finished_at, error_message
                ) VALUES (?, ?, ?, ?, ?)
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
            FROM sector_rotation_refresh_runs
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

    def _seed_default_targets(self, connection: sqlite3.Connection) -> None:
        timestamp = self._format_now()
        connection.executemany(
            '''
            INSERT INTO sector_rotation_targets (
              code, name, quote_id, security_type_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            [
                (
                    target.code,
                    target.name,
                    target.quote_id,
                    target.security_type_name,
                    timestamp,
                    timestamp,
                )
                for target in self._default_targets
            ],
        )

    def _table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?"
        row = connection.execute(query, (table_name,)).fetchone()
        return row is not None

    def _build_target(self, row: sqlite3.Row) -> RotationTarget:
        return RotationTarget(
            code=row['code'],
            name=row['name'],
            quote_id=row['quote_id'],
            security_type_name=row['security_type_name'],
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _format_now(self) -> str:
        return self._now_provider().strftime('%Y-%m-%d %H:%M:%S')
