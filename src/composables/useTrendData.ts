import { onBeforeUnmount, onMounted, ref } from 'vue';
import { AUTO_REFRESH_INTERVAL_SECONDS } from '../constants';
import type { AutoRefreshState, DashboardResponse, RefreshRun, TrendDataset } from '../types';

interface TrendDataState {
  autoRefresh: ReturnType<typeof ref<AutoRefreshState | null>>;
  dataset: ReturnType<typeof ref<TrendDataset | null>>;
  errorMessage: ReturnType<typeof ref<string>>;
  isLoading: ReturnType<typeof ref<boolean>>;
  lastRun: ReturnType<typeof ref<RefreshRun | null>>;
  serverRefreshing: ReturnType<typeof ref<boolean>>;
}

export function useTrendData() {
  const state = createState();
  let pollTimer: number | null = null;
  let isRequestInFlight = false;

  onMounted(async () => {
    await loadDashboard(state, true);
  });

  onBeforeUnmount(() => clearPollTimer(pollTimer));

  return {
    autoRefresh: state.autoRefresh,
    dataset: state.dataset,
    errorMessage: state.errorMessage,
    isLoading: state.isLoading,
    lastRun: state.lastRun,
    loadTrendData: () => loadDashboard(state, true),
    serverRefreshing: state.serverRefreshing,
  };

  async function loadDashboard(currentState: TrendDataState, isInitialLoad: boolean) {
    if (isRequestInFlight) {
      return;
    }

    isRequestInFlight = true;

    if (isInitialLoad) {
      currentState.isLoading.value = true;
    }

    try {
      applyDashboard(currentState, await requestDashboard('/api/dashboard'));
      currentState.errorMessage.value = '';
    } catch (error) {
      currentState.errorMessage.value = error instanceof Error ? error.message : '未知错误';
    } finally {
      isRequestInFlight = false;

      if (isInitialLoad) {
        currentState.isLoading.value = false;
      }

      pollTimer = scheduleNextPoll(currentState, () => loadDashboard(currentState, false), pollTimer);
    }
  }
}

function createState(): TrendDataState {
  return {
    autoRefresh: ref<AutoRefreshState | null>(null),
    dataset: ref<TrendDataset | null>(null),
    errorMessage: ref(''),
    isLoading: ref(true),
    lastRun: ref<RefreshRun | null>(null),
    serverRefreshing: ref(false),
  };
}

async function requestDashboard(url: string) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return (await response.json()) as DashboardResponse;
}

function applyDashboard(state: TrendDataState, payload: DashboardResponse) {
  state.autoRefresh.value = payload.autoRefresh;
  state.dataset.value = payload.dataset;
  state.lastRun.value = payload.lastRun;
  state.serverRefreshing.value = payload.isRefreshing;
}

function scheduleNextPoll(
  state: TrendDataState,
  callback: () => void,
  previousTimer: number | null = null,
): number {
  clearPollTimer(previousTimer);

  const intervalSeconds = state.autoRefresh.value?.intervalSeconds ?? AUTO_REFRESH_INTERVAL_SECONDS;
  return window.setTimeout(callback, intervalSeconds * 1000);
}

function clearPollTimer(pollTimer: number | null) {
  if (pollTimer !== null) {
    window.clearTimeout(pollTimer);
  }
}

async function readErrorMessage(response: Response) {
  const prefix = '数据加载失败';

  try {
    const payload = (await response.json()) as { error?: string };
    return payload.error ? `${prefix}：${payload.error}` : `${prefix}：${response.status}`;
  } catch {
    return `${prefix}：${response.status}`;
  }
}
