import type { SortKey, StatusFilter, TrendItem } from '../types';

interface FilterSortOptions {
  items: TrendItem[];
  searchTerm: string;
  statusFilter: StatusFilter;
  sortKey: SortKey;
}

export function filterAndSortTrends(options: FilterSortOptions): TrendItem[] {
  return sortTrends(filterTrends(options), options.sortKey);
}

export function filterTrends(options: Omit<FilterSortOptions, 'sortKey'>): TrendItem[] {
  const keyword = options.searchTerm.trim().toLowerCase();

  return options.items.filter((item) => {
    const matchesSearch =
      keyword.length === 0 ||
      item.code.toLowerCase().includes(keyword) ||
      item.name.toLowerCase().includes(keyword);

    const matchesStatus =
      options.statusFilter === 'ALL' || item.status === options.statusFilter;

    return matchesSearch && matchesStatus;
  });
}

export function sortTrends(items: TrendItem[], sortKey: SortKey): TrendItem[] {
  return [...items].sort((left, right) => compareTrendItems(left, right, sortKey));
}

export function getStatusTagType(status: TrendItem['status']): string {
  return status === 'YES' ? 'success' : 'danger';
}

export function getStrengthTagType(deviationRate: number): string {
  if (deviationRate >= 2) {
    return 'success';
  }

  if (deviationRate >= 0) {
    return 'warning';
  }

  if (deviationRate >= -2) {
    return 'info';
  }

  return 'danger';
}

function compareTrendItems(left: TrendItem, right: TrendItem, sortKey: SortKey): number {
  if (sortKey === 'deviation-desc') {
    return right.deviationRate - left.deviationRate;
  }

  if (sortKey === 'change-desc') {
    return right.dayChangePct - left.dayChangePct;
  }

  if (sortKey === 'status-time-desc') {
    return right.statusChangedAt.localeCompare(left.statusChangedAt);
  }

  return left.rank - right.rank;
}
