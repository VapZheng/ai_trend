import type { TrendHistoryPoint, TrendItem, TrendViewKey } from '../types';
import { getDeviationRate } from './chart';
import { getTrendViewHistory } from './trendViews';

export function buildTrendItemsForDate(
  items: readonly TrendItem[],
  selectedDate: string,
  trendView: TrendViewKey = 'ma20',
): TrendItem[] {
  return items
    .map((item) => buildTrendItemForDate(item, selectedDate, trendView))
    .filter((item): item is TrendItem => item !== null)
    .sort((left, right) => right.deviationRate - left.deviationRate)
    .map((item, index) => ({ ...item, rank: index + 1 }));
}

function buildTrendItemForDate(
  item: TrendItem,
  selectedDate: string,
  trendView: TrendViewKey,
): TrendItem | null {
  const history = getTrendViewHistory(item.history, trendView);
  const pointIndex = history.findIndex((point) => point.date === selectedDate);

  if (pointIndex < 0) {
    return null;
  }

  const visibleHistory = history.slice(0, pointIndex + 1);
  const currentPoint = visibleHistory[pointIndex];
  const previousPoint = visibleHistory[pointIndex - 1] ?? null;
  const statusStartIndex = findStatusStartIndex(visibleHistory, pointIndex);
  const statusStartPoint = visibleHistory[statusStartIndex];
  const deviationRate = getDeviationRate(currentPoint);

  return {
    ...item,
    close: currentPoint.close,
    critical: currentPoint.critical,
    dayChangePct: calculatePercentChange(currentPoint.close, previousPoint?.close ?? currentPoint.close),
    deviationRate,
    history: visibleHistory,
    intervalGainPct: calculatePercentChange(currentPoint.close, statusStartPoint.close),
    rank: item.rank,
    status: currentPoint.status,
    statusChangedAt: statusStartPoint.date,
    trendStrength: getTrendStrengthLabel(deviationRate),
  };
}

function findStatusStartIndex(history: TrendHistoryPoint[], pointIndex: number): number {
  let currentIndex = pointIndex;

  while (currentIndex > 0 && history[currentIndex - 1].status === history[pointIndex].status) {
    currentIndex -= 1;
  }

  return currentIndex;
}

function calculatePercentChange(currentValue: number, baseValue: number): number {
  if (baseValue === 0) {
    return 0;
  }

  return Number((((currentValue - baseValue) / baseValue) * 100).toFixed(2));
}

function getTrendStrengthLabel(deviationRate: number): string {
  if (deviationRate >= 5) {
    return '很强';
  }

  if (deviationRate >= 2) {
    return '偏强';
  }

  if (deviationRate >= 0) {
    return '临界上方';
  }

  if (deviationRate >= -2) {
    return '临界下方';
  }

  return '偏弱';
}
