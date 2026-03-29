from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Sequence

from .config import FetchOptions
from .errors import ValidationError
from .fetcher import IndexTarget, build_client, build_trend_item, get_date_range, rank_items, validate_options
from .rotation_history import fetch_rotation_points
from .rotation_models import RotationTarget

SEARCH_API_TOKEN = 'D43BF722C8E33BDC906FB84D85E326E8'
SEARCH_API_URL = 'https://searchapi.eastmoney.com/api/suggest/get'
SUPPORTED_SECURITY_TYPES = {'指数', '板块'}


def build_rotation_dataset(
    targets: Sequence[RotationTarget],
    fetch_options: FetchOptions,
    now_provider: Callable[[], datetime],
) -> dict[str, Any]:
    validate_options(fetch_options)
    index_targets = build_index_targets(targets)
    start_date, end_date = get_date_range(fetch_options.lookback_days, now_provider)
    windows = tuple(sorted(fetch_options.ma_windows))
    target_points = {
        target.code: fetch_rotation_points(target, start_date, end_date, fetch_options.retry_count)
        for target in index_targets
    }
    latest_data_date = min(points[-1].date for points in target_points.values())
    generated_at = now_provider().strftime('%Y-%m-%d %H:%M:%S')
    views = {
        f'ma{window}': {
            'key': f'ma{window}',
            'label': f'{window}日均线',
            'latestDataDate': latest_data_date,
            'maWindow': window,
            'items': rank_items([
                build_trend_item(target, target_points[target.code], window, fetch_options.history_limit)
                for target in index_targets
            ]),
        }
        for window in windows
    }
    return {
        'updatedAt': generated_at,
        'latestDataDate': latest_data_date,
        'defaultViewKey': f'ma{windows[-1]}',
        'viewOrder': [f'ma{window}' for window in windows],
        'views': views,
    }


def build_index_targets(targets: Sequence[RotationTarget]) -> list[IndexTarget]:
    return [
        IndexTarget(code=target.code, name=target.name, secid=target.quote_id)
        for target in targets
    ]


def resolve_rotation_target(code: str) -> RotationTarget:
    normalized_code = normalize_code(code)
    payload = request_search_payload(normalized_code)
    matched_row = select_search_match(payload, normalized_code)
    return RotationTarget(
        code=matched_row['Code'],
        name=matched_row['Name'],
        quote_id=matched_row['QuoteID'],
        security_type_name=matched_row['SecurityTypeName'],
    )


def normalize_code(code: str) -> str:
    normalized_code = code.strip().upper()
    if len(normalized_code) == 0:
        raise ValidationError('代码不能为空')
    return normalized_code


def request_search_payload(code: str) -> list[dict[str, Any]]:
    params = {
        'count': '10',
        'input': code,
        'token': SEARCH_API_TOKEN,
        'type': '14',
    }
    with build_client() as client:
        response = client.get(SEARCH_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    return payload.get('QuotationCodeTable', {}).get('Data', [])


def select_search_match(rows: list[dict[str, Any]], code: str) -> dict[str, Any]:
    exact_matches = [
        row
        for row in rows
        if str(row.get('Code', '')).upper() == code and row.get('SecurityTypeName') in SUPPORTED_SECURITY_TYPES
    ]
    if len(exact_matches) == 0:
        raise ValidationError(f'未找到可用的板块/指数代码：{code}')

    matched_row = exact_matches[0]
    if not matched_row.get('QuoteID') or not matched_row.get('Name'):
        raise ValidationError(f'{code} 缺少必要的行情标识，无法保存配置')
    return matched_row
