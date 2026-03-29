import type { TrendHistoryPoint, TrendItem, TrendViewKey, TrendViewMeta, TrendViewOption } from '../types';

const TREND_VIEW_META: Record<TrendViewKey, TrendViewMeta> = {
  ma5: {
    criticalLabel: '5日临界值',
    description: '以 5 日均线作为临界值，更敏感地观察短线切换。',
    label: '5日均线',
    shortLabel: '5日',
    title: '5日均线视图',
    value: 'ma5',
    windowSize: 5,
  },
  ma20: {
    criticalLabel: '20日临界值',
    description: '以 20 日均线作为临界值，适合看中短周期趋势强弱。',
    label: '20日均线',
    shortLabel: '20日',
    title: '20日均线视图',
    value: 'ma20',
    windowSize: 20,
  },
};

export const DEFAULT_TREND_VIEW_KEY: TrendViewKey = 'ma20';

export const TREND_VIEW_OPTIONS: TrendViewOption[] = [
  TREND_VIEW_META.ma5,
  TREND_VIEW_META.ma20,
].map(({ criticalLabel, label, shortLabel, value }) => ({
  criticalLabel,
  label,
  shortLabel,
  value,
}));

export function getTrendViewMeta(viewKey: TrendViewKey): TrendViewMeta {
  return TREND_VIEW_META[viewKey];
}

export function getTrendViewWindow(viewKey: TrendViewKey): number {
  return getTrendViewMeta(viewKey).windowSize;
}

export function getTrendViewAvailableDates(items: readonly TrendItem[], viewKey: TrendViewKey): string[] {
  void viewKey;
  return [...(items[0]?.history ?? [])].map((point) => point.date);
}

export function getTrendViewHistory(
  history: readonly TrendHistoryPoint[],
  viewKey: TrendViewKey,
): TrendHistoryPoint[] {
  void viewKey;
  return [...history];
}

export function buildTrendViewNotice(
  viewKey: TrendViewKey,
  items: readonly TrendItem[],
  availableDates: readonly string[],
): string {
  const viewMeta = getTrendViewMeta(viewKey);

  if (items.length === 0) {
    return `当前页面会在有数据后按 ${viewMeta.criticalLabel} 联动总览、筛选、排序、日期切换与图表。`;
  }

  if (availableDates.length === 0) {
    return `当前数据不足以展示 ${viewMeta.label} 视图，请先执行同步。`;
  }

  return `当前页面所有总览、筛选、排序、日期切换与图表对比，均按 ${viewMeta.criticalLabel} 联动。`;
}
