import { computed, ref, watch } from 'vue';
import type { FilterPresetKey, SortKey, StatusFilter, TrendDataset, TrendItem, TrendViewKey } from '../types';
import { buildMarketOverview } from '../utils/dashboardOverview';
import { normalizeCompareCodes } from '../utils/dashboardState';
import { applyFilterPreset, buildFilterPresetCounts } from '../utils/filterPresets';
import { buildTrendItemsForDate } from '../utils/trendSlice';
import {
  DEFAULT_TREND_VIEW_KEY,
  TREND_VIEW_OPTIONS,
  buildTrendViewNotice,
  getTrendViewAvailableDates,
  getTrendViewMeta,
} from '../utils/trendViews';
import { filterTrends, sortTrends } from '../utils/trends';
import { useTrendData } from './useTrendData';

type TrendDataState = ReturnType<typeof useTrendData>;
type DashboardState = ReturnType<typeof createDashboardState>;

export function useDashboardViewModel() {
  const trendData = useTrendData();
  const state = createDashboardState(trendData);

  registerDashboardWatchers(state);

  return {
    activeDatasetView: state.activeDatasetView,
    activeTrendView: state.activeTrendView,
    activeTrendViewMeta: state.activeTrendViewMeta,
    autoRefresh: trendData.autoRefresh,
    availableDates: state.availableDates,
    compareCodes: state.compareCodes,
    dataset: trendData.dataset,
    errorMessage: trendData.errorMessage,
    handleCompareCodesChange: (nextCodes: string[]) => updateCompareCodes(state, nextCodes),
    handleSelect: (item: TrendItem) => selectTrendItem(state, item),
    handleToggleCompare: (item: TrendItem) => toggleCompareItem(state, item),
    handleTrendViewChange: (nextView: TrendViewKey) => changeTrendView(state, nextView),
    isLoading: trendData.isLoading,
    items: state.items,
    lastRun: trendData.lastRun,
    marketOverview: state.marketOverview,
    presetCounts: state.presetCounts,
    recentCompareCodes: state.recentCompareCodes,
    resetFilters: () => resetDashboardFilters(state),
    searchTerm: state.searchTerm,
    selectedDataDate: state.selectedDataDate,
    selectedItem: state.selectedItem,
    selectedPreset: state.selectedPreset,
    serverRefreshing: trendData.serverRefreshing,
    sortKey: state.sortKey,
    statusFilter: state.statusFilter,
    trendViewNotice: state.trendViewNotice,
    trendViewOptions: TREND_VIEW_OPTIONS,
    visibleItems: state.visibleItems,
  };
}

function createDashboardState(trendData: TrendDataState) {
  const activeTrendView = ref<TrendViewKey>(DEFAULT_TREND_VIEW_KEY);
  const searchTerm = ref('');
  const sortKey = ref<SortKey>('rank-asc');
  const statusFilter = ref<StatusFilter>('ALL');
  const selectedDataDate = ref('');
  const selectedPreset = ref<FilterPresetKey>('all');
  const selectedCode = ref('');
  const compareCodes = ref<string[]>([]);
  const recentCompareCodes = ref<string[]>([]);
  const dataset = trendData.dataset;
  const activeDatasetView = computed(() => dataset.value?.views[activeTrendView.value] ?? null);
  const sourceItems = computed(() => activeDatasetView.value?.items ?? []);
  const activeTrendViewMeta = computed(() => getTrendViewMeta(activeTrendView.value));
  const availableDates = computed(() => getTrendViewAvailableDates(sourceItems.value, activeTrendView.value));
  const items = computed(() => buildVisibleDateItems(sourceItems.value, selectedDataDate.value, activeTrendView.value));
  const filteredItems = computed(() => filterTrends({ items: items.value, searchTerm: searchTerm.value, statusFilter: statusFilter.value }));
  const presetCounts = computed(() => buildFilterPresetCounts({ items: filteredItems.value, selectedDataDate: selectedDataDate.value }));
  const visibleItems = computed(() => buildVisibleItems(filteredItems.value, selectedPreset.value, selectedDataDate.value, sortKey.value));
  const marketOverview = computed(() => buildMarketOverview({ criticalLabel: activeTrendViewMeta.value.criticalLabel, items: visibleItems.value }));
  const selectedItem = computed(() => visibleItems.value.find((item) => item.code === selectedCode.value) ?? visibleItems.value[0] ?? null);
  const trendViewNotice = computed(() => buildTrendViewNotice(activeTrendView.value, sourceItems.value, availableDates.value));

  return {
    activeDatasetView,
    activeTrendView,
    activeTrendViewMeta,
    availableDates,
    compareCodes,
    dataset,
    items,
    marketOverview,
    presetCounts,
    recentCompareCodes,
    searchTerm,
    selectedCode,
    selectedDataDate,
    selectedItem,
    selectedPreset,
    sortKey,
    statusFilter,
    trendViewNotice,
    visibleItems,
  };
}

