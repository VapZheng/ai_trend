<script setup lang="ts">
import { computed } from 'vue';
import type { TrendViewMeta } from '../types';
import type { MarketOverview } from '../utils/dashboardOverview';
import { formatPercent } from '../utils/formatters';

const props = defineProps<{
  market: MarketOverview;
  trendView: TrendViewMeta;
}>();

const hasMarketData = computed(() => props.market.totalCount > 0);
const distributionValue = computed(() => {
  return hasMarketData.value ? `${props.market.yesCount} : ${props.market.noCount}` : '--';
});
const distributionNote = computed(() => {
  if (!hasMarketData.value) {
    return '当前筛选范围内暂无可统计分布';
  }

  return `YES ${(props.market.yesRatio * 100).toFixed(1)}% · NO ${(props.market.noRatio * 100).toFixed(1)}%`;
});
const strongestNote = computed(() => {
  if (!props.market.strongestItem) {
    return '当前筛选范围内暂无最强标的';
  }

  return `${props.market.strongestItem.code} · ${formatPercent(props.market.strongestItem.deviationRate)}`;
});
</script>

<template>
  <section class="summary-section">
    <div class="section-head">
      <div>
        <h3>市场摘要</h3>
        <p>所有结论均基于当前激活的 {{ trendView.label }} 视图。</p>
      </div>
      <el-tag effect="plain" round size="large" type="primary">{{ trendView.label }}</el-tag>
    </div>

    <div class="summary-grid">
      <el-card class="summary-card summary-card--accent" shadow="hover">
        <p class="summary-label">{{ trendView.shortLabel }} 总体结论</p>
        <h2>{{ market.conclusionTitle }}</h2>
        <p class="summary-note">{{ market.conclusionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover">
        <p class="summary-label">{{ trendView.shortLabel }} YES / NO 分布</p>
        <h2>{{ distributionValue }}</h2>
        <p class="summary-note">{{ distributionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover">
        <p class="summary-label">{{ trendView.shortLabel }} 整体温度</p>
        <h2>{{ hasMarketData ? formatPercent(market.averageDeviation) : '--' }}</h2>
        <p class="summary-note">{{ hasMarketData ? market.temperatureLabel : '等待可用数据后展示温度结论' }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover">
        <p class="summary-label">{{ trendView.shortLabel }} 最强标的</p>
        <h2>{{ market.strongestItem?.name ?? '--' }}</h2>
        <p class="summary-note">{{ strongestNote }}</p>
      </el-card>
    </div>
  </section>
</template>
