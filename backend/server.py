from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .errors import ConflictError, ValidationError

DASHBOARD_SYNC_REMOVED_ERROR = '手动同步接口已移除，主看板默认每 10 秒自动取数。'
DASHBOARD_SCHEDULER_REMOVED_ERROR = '调度配置接口已移除，主看板默认每 10 秒自动取数。'


class DashboardRequestHandler(BaseHTTPRequestHandler):
    rotation_service = None
    scheduler = None
    service = None
    static_dir: Path | None = None

    def do_GET(self) -> None:
        route, _ = parse_request(self.path)
        if route == '/api/dashboard':
            self._write_json(HTTPStatus.OK, self.service.build_dashboard(self.scheduler.get_next_run_at()).to_dict())
            return
        if route == '/api/sector-rotation':
            self._write_json(HTTPStatus.OK, self.rotation_service.build_payload().to_dict())
            return
        if route == '/api/health':
            self._write_json(HTTPStatus.OK, {'ok': True})
            return
        self._serve_static(route)

    def do_POST(self) -> None:
        route, _ = parse_request(self.path)
        if route in {'/api/dashboard/refresh', '/api/trends/refresh'}:
            self._write_json(HTTPStatus.GONE, {'error': DASHBOARD_SYNC_REMOVED_ERROR})
            return
        if route == '/api/sector-rotation/refresh':
            self._write_rotation_result(self.rotation_service.refresh_dataset)
            return
        if route == '/api/sector-rotation/targets':
            self._write_rotation_target_add_result()
            return
        self._write_json(HTTPStatus.NOT_FOUND, {'error': '接口不存在'})

    def do_PUT(self) -> None:
        self._write_json(HTTPStatus.GONE, {'error': DASHBOARD_SCHEDULER_REMOVED_ERROR})

    def do_DELETE(self) -> None:
        route, query = parse_request(self.path)
        if route != '/api/sector-rotation/targets':
            self._write_json(HTTPStatus.NOT_FOUND, {'error': '接口不存在'})
            return

        code = parse_code_query(query)
        self._write_rotation_result(lambda: self.rotation_service.remove_target(code))

    def log_message(self, format: str, *args) -> None:
        return None

    def _write_rotation_result(self, action) -> None:
        try:
            action()
            self._write_json(HTTPStatus.OK, self.rotation_service.build_payload().to_dict())
        except ConflictError as error:
            self._write_json(HTTPStatus.CONFLICT, {'error': str(error)})
        except ValidationError as error:
            self._write_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
        except Exception as error:
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {'error': str(error)})

    def _write_rotation_target_add_result(self) -> None:
        try:
            payload = self._read_json_body()
            code = parse_code_payload(payload)
        except ValidationError as error:
            self._write_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
            return

        self._write_rotation_result(lambda: self.rotation_service.add_target(code))

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get('Content-Length', '0'))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            return json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError as error:
            raise ValidationError('请求体必须是合法 JSON') from error

    def _serve_static(self, route: str) -> None:
        if self.static_dir is None:
            self._write_json(HTTPStatus.NOT_FOUND, {'error': '静态资源目录不存在'})
            return
        file_path = resolve_static_path(self.static_dir, route)
        if file_path is None or not file_path.exists():
            self._write_json(HTTPStatus.NOT_FOUND, {'error': '资源不存在'})
            return

        content_type, _ = mimetypes.guess_type(file_path.name)
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', content_type or 'application/octet-stream')
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def _write_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_server(host: str, port: int, service, scheduler, rotation_service, static_dir: Path | None) -> ThreadingHTTPServer:
    handler = type('ConfiguredDashboardRequestHandler', (DashboardRequestHandler,), {})
    handler.rotation_service = rotation_service
    handler.service = service
    handler.scheduler = scheduler
    handler.static_dir = static_dir.resolve() if static_dir else None
    return ThreadingHTTPServer((host, port), handler)


def resolve_static_path(static_dir: Path, route: str) -> Path | None:
    requested_path = route.lstrip('/') or 'index.html'
    resolved_path = (static_dir / requested_path).resolve()
    static_root = static_dir.resolve()
    if static_root not in resolved_path.parents and resolved_path != static_root:
        return None
    if resolved_path.exists() and resolved_path.is_file():
        return resolved_path
    if Path(requested_path).suffix:
        return None
    fallback_path = static_root / 'index.html'
    return fallback_path if fallback_path.exists() else None


def parse_request(path: str) -> tuple[str, dict[str, list[str]]]:
    parsed_url = urlparse(path)
    return parsed_url.path, parse_qs(parsed_url.query)


def parse_code_payload(payload: dict) -> str:
    code = payload.get('code')
    if not isinstance(code, str):
        raise ValidationError('code 必须是字符串')
    return code


def parse_code_query(query: dict[str, list[str]]) -> str:
    code_values = query.get('code', [])
    if len(code_values) != 1:
        raise ValidationError('code 查询参数不能为空')
    return code_values[0]
