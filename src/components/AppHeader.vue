<script setup lang="ts">
import { computed } from 'vue';
import { AUTO_REFRESH_CONSTRAINT_NOTE } from '../constants';
import type { AutoRefreshState, RefreshRun, TrendViewKey, TrendViewOption } from '../types';
import { getRunSourceLabel } from '../utils/dashboardOverview';

const props = defineProps<{
  activeTrendView: TrendViewKey;
  autoRefresh: AutoRefreshState | null;
  isRefreshing: boolean;
  lastRun: RefreshRun | null;
  latestDataDate: string;
  selectedDataDate: string;
  trendViewDescription: string;
  trendViewLabel: string;
  trendViewOptions: TrendViewOption[];
  updatedAt: string;
}>();

const emit = defineEmits<{
  'update:activeTrendView': [value: TrendViewKey];
}>();

const isLatestView = computed(() => props.latestDataDate.length > 0 && props.selectedDataDate === props.latestDataDate);
const headerDescription = computed(() => `当前按 ${props.trendViewLabel} 观察市场强弱。${props.trendViewDescription}`);
const freshnessLabel = computed(() => {
  if (props.isRefreshing) {
    return '自动取数中';
  }

  if (props.latestDataDate.length === 0) {
    return '暂无数据';
  }

  return isLatestView.value ? '最新数据' : '历史截面';
});
const freshnessNote = computed(() => {
  if (props.latestDataDate.length === 0) {
    return '完成首次自动取数后显示最新交易日与后台更新时间。';
  }

  if (isLatestView.value) {
    return `数据 ${props.latestDataDate} · 后台 ${props.updatedAt}`;
  }

  const selectedDate = props.selectedDataDate || '--';
  return `当前 ${selectedDate} · 最新 ${props.latestDataDate} · 后台 ${props.updatedAt}`;
});
const executionLabel = computed(() => {
  if (props.isRefreshing) {
    return '执行中';
  }

  if (!props.lastRun) {
    return '暂无记录';
  }

  return props.lastRun.status === 'success' ? '执行成功' : '执行失败';
});
const executionNote = computed(() => {
  if (!props.lastRun) {
    return '完成首次自动取数后，这里会显示最近一次执行来源和完成时间。';
  }

  const runTime = props.lastRun.finishedAt ?? props.lastRun.startedAt;
  return `${getRunSourceLabel(props.lastRun.source)} · ${runTime}`;
});
const autoRefreshSummary = computed(() => {
  const intervalSeconds = props.autoRefresh?.intervalSeconds ?? 10;
  if (props.isRefreshing) {
    return `默认 ${intervalSeconds} 秒自动取数，当前执行中。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
  }

  if (props.autoRefresh?.nextRunAt) {
    return `默认 ${intervalSeconds} 秒自动取数，下次执行 ${props.autoRefresh.nextRunAt}。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
  }

  return `默认 ${intervalSeconds} 秒自动取数。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
});
const freshnessTagType = computed(() => {
  if (props.isRefreshing) {
    return 'primary';
  }

  return isLatestView.value ? 'success' : 'warning';
});
const executionTagType = computed(() => {
  if (props.isRefreshing) {
    return 'primary';
  }

  if (props.lastRun?.status === 'failed') {
    return 'warning';
  }

  if (props.lastRun?.status === 'success') {
    return 'success';
  }

  return 'info';
});

function handleTrendViewChange(value: string | number | boolean) {
  emit('update:activeTrendView', value as TrendViewKey);
}
</script>

<template>
  <section class="hero-card app-header">
    <div class="app-header__top">
      <div class="app-header__copy">
        <div class="app-header__title-row">
          <h1>趋势看板</h1>
          <el-tag effect="dark" round size="large" type="primary">{{ trendViewLabel }}</el-tag>
        </div>
      </div>

      <el-segmented
        :model-value="activeTrendView"
        :options="trendViewOptions"
        class="app-header__switch"
        size="large"
        @update:model-value="handleTrendViewChange"
      />
    </div>

    <div class="app-header__status">
      <div class="app-header__fact-compact">
        <span class="app-header__fact-label">数据</span>
        <el-tag :type="freshnessTagType" effect="plain" round size="small">
          <span v-if="isRefreshing" class="loading-spinner">⟳</span>
          {{ freshnessLabel }}
        </el-tag>
        <span class="app-header__fact-time">{{ freshnessNote }}</span>
      </div>

      <div class="app-header__fact-compact">
        <span class="app-header__fact-label">执行</span>
        <el-tag :type="executionTagType" effect="plain" round size="small" role="status" :aria-live="lastRun?.status === 'failed' ? 'polite' : 'off'">
          <span v-if="isRefreshing" class="loading-spinner">⟳</span>
          {{ executionLabel }}
        </el-tag>
        <span class="app-header__fact-time">{{ executionNote }}</span>
      </div>
    </div>
  </section>
</template>
