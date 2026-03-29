from __future__ import annotations

from argparse import ArgumentParser, Namespace
from datetime import datetime

from .config import load_app_config
from .fetcher import build_default_fetcher
from .repository import SQLiteTrendRepository
from .rotation_models import DEFAULT_ROTATION_TARGETS
from .rotation_repository import SQLiteRotationRepository
from .rotation_service import SectorRotationService
from .scheduler import RefreshScheduler
from .server import build_server
from .service import TrendDashboardService


def parse_args() -> Namespace:
    parser = ArgumentParser(description='启动鱼盆模型趋势看板服务')
    parser.add_argument('--host', help='监听地址')
    parser.add_argument('--port', type=int, help='监听端口')
    parser.add_argument('--static-dir', help='静态资源目录，默认 dist')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_app_config(static_dir=args.static_dir, host=args.host, port=args.port)
    repository = SQLiteTrendRepository(
        database_path=config.database_path,
        now_provider=datetime.now,
    )
    repository.initialize()
    rotation_repository = SQLiteRotationRepository(
        database_path=config.database_path,
        default_targets=DEFAULT_ROTATION_TARGETS,
        now_provider=datetime.now,
    )
    rotation_repository.initialize()
    service = TrendDashboardService(
        fetcher=build_default_fetcher(),
        repository=repository,
        fetch_options=config.fetch_options,
        now_provider=datetime.now,
    )
    rotation_service = SectorRotationService(
        fetch_options=config.fetch_options,
        now_provider=datetime.now,
        repository=rotation_repository,
    )
    scheduler = RefreshScheduler(
        repository=repository,
        service=service,
        interval_seconds=config.auto_refresh_interval_seconds,
        now_provider=datetime.now,
    )
    server = build_server(
        config.host,
        config.port,
        service,
        scheduler,
        rotation_service,
        config.static_dir,
    )
    scheduler.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        server.server_close()


if __name__ == '__main__':
    main()
