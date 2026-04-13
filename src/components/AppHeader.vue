<script setup lang="ts">
import { computed, ref } from 'vue';
import { AUTO_REFRESH_CONSTRAINT_NOTE } from '../constants';
import type { AutoRefreshState, TrendViewKey, TrendViewOption } from '../types';

const props = defineProps<{
  activeTrendView: TrendViewKey;
  autoRefresh: AutoRefreshState | null;
  isRefreshing: boolean;
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

const showDetails = ref(false);

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
const collectedAtLabel = computed(() => {
  if (props.updatedAt.length === 0) {
    return '暂无记录';
  }

  return props.updatedAt;
});
const autoRefreshSummary = computed(() => {
  const intervalSeconds = props.autoRefresh?.intervalSeconds ?? 10;
  if (props.isRefreshing) {
    return `默认 ${intervalSeconds} 秒自动取数，仅在北京时间 09:00-15:15 生效，当前执行中。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
  }

  if (props.autoRefresh?.nextRunAt) {
    return `默认 ${intervalSeconds} 秒自动取数，仅在北京时间 09:00-15:15 生效，下次执行 ${props.autoRefresh.nextRunAt}。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
  }

  return `默认 ${intervalSeconds} 秒自动取数，仅在北京时间 09:00-15:15 生效。${AUTO_REFRESH_CONSTRAINT_NOTE}`;
});
const freshnessTagType = computed(() => {
  if (props.isRefreshing) {
    return 'primary';
  }

  return isLatestView.value ? 'success' : 'warning';
});

function handleTrendViewChange(value: string | number | boolean) {
  emit('update:activeTrendView', value as TrendViewKey);
}

function toggleDetails() {
  showDetails.value = !showDetails.value;
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
        <el-button
          v-if="freshnessNote"
          link
          type="primary"
          size="small"
          :icon="showDetails ? 'CaretTop' : 'CaretBottom'"
          @click="toggleDetails"
          aria-label="切换详细信息"
        />
      </div>

      <div class="app-header__fact-compact">
        <span class="app-header__fact-label">采集</span>
        <el-tag effect="plain" round size="small" type="info">
          {{ collectedAtLabel }}
        </el-tag>
      </div>
    </div>

    <transition name="slide-fade">
      <div v-if="showDetails" class="app-header__details">
        <div class="app-header__detail-item">
          <span class="app-header__detail-label">数据时间</span>
          <span class="app-header__detail-value">{{ freshnessNote }}</span>
        </div>
        <div class="app-header__detail-item">
          <span class="app-header__detail-label">采集时间</span>
          <span class="app-header__detail-value">{{ collectedAtLabel }}</span>
        </div>
        <div class="app-header__detail-item">
          <span class="app-header__detail-label">自动刷新</span>
          <span class="app-header__detail-value">{{ autoRefreshSummary }}</span>
        </div>
      </div>
    </transition>
  </section>
</template>
