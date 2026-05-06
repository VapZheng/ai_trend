from __future__ import annotations

from .models import ALERT_RULE_ANY_MA_NO, AlertEvaluationResult, TrendAlertState, TriggeredAlertItem

STATUS_NO = 'NO'
WINDOW_MA5 = 'ma5'
WINDOW_MA20 = 'ma20'


def evaluate_any_ma_no_alerts(
    dataset: dict,
    existing_states: dict[str, TrendAlertState],
    refreshed_at: str,
) -> AlertEvaluationResult:
    views = dataset.get('views', {})
    ma5_view = require_view(views, WINDOW_MA5)
    ma20_view = require_view(views, WINDOW_MA20)
    ma5_items = index_items_by_code(ma5_view['items'])
    ma20_items = index_items_by_code(ma20_view['items'])
    codes = sorted(set(ma5_items) | set(ma20_items) | set(existing_states))
    triggered_items: list[TriggeredAlertItem] = []
    upserted_states: list[TrendAlertState] = []
    entered_codes: list[str] = []
    exited_codes: list[str] = []

    for code in codes:
        ma5_item = ma5_items.get(code)
        ma20_item = ma20_items.get(code)
        active_windows = build_active_windows(ma5_item, ma20_item)
        previous_state = existing_states.get(code)
        was_active = previous_state.is_active if previous_state else False
        is_active = len(active_windows) > 0
        last_entered_at = refreshed_at if is_active and not was_active else previous_state.last_entered_at if previous_state else None
        change_labels = build_change_labels(previous_state.active_windows if previous_state else (), active_windows)
        upserted_states.append(
            TrendAlertState(
                rule_key=ALERT_RULE_ANY_MA_NO,
                code=code,
                is_active=is_active,
                active_windows=active_windows,
                last_entered_at=last_entered_at,
                last_notified_at=previous_state.last_notified_at if previous_state else None,
                updated_at=refreshed_at,
            )
        )
        if previous_state is not None and len(change_labels) > 0:
            entered_codes.append(code)
            triggered_items.append(build_triggered_item(code, ma5_item, ma20_item, active_windows, change_labels))
        if was_active and not is_active:
            exited_codes.append(code)

    return AlertEvaluationResult(
        triggered_items=triggered_items,
        upserted_states=upserted_states,
        entered_codes=entered_codes,
        exited_codes=exited_codes,
    )


def require_view(views: dict, key: str) -> dict:
    view = views.get(key)
    if view is None:
        raise ValueError(f'缺少 {key} 视图，无法判定均线告警')
    return view


def index_items_by_code(items: list[dict]) -> dict[str, dict]:
    return {item['code']: item for item in items}


def build_active_windows(ma5_item: dict | None, ma20_item: dict | None) -> tuple[str, ...]:
    windows: list[str] = []
    if ma5_item is not None and ma5_item['status'] == STATUS_NO:
        windows.append(WINDOW_MA5)
    if ma20_item is not None and ma20_item['status'] == STATUS_NO:
        windows.append(WINDOW_MA20)
    return tuple(windows)


def build_triggered_item(
    code: str,
    ma5_item: dict | None,
    ma20_item: dict | None,
    active_windows: tuple[str, ...],
    change_labels: list[str],
) -> TriggeredAlertItem:
    sample_item = ma5_item or ma20_item
    return TriggeredAlertItem(
        code=code,
        name=sample_item['name'],
        close=sample_item['close'],
        changed_windows=tuple(extract_changed_windows(change_labels)),
        change_labels=change_labels,
        status_started_at=get_status_started_at(ma5_item, ma20_item, change_labels, active_windows),
    )


def get_status_started_at(
    ma5_item: dict | None,
    ma20_item: dict | None,
    change_labels: list[str],
    active_windows: tuple[str, ...],
) -> str:
    dates: list[str] = []
    if has_window_change(change_labels, WINDOW_MA5) and ma5_item is not None:
        dates.append(ma5_item['statusChangedAt'])
    if has_window_change(change_labels, WINDOW_MA20) and ma20_item is not None:
        dates.append(ma20_item['statusChangedAt'])
    if len(dates) == 0:
        if WINDOW_MA5 in active_windows and ma5_item is not None:
            dates.append(ma5_item['statusChangedAt'])
        if WINDOW_MA20 in active_windows and ma20_item is not None:
            dates.append(ma20_item['statusChangedAt'])
    return max(dates)


def build_change_labels(previous_windows: tuple[str, ...], current_windows: tuple[str, ...]) -> list[str]:
    labels: list[str] = []
    for window in (WINDOW_MA5, WINDOW_MA20):
        was_no = window in previous_windows
        is_no = window in current_windows
        if was_no == is_no:
            continue
        labels.append(f'{window} {"NO->YES" if was_no else "YES->NO"}')
    return labels


def extract_changed_windows(change_labels: list[str]) -> list[str]:
    return [label.split(' ', 1)[0] for label in change_labels]


def has_window_change(change_labels: list[str], window: str) -> bool:
    return any(label.startswith(f'{window} ') for label in change_labels)


class AnyMaNoAlertService:
    def evaluate_and_persist(self, dataset: dict, repository, refreshed_at: str) -> AlertEvaluationResult:
        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states=repository.list_alert_states(ALERT_RULE_ANY_MA_NO),
            refreshed_at=refreshed_at,
        )
        for state in result.upserted_states:
            repository.upsert_alert_state(state)
        return result

    def format_message(self, triggered_items: list[TriggeredAlertItem], refreshed_at: str) -> str:
        lines = [
            '## 趋势告警：均线状态发生切换',
            f'> 时间：{refreshed_at}',
            f'> 数量：{len(triggered_items)}',
            '',
        ]
        for item in triggered_items:
            lines.append(
                f'- {item.name}({item.code}) | 最新价 {item.close:.2f} | 切换 {", ".join(item.change_labels)} | 状态开始 {item.status_started_at}'
            )
        return '\n'.join(lines)
