from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from time import sleep
from typing import Any, Callable, Sequence

import httpx

from .config import FetchOptions, REQUEST_TIMEOUT_SECONDS

API_URL = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
API_TOKEN = 'fa5fd1943c7b386f172d6893dbfba10b'
RETRY_DELAY_SECONDS = 1.5
STATUS_NO = 'NO'
STATUS_YES = 'YES'
REQUEST_HEADERS = {
    'Accept': 'application/json,text/plain,*/*',
    'Referer': 'https://quote.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
}


@dataclass(frozen=True)
class IndexTarget:
    code: str
    name: str
    secid: str


@dataclass(frozen=True)
class DailyPoint:
    close: float
    date: str


@dataclass(frozen=True)
class EnrichedPoint:
    close: float
    critical: float
    date: str
    status: str


TARGETS = (
    IndexTarget(code='000001', name='上证指数', secid='1.000001'),
    IndexTarget(code='399001', name='深证成指', secid='0.399001'),
    IndexTarget(code='399006', name='创业板指', secid='0.399006'),
    IndexTarget(code='000300', name='沪深300', secid='1.000300'),
    IndexTarget(code='000905', name='中证500', secid='1.000905'),
    IndexTarget(code='000852', name='中证1000', secid='1.000852'),
    IndexTarget(code='932000', name='中证2000', secid='2.932000'),
    IndexTarget(code='000688', name='科创50', secid='1.000688'),
    IndexTarget(code='899050', name='北证50', secid='0.899050'),
    IndexTarget(code='HSI', name='恒生指数', secid='100.HSI'),
    IndexTarget(code='HSCEI', name='国企指数', secid='100.HSCEI'),
)


