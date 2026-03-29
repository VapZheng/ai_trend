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
    <div class="summary-grid">
      <el-card class="summary-card summary-card--accent" shadow="hover" role="region" aria-label="总体结论">
        <div class="summary-card__header">
          <i class="el-icon-data-analysis"></i>
          <p class="summary-label">总体结论</p>
        </div>
        <h2 class="summary-card__title">{{ market.conclusionTitle }}</h2>
        <p class="summary-card__note">{{ market.conclusionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover" role="region" aria-label="YES / NO 分布">
        <div class="summary-card__header">
          <i class="el-icon-pie-chart"></i>
          <p class="summary-label">YES / NO</p>
        </div>
        <h2 class="summary-card__title">{{ distributionValue }}</h2>
        <p class="summary-card__note">{{ distributionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover" role="region" aria-label="整体温度">
        <div class="summary-card__header">
          <i class="el-icon-temperature"></i>
          <p class="summary-label">整体温度</p>
        </div>
        <h2 class="summary-card__title">{{ hasMarketData ? formatPercent(market.averageDeviation) : '--' }}</h2>
        <p class="summary-card__note">{{ hasMarketData ? market.temperatureLabel : '等待数据' }}</p>
      </el-card>
    </div>
  </section>
</template>
