<script setup lang="ts">
import { computed } from 'vue';
import { DataAnalysis, PieChart, Opportunity } from '@element-plus/icons-vue';
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
</script>

<template>
  <section class="summary-section">
    <div class="summary-grid">
      <el-card class="summary-card summary-card--accent" shadow="hover" role="region" aria-label="总体结论">
        <div class="summary-card__header">
          <el-icon><DataAnalysis /></el-icon>
          <p class="summary-label">总体结论</p>
        </div>
        <h2 class="summary-card__title">{{ market.conclusionTitle }}</h2>
        <p class="summary-card__note">{{ market.conclusionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover" role="region" aria-label="YES / NO 分布">
        <div class="summary-card__header">
          <el-icon><PieChart /></el-icon>
          <p class="summary-label">YES / NO</p>
        </div>
        <h2 class="summary-card__title">{{ distributionValue }}</h2>
        <p class="summary-card__note">{{ distributionNote }}</p>
      </el-card>

      <el-card class="summary-card" shadow="hover" role="region" aria-label="整体温度">
        <div class="summary-card__header">
          <el-icon><Opportunity /></el-icon>
          <p class="summary-label">整体温度</p>
        </div>
        <h2 class="summary-card__title">{{ hasMarketData ? formatPercent(market.averageDeviation) : '--' }}</h2>
        <p class="summary-card__note">{{ hasMarketData ? market.temperatureLabel : '等待数据' }}</p>
      </el-card>
    </div>
  </section>
</template>

<style scoped>
.summary-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.summary-card__header .el-icon {
  color: var(--color-primary);
  font-size: 16px;
}
</style>