function registerDashboardWatchers(state: DashboardState) {
  watch(state.dataset, (dataset) => syncActiveTrendView(state.activeTrendView, dataset ?? null), { immediate: true });
  watch(state.availableDates, (dates) => syncSelectedDate(state.selectedDataDate, dates), { immediate: true });
  watch(state.visibleItems, (items) => syncSelectedCode(state.selectedCode, items), { immediate: true });
  watch(state.selectedItem, (item) => syncCompareCodesWithSelection(state.compareCodes, item), { immediate: true });
  watch(state.items, (items) => syncCodesWithAvailableItems(state, items));
}

function buildVisibleDateItems(
  sourceItems: readonly TrendItem[],
  selectedDate: string,
  trendView: TrendViewKey,
): TrendItem[] {
  if (selectedDate.length === 0) {
    return [];
  }

  return buildTrendItemsForDate(sourceItems, selectedDate, trendView);
}

function buildVisibleItems(
  items: readonly TrendItem[],
  selectedPreset: FilterPresetKey,
  selectedDataDate: string,
  sortKey: SortKey,
): TrendItem[] {
  const presetItems = applyFilterPreset({
    items: [...items],
    presetKey: selectedPreset,
    selectedDataDate,
  });

  return sortTrends(presetItems, sortKey);
}

function changeTrendView(state: DashboardState, nextView: TrendViewKey) {
  state.activeTrendView.value = nextView;
}

function selectTrendItem(state: DashboardState, item: TrendItem) {
  state.selectedCode.value = item.code;
}

function toggleCompareItem(state: DashboardState, item: TrendItem) {
  if (item.code === state.selectedCode.value) {
    return;
  }

  if (state.compareCodes.value.includes(item.code)) {
    state.compareCodes.value = state.compareCodes.value.filter((code) => code !== item.code);
    return;
  }

  state.compareCodes.value = [...state.compareCodes.value, item.code];
  rememberRecentCompareCode(state.recentCompareCodes, item.code);
}

function updateCompareCodes(state: DashboardState, nextCodes: string[]) {
  const normalizedCodes = normalizeCompareCodes(nextCodes, state.items.value, state.selectedCode.value);

  normalizedCodes
    .filter((code) => !state.compareCodes.value.includes(code))
    .forEach((code) => rememberRecentCompareCode(state.recentCompareCodes, code));

  state.compareCodes.value = normalizedCodes;
}

function resetDashboardFilters(state: DashboardState) {
  state.searchTerm.value = '';
  state.sortKey.value = 'rank-asc';
  state.statusFilter.value = 'ALL';
  state.selectedPreset.value = 'all';
  state.selectedDataDate.value = state.availableDates.value[state.availableDates.value.length - 1] ?? '';
}

function syncSelectedDate(selectedDataDate: DashboardState['selectedDataDate'], dates: string[]) {
  if (dates.length === 0) {
    selectedDataDate.value = '';
    return;
  }

  if (!dates.includes(selectedDataDate.value)) {
    selectedDataDate.value = dates[dates.length - 1];
  }
}

function syncActiveTrendView(activeTrendView: DashboardState['activeTrendView'], dataset: TrendDataset | null) {
  if (!dataset) {
    activeTrendView.value = DEFAULT_TREND_VIEW_KEY;
    return;
  }

  if (!dataset.viewOrder.includes(activeTrendView.value)) {
    activeTrendView.value = dataset.defaultViewKey;
  }
}

function syncSelectedCode(selectedCode: DashboardState['selectedCode'], items: TrendItem[]) {
  if (!items.some((item) => item.code === selectedCode.value)) {
    selectedCode.value = items[0]?.code ?? '';
  }
}

function syncCompareCodesWithSelection(compareCodes: DashboardState['compareCodes'], item: TrendItem | null) {
  if (!item) {
    compareCodes.value = [];
    return;
  }

  compareCodes.value = compareCodes.value.filter((code) => code !== item.code);
}

function syncCodesWithAvailableItems(state: DashboardState, items: TrendItem[]) {
  state.compareCodes.value = normalizeCompareCodes(state.compareCodes.value, items, state.selectedCode.value);
  state.recentCompareCodes.value = state.recentCompareCodes.value.filter((code) => items.some((item) => item.code === code));
}

function rememberRecentCompareCode(recentCompareCodes: DashboardState['recentCompareCodes'], code: string) {
  recentCompareCodes.value = [code, ...recentCompareCodes.value.filter((value) => value !== code)];
}
