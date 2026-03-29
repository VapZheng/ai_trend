import {
  FILTER_PRESET_NEAR_CRITICAL_MAX_DEVIATION,
  FILTER_PRESET_RECENT_SWITCH_DAYS,
  FILTER_PRESET_TOP_RANK_LIMIT,
} from '../constants';
import type { FilterPresetKey, TrendItem } from '../types';

interface FilterPresetOptions {
  items: TrendItem[];
  presetKey: FilterPresetKey;
  selectedDataDate: string;
}

interface FilterPresetCountOptions {
  items: TrendItem[];
  selectedDataDate: string;
}

export function applyFilterPreset(options: FilterPresetOptions): TrendItem[] {
  const presetKey = options.presetKey;

  if (presetKey === 'all') {
    return options.items;
  }

  return options.items.filter((item) => {
    return matchesFilterPreset(item, presetKey, options.selectedDataDate);
  });
}

export function buildFilterPresetCounts(
  options: FilterPresetCountOptions,
): Record<FilterPresetKey, number> {
  return {
    all: options.items.length,
    'top-strength': countPresetItems(options.items, 'top-strength', options.selectedDataDate),
    'near-critical': countPresetItems(options.items, 'near-critical', options.selectedDataDate),
    'recent-switch': countPresetItems(options.items, 'recent-switch', options.selectedDataDate),
    'breakout-continued': countPresetItems(
      options.items,
      'breakout-continued',
      options.selectedDataDate,
    ),
  };
}

function countPresetItems(
  items: TrendItem[],
  presetKey: Exclude<FilterPresetKey, 'all'>,
  selectedDataDate: string,
): number {
  return items.filter((item) => matchesFilterPreset(item, presetKey, selectedDataDate)).length;
}

function matchesFilterPreset(
  item: TrendItem,
  presetKey: Exclude<FilterPresetKey, 'all'>,
  selectedDataDate: string,
): boolean {
  if (presetKey === 'top-strength') {
    return item.rank <= FILTER_PRESET_TOP_RANK_LIMIT;
  }

  if (presetKey === 'near-critical') {
    return Math.abs(item.deviationRate) <= FILTER_PRESET_NEAR_CRITICAL_MAX_DEVIATION;
  }

  if (presetKey === 'recent-switch') {
    const dayDifference = getRecentSwitchDayDifference(selectedDataDate, item.statusChangedAt);
    return dayDifference >= 0 && dayDifference <= FILTER_PRESET_RECENT_SWITCH_DAYS;
  }

  return item.status === 'YES' && item.intervalGainPct > 0;
}

function getRecentSwitchDayDifference(selectedDataDate: string, statusChangedAt: string): number {
  const selectedTime = parseDateValue(selectedDataDate);
  const changedTime = parseDateValue(statusChangedAt);

  return (selectedTime - changedTime) / MILLISECONDS_PER_DAY;
}

function parseDateValue(dateText: string): number {
  const parsedValue = Date.parse(`${dateText.slice(0, 10)}T00:00:00`);

  if (Number.isNaN(parsedValue)) {
    throw new Error(`无法解析快捷筛选日期：${dateText}`);
  }

  return parsedValue;
}

const MILLISECONDS_PER_DAY = 1000 * 60 * 60 * 24;
