<script setup lang="ts">
import { computed } from 'vue';
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

const collectedAtLabel = computed(() => {
  if (props.updatedAt.length === 0) {
    return '暂无记录';
  }

  return props.updatedAt;
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
      <span class="app-header__meta-label">采集时间</span>
      <span class="app-header__meta-value">{{ collectedAtLabel }}</span>
    </div>
  </section>
</template>
