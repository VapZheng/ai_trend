from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from functools import lru_cache
from io import StringIO
from time import sleep

import akshare as ak

from .fetcher import DailyPoint, IndexTarget, RETRY_DELAY_SECONDS

BOARD_NAME_ALIASES = {
    '机器人': ('concept', '机器人概念'),
    '机器人概念': ('concept', '机器人概念'),
    '证券Ⅱ': ('industry', '证券'),
    '银行Ⅱ': ('industry', '银行'),
}
HK_INDEX_PREFIX = '100.'
INDEX_SYMBOL_ALIASES = {
    '899050': 'bj899050',
}
SUPPORTED_A_SHARE_PREFIXES = {
    '0': 'sz',
    '1': 'sh',
}


def fetch_rotation_points(
    target: IndexTarget,
    start_date: str,
    end_date: str,
    retry_count: int,
) -> list[DailyPoint]:
    for attempt in range(retry_count):
        try:
            return fetch_rotation_points_once(target, start_date, end_date)
        except Exception as error:
            if attempt == retry_count - 1:
                raise RuntimeError(f'抓取 {target.code} {target.name} 失败：{error}') from error
            sleep(RETRY_DELAY_SECONDS)
    raise RuntimeError(f'抓取 {target.code} {target.name} 失败')


def fetch_rotation_points_once(
    target: IndexTarget,
    start_date: str,
    end_date: str,
) -> list[DailyPoint]:
    if is_hk_index(target):
        return fetch_hk_index_points(target, start_date, end_date)
    if is_board_target(target):
        return fetch_board_points(target, start_date, end_date)
    return fetch_a_share_index_points(target, start_date, end_date)


def is_hk_index(target: IndexTarget) -> bool:
    return target.secid.startswith(HK_INDEX_PREFIX)


def is_board_target(target: IndexTarget) -> bool:
    return target.code.startswith('BK')


def fetch_hk_index_points(
    target: IndexTarget,
    start_date: str,
    end_date: str,
) -> list[DailyPoint]:
    frame = call_akshare(lambda: ak.stock_hk_index_daily_sina(symbol=target.code))
    return build_points_from_frame(frame, 'date', 'close', start_date, end_date)


def fetch_a_share_index_points(
    target: IndexTarget,
    start_date: str,
    end_date: str,
) -> list[DailyPoint]:
    symbol = resolve_a_share_index_symbol(target)
    frame = call_akshare(lambda: ak.stock_zh_index_daily_tx(symbol=symbol))
    return build_points_from_frame(frame, 'date', 'close', start_date, end_date)


def resolve_a_share_index_symbol(target: IndexTarget) -> str:
    aliased_symbol = INDEX_SYMBOL_ALIASES.get(target.code)
    if aliased_symbol:
        return aliased_symbol

    market, _, _ = target.secid.partition('.')
    prefix = SUPPORTED_A_SHARE_PREFIXES.get(market)
    if prefix is None:
        raise ValueError(f'{target.code} 的市场标识 {market} 暂不支持当前轮动取数链路')
    return f'{prefix}{target.code}'


def fetch_board_points(
    target: IndexTarget,
    start_date: str,
    end_date: str,
) -> list[DailyPoint]:
    board_type, symbol = resolve_board_symbol(target.name)
    if board_type == 'industry':
        frame = call_akshare(
            lambda: ak.stock_board_industry_index_ths(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        )
    else:
        frame = call_akshare(
            lambda: ak.stock_board_concept_index_ths(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        )
    return build_points_from_frame(frame, '日期', '收盘价', start_date, end_date)


def resolve_board_symbol(name: str) -> tuple[str, str]:
    aliased_match = BOARD_NAME_ALIASES.get(name)
    if aliased_match is not None:
        return aliased_match

    industry_names, concept_names = load_board_name_sets()
    matches = []
    for board_type, candidate in build_board_candidates(name):
        if board_type == 'industry' and candidate in industry_names:
            matches.append((board_type, candidate))
        if board_type == 'concept' and candidate in concept_names:
            matches.append((board_type, candidate))

    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) == 0:
        raise ValueError(f'{name} 未找到可用的同花顺板块映射')
    if len(unique_matches) > 1:
        raise ValueError(f'{name} 命中多个同花顺板块映射：{unique_matches}')
    return unique_matches[0]


def build_board_candidates(name: str) -> list[tuple[str, str]]:
    trimmed_name = name.strip()
    simplified_name = trimmed_name.removesuffix('Ⅱ')
    candidates = [
        ('industry', trimmed_name),
        ('concept', trimmed_name),
        ('industry', simplified_name),
        ('concept', simplified_name),
        ('concept', f'{trimmed_name}概念'),
        ('concept', f'{simplified_name}概念'),
    ]
    return list(dict.fromkeys(candidates))


@lru_cache(maxsize=1)
def load_board_name_sets() -> tuple[frozenset[str], frozenset[str]]:
    industry_frame = call_akshare(ak.stock_board_industry_name_ths)
    concept_frame = call_akshare(ak.stock_board_concept_name_ths)
    return (
        frozenset(industry_frame['name'].astype(str)),
        frozenset(concept_frame['name'].astype(str)),
    )


def build_points_from_frame(
    frame,
    date_column: str,
    close_column: str,
    start_date: str,
    end_date: str,
) -> list[DailyPoint]:
    points = [
        DailyPoint(close=round(float(row[close_column]), 2), date=format_point_date(row[date_column]))
        for _, row in frame.iterrows()
        if start_date <= normalize_date_key(row[date_column]) <= end_date
    ]
    if len(points) == 0:
        raise ValueError('未返回有效历史数据')
    return points


def normalize_date_key(value) -> str:
    return str(value).replace('-', '')[:8]


def format_point_date(value) -> str:
    date_key = normalize_date_key(value)
    return f'{date_key[0:4]}-{date_key[4:6]}-{date_key[6:8]}'


def call_akshare(operation):
    buffer = StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        return operation()