class TrendDatasetFetcher:
    def __init__(
        self,
        client_factory: Callable[[], httpx.Client],
        targets: Sequence[IndexTarget],
        now_provider: Callable[[], datetime],
    ) -> None:
        self._client_factory = client_factory
        self._targets = tuple(targets)
        self._now_provider = now_provider

    def build_dataset(self, options: FetchOptions) -> dict[str, Any]:
        validate_options(options)
        start_date, end_date = get_date_range(options.lookback_days, self._now_provider)
        windows = tuple(sorted(options.ma_windows))
        target_points = {
            target.code: fetch_index_points(self._client_factory, target, start_date, end_date, options.retry_count)
            for target in self._targets
        }

        latest_data_date = min(points[-1].date for points in target_points.values())
        generated_at = self._now_provider().strftime('%Y-%m-%d %H:%M:%S')
        views = {
            f'ma{window}': {
                'key': f'ma{window}',
                'label': f'{window}日均线',
                'latestDataDate': latest_data_date,
                'maWindow': window,
                'items': rank_items([
                    build_trend_item(target, target_points[target.code], window, options.history_limit)
                    for target in self._targets
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


def build_default_fetcher() -> TrendDatasetFetcher:
    return TrendDatasetFetcher(
        client_factory=build_client,
        targets=TARGETS,
        now_provider=datetime.now,
    )


def build_client() -> httpx.Client:
    return httpx.Client(
        headers=REQUEST_HEADERS,
        http2=False,
        timeout=REQUEST_TIMEOUT_SECONDS,
        trust_env=False,
    )


def validate_options(options: FetchOptions) -> None:
    if options.history_limit < 20:
        raise ValueError('history_limit 必须大于等于 20')
    if options.lookback_days < 60:
        raise ValueError('lookback_days 必须大于等于 60')
    if len(options.ma_windows) == 0:
        raise ValueError('ma_windows 不能为空')
    if len(set(options.ma_windows)) != len(options.ma_windows):
        raise ValueError('ma_windows 不能包含重复窗口')
    if any(window < 2 for window in options.ma_windows):
        raise ValueError('ma_windows 中每个窗口都必须大于等于 2')
    if options.retry_count < 1:
        raise ValueError('retry_count 必须大于等于 1')


def get_date_range(
    lookback_days: int,
    now_provider: Callable[[], datetime],
) -> tuple[str, str]:
    current_time = now_provider()
    end_date = current_time.strftime('%Y%m%d')
    start_date = (current_time - timedelta(days=lookback_days)).strftime('%Y%m%d')
    return start_date, end_date


def fetch_index_points(
    client_factory: Callable[[], httpx.Client],
    target: IndexTarget,
    start_date: str,
    end_date: str,
    retry_count: int,
) -> list[DailyPoint]:
    params = build_request_params(target.secid, start_date, end_date)
    for attempt in range(retry_count):
        try:
            with client_factory() as client:
                response = client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json().get('data')
            if not data or not data.get('klines'):
                raise ValueError(f'{target.code} 未返回有效 K 线数据')
            return parse_klines(data['klines'])
        except Exception as error:
            if attempt == retry_count - 1:
                raise RuntimeError(f'抓取 {target.code} {target.name} 失败：{error}') from error
            sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(f'抓取 {target.code} {target.name} 失败')


def build_request_params(secid: str, start_date: str, end_date: str) -> dict[str, str]:
    return {
        'beg': start_date,
        'end': end_date,
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
        'fqt': '0',
        'klt': '101',
        'secid': secid,
        'ut': API_TOKEN,
    }


def parse_klines(records: list[str]) -> list[DailyPoint]:
    points: list[DailyPoint] = []
    for record in records:
        fields = record.split(',')
        if len(fields) < 3:
            raise ValueError(f'K 线格式异常: {record}')
        points.append(DailyPoint(date=fields[0], close=float(fields[2])))
    return points


def build_trend_item(
    target: IndexTarget,
    points: list[DailyPoint],
    ma_window: int,
    history_limit: int,
) -> dict[str, Any]:
    if len(points) < ma_window + 1:
        raise ValueError(f'{target.code} 历史数据不足，无法计算 {ma_window} 日均线')

    enriched_points = enrich_points(points, ma_window)
    history_points = enriched_points[-history_limit:]
    latest_point = history_points[-1]
    previous_close = points[-2].close
    run_start_index = find_run_start_index(history_points)
    run_start_point = history_points[run_start_index]
    return {
        'rank': 0,
        'code': target.code,
        'name': target.name,
        'status': latest_point.status,
        'dayChangePct': calculate_percent_change(latest_point.close, previous_close),
        'close': round(latest_point.close, 2),
        'critical': round(latest_point.critical, 2),
        'deviationRate': calculate_deviation_rate(latest_point.close, latest_point.critical),
        'statusChangedAt': run_start_point.date,
        'intervalGainPct': calculate_percent_change(latest_point.close, run_start_point.close),
        'trendStrength': get_trend_strength_label(latest_point.close, latest_point.critical),
        'history': [serialize_history_point(point) for point in history_points],
    }


def enrich_points(points: list[DailyPoint], ma_window: int) -> list[EnrichedPoint]:
    rolling_sum = sum(point.close for point in points[:ma_window])
    enriched_points = [create_enriched_point(points[ma_window - 1], rolling_sum / ma_window)]
    for index in range(ma_window, len(points)):
        rolling_sum += points[index].close - points[index - ma_window].close
        enriched_points.append(create_enriched_point(points[index], rolling_sum / ma_window))
    return enriched_points


def create_enriched_point(point: DailyPoint, critical_value: float) -> EnrichedPoint:
    critical = round(critical_value, 2)
    status = STATUS_YES if point.close >= critical else STATUS_NO
    return EnrichedPoint(close=round(point.close, 2), critical=critical, date=point.date, status=status)


def find_run_start_index(points: list[EnrichedPoint]) -> int:
    current_index = len(points) - 1
    current_status = points[current_index].status
    while current_index > 0 and points[current_index - 1].status == current_status:
        current_index -= 1
    return current_index


def serialize_history_point(point: EnrichedPoint) -> dict[str, Any]:
    return {
        'date': point.date,
        'close': point.close,
        'critical': point.critical,
        'status': point.status,
    }


def rank_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked_items = sorted(items, key=lambda item: item['deviationRate'], reverse=True)
    for index, item in enumerate(ranked_items, start=1):
        item['rank'] = index
    return ranked_items


def calculate_percent_change(current_value: float, base_value: float) -> float:
    if base_value == 0:
        raise ValueError('基准值不能为 0')
    return round((current_value - base_value) / base_value * 100, 2)


def calculate_deviation_rate(close_value: float, critical_value: float) -> float:
    if critical_value == 0:
        raise ValueError('临界值不能为 0')
    return round((close_value - critical_value) / critical_value * 100, 2)


def get_trend_strength_label(close_value: float, critical_value: float) -> str:
    deviation_rate = calculate_deviation_rate(close_value, critical_value)
    if deviation_rate >= 5:
        return '很强'
    if deviation_rate >= 2:
        return '偏强'
    if deviation_rate >= 0:
        return '临界上方'
    if deviation_rate >= -2:
        return '临界下方'
    return '偏弱'
