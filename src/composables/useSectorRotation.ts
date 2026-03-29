import { computed, onMounted, ref, watch } from 'vue';
import type { Ref } from 'vue';
import type {
  RefreshRun,
  SectorRotationResponse,
  SectorRotationTarget,
  TrendDataset,
  TrendItem,
  TrendViewKey,
} from '../types';
import { buildMarketOverview } from '../utils/dashboardOverview';
import { DEFAULT_TREND_VIEW_KEY, TREND_VIEW_OPTIONS, getTrendViewMeta } from '../utils/trendViews';

interface SectorRotationState {
  dataset: Ref<TrendDataset | null>;
  errorMessage: Ref<string>;
  isLoading: Ref<boolean>;
  isRefreshing: Ref<boolean>;
  isSavingConfig: Ref<boolean>;
  lastRun: Ref<RefreshRun | null>;
  targets: Ref<SectorRotationTarget[]>;
}

export function useSectorRotation() {
  const state = createState();
  const activeTrendView = ref<TrendViewKey>(DEFAULT_TREND_VIEW_KEY);
  const selectedCode = ref('');
  const detailVisible = ref(false);

  const activeDatasetView = computed(() => state.dataset.value?.views[activeTrendView.value] ?? null);
  const activeTrendViewMeta = computed(() => getTrendViewMeta(activeTrendView.value));
  const items = computed(() => activeDatasetView.value?.items ?? []);
  const marketOverview = computed(() =>
    buildMarketOverview({
      criticalLabel: activeTrendViewMeta.value.criticalLabel,
      items: items.value,
    }),
  );
  const selectedItem = computed(() => items.value.find((item) => item.code === selectedCode.value) ?? items.value[0] ?? null);
  const selectedTarget = computed(() => state.targets.value.find((target) => target.code === selectedItem.value?.code) ?? null);

  onMounted(() => {
    void loadSectorRotation(state);
  });

  watch(state.dataset, (dataset) => syncActiveTrendView(activeTrendView, dataset ?? null), { immediate: true });
  watch(items, (nextItems) => syncSelectedCode(selectedCode, nextItems), { immediate: true });

  return {
    activeTrendView,
    activeTrendViewMeta,
    dataset: state.dataset,
    detailVisible,
    errorMessage: state.errorMessage,
    handleTrendViewChange: (value: TrendViewKey) => {
      activeTrendView.value = value;
    },
    isLoading: state.isLoading,
    isRefreshing: state.isRefreshing,
    isSavingConfig: state.isSavingConfig,
    items,
    lastRun: state.lastRun,
    marketOverview,
    openDetail: (item: TrendItem) => openDetail(detailVisible, selectedCode, item),
    refreshSectorRotation: () => refreshSectorRotation(state),
    removeTarget: (code: string) => mutateTargets(state, () => requestSectorRotation(`/api/sector-rotation/targets?code=${encodeURIComponent(code)}`, 'DELETE')),
    selectedItem,
    selectedTarget,
    setSelectedCode: (code: string) => {
      selectedCode.value = code;
    },
    targets: state.targets,
    trendViewOptions: TREND_VIEW_OPTIONS,
    addTarget: (code: string) => mutateTargets(state, () => requestSectorRotation('/api/sector-rotation/targets', 'POST', { code })),
  };
}

function createState(): SectorRotationState {
  return {
    dataset: ref<TrendDataset | null>(null),
    errorMessage: ref(''),
    isLoading: ref(true),
    isRefreshing: ref(false),
    isSavingConfig: ref(false),
    lastRun: ref<RefreshRun | null>(null),
    targets: ref<SectorRotationTarget[]>([]),
  };
}

async function loadSectorRotation(state: SectorRotationState) {
  await withBusy(state.isLoading, state.errorMessage, async () => {
    applySectorRotation(state, await requestSectorRotation('/api/sector-rotation'));
  });
}

async function refreshSectorRotation(state: SectorRotationState) {
  await withBusy(state.isRefreshing, state.errorMessage, async () => {
    applySectorRotation(state, await requestSectorRotation('/api/sector-rotation/refresh', 'POST'));
  });
}

async function mutateTargets(state: SectorRotationState, operation: () => Promise<SectorRotationResponse>) {
  await withBusy(state.isSavingConfig, state.errorMessage, async () => {
    await operation();
    await reloadAfterConfigChange(state);
  });
}

async function reloadAfterConfigChange(state: SectorRotationState) {
  applySectorRotation(state, await requestSectorRotation('/api/sector-rotation'));
  if (state.targets.value.length === 0) {
    state.dataset.value = null;
    return;
  }
  applySectorRotation(state, await requestSectorRotation('/api/sector-rotation/refresh', 'POST'));
}

async function requestSectorRotation(url: string, method = 'GET', body?: object) {
  const response = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, method));
  }

  return (await response.json()) as SectorRotationResponse;
}

function applySectorRotation(state: SectorRotationState, payload: SectorRotationResponse) {
  state.dataset.value = payload.dataset;
  state.lastRun.value = payload.lastRun;
  state.targets.value = payload.targets;
}

async function withBusy(
  busyRef: SectorRotationState['isLoading'],
  errorRef: SectorRotationState['errorMessage'],
  job: () => Promise<void>,
) {
  busyRef.value = true;
  errorRef.value = '';
  try {
    await job();
  } catch (error) {
    errorRef.value = error instanceof Error ? error.message : '未知错误';
  } finally {
    busyRef.value = false;
  }
}

async function readErrorMessage(response: Response, method: string) {
  const prefix = method === 'GET' ? '板块轮动数据加载失败' : '板块轮动请求执行失败';

  try {
    const payload = (await response.json()) as { error?: string };
    return payload.error ? `${prefix}：${payload.error}` : `${prefix}：${response.status}`;
  } catch {
    return `${prefix}：${response.status}`;
  }
}

function syncActiveTrendView(activeTrendView: Ref<TrendViewKey>, dataset: TrendDataset | null) {
  if (!dataset) {
    activeTrendView.value = DEFAULT_TREND_VIEW_KEY;
    return;
  }

  if (!dataset.viewOrder.includes(activeTrendView.value)) {
    activeTrendView.value = dataset.defaultViewKey;
  }
}

function syncSelectedCode(selectedCode: Ref<string>, items: TrendItem[]) {
  if (!items.some((item) => item.code === selectedCode.value)) {
    selectedCode.value = items[0]?.code ?? '';
  }
}

function openDetail(
  detailVisible: Ref<boolean>,
  selectedCode: Ref<string>,
  item: TrendItem,
) {
  selectedCode.value = item.code;
  detailVisible.value = true;
}
