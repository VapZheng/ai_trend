<script setup lang="ts">
import type { TrendItem, TrendViewMeta } from '../types';
import { formatDate, formatNumber, formatPercent } from '../utils/formatters';
import { getStatusTagType, getStrengthTagType } from '../utils/trends';

const props = defineProps<{
  items: TrendItem[];
  selectedCode: string;
  trendView: TrendViewMeta;
}>();

const emit = defineEmits<{
  select: [item: TrendItem];
  'view-detail': [item: TrendItem];
}>();

function rowClassName({ row }: { row: TrendItem }) {
  return row.code === props.selectedCode ? 'trend-row trend-row--active' : 'trend-row';
}
</script>

<template>
  <div class="desktop-table">
    <el-table class="trend-table" size="small" :data="items" :row-class-name="rowClassName" @row-click="emit('select', $event)">
      <el-table-column label="趋势强度" min-width="120">
        <template #default="scope">
          <div class="strength-cell">
            <span class="rank-number">{{ scope.row.rank }}</span>
            <el-tag :type="getStrengthTagType(scope.row.deviationRate)" round>
              {{ scope.row.trendStrength }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="code" label="代码" min-width="100" />
      <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />

      <el-table-column label="状态" min-width="90">
        <template #default="scope">
          <el-tag :type="getStatusTagType(scope.row.status)" round>
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="涨幅" min-width="100" align="right">
        <template #default="scope">{{ formatPercent(scope.row.dayChangePct) }}</template>
      </el-table-column>

      <el-table-column label="现价" min-width="100" align="right">
        <template #default="scope">{{ formatNumber(scope.row.close) }}</template>
      </el-table-column>

      <el-table-column :label="trendView.criticalLabel" min-width="120" align="right">
        <template #default="scope">{{ formatNumber(scope.row.critical) }}</template>
      </el-table-column>

      <el-table-column label="偏离率" min-width="100" align="right">
        <template #default="scope">{{ formatPercent(scope.row.deviationRate) }}</template>
      </el-table-column>

      <el-table-column label="状态时间" min-width="120">
        <template #default="scope">{{ formatDate(scope.row.statusChangedAt) }}</template>
      </el-table-column>

      <el-table-column label="区间涨幅" min-width="110" align="right">
        <template #default="scope">{{ formatPercent(scope.row.intervalGainPct) }}</template>
      </el-table-column>

      <el-table-column label="明细" min-width="120" align="center">
        <template #default="scope">
          <el-button plain size="small" @click.stop="emit('view-detail', scope.row)">查看明细</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <div class="mobile-list">
    <button
      v-for="item in items"
      :key="item.code"
      :class="['mobile-card', { 'mobile-card--active': item.code === selectedCode }]"
      type="button"
      @click="emit('select', item)"
    >
      <div class="mobile-card__head">
        <div>
          <strong>{{ item.name }}</strong>
          <p>{{ item.code }}</p>
        </div>
        <el-tag :type="getStatusTagType(item.status)" round>{{ item.status }}</el-tag>
      </div>

      <div class="mobile-card__grid">
        <span>现价 {{ formatNumber(item.close) }}</span>
        <span>{{ trendView.shortLabel }}临界 {{ formatNumber(item.critical) }}</span>
        <span>偏离 {{ formatPercent(item.deviationRate) }}</span>
        <span>区间 {{ formatPercent(item.intervalGainPct) }}</span>
      </div>

      <div class="rotation-mobile-actions">
        <span class="rotation-mobile-actions__hint">点击卡片切换当前对象</span>
        <el-button plain size="small" @click.stop="emit('view-detail', item)">查看明细</el-button>
      </div>
    </button>
  </div>
</template>

<style scoped>
.rotation-mobile-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.rotation-mobile-actions__hint {
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 768px) {
  .rotation-mobile-actions {
    display: grid;
  }

  .rotation-mobile-actions .el-button {
    width: 100%;
  }
}
</style>
