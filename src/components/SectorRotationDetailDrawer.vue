<script setup lang="ts">
import { computed } from 'vue';
import type { SectorRotationTarget, TrendHistoryPoint, TrendItem, TrendViewMeta } from '../types';
import { formatDate, formatNumber, formatPercent } from '../utils/formatters';

const props = defineProps<{
  item: TrendItem | null;
  modelValue: boolean;
  target: SectorRotationTarget | null;
  trendView: TrendViewMeta;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const historyRows = computed(() => [...(props.item?.history ?? [])].reverse());

function getDeviationRate(point: TrendHistoryPoint): number {
  if (point.critical === 0) {
    return 0;
  }
  return Number((((point.close - point.critical) / point.critical) * 100).toFixed(2));
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    append-to-body
    destroy-on-close
    size="92%"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="rotation-detail__header">
        <div>
          <h3>{{ item?.name ?? '板块轮动明细' }}</h3>
          <p>{{ item?.code ?? '--' }} · {{ target?.securityTypeName ?? '未识别类型' }}</p>
        </div>
        <div class="rotation-detail__tags">
          <el-tag v-if="target" effect="plain" round>{{ target.securityTypeName }}</el-tag>
          <el-tag v-if="item" :type="item.status === 'YES' ? 'success' : 'danger'" round>
            {{ item.status }}
          </el-tag>
          <el-tag effect="plain" round type="primary">{{ trendView.label }}</el-tag>
        </div>
      </div>
    </template>

    <div v-if="item" class="rotation-detail">
      <div class="rotation-detail__summary">
        <article class="rotation-detail__metric">
          <span>现价</span>
          <strong>{{ formatNumber(item.close) }}</strong>
        </article>
        <article class="rotation-detail__metric">
          <span>{{ trendView.criticalLabel }}</span>
          <strong>{{ formatNumber(item.critical) }}</strong>
        </article>
        <article class="rotation-detail__metric">
          <span>偏离率</span>
          <strong>{{ formatPercent(item.deviationRate) }}</strong>
        </article>
        <article class="rotation-detail__metric">
          <span>区间涨幅</span>
          <strong>{{ formatPercent(item.intervalGainPct) }}</strong>
        </article>
      </div>

      <p class="rotation-detail__note">
        明细清单直接使用当前 {{ trendView.label }} 的真实 K 线序列，展示日期、收盘价、临界值、状态与偏离率。
      </p>

      <el-table :data="historyRows" size="small">
        <el-table-column label="日期" min-width="110">
          <template #default="scope">{{ formatDate(scope.row.date) }}</template>
        </el-table-column>
        <el-table-column label="收盘价" min-width="110" align="right">
          <template #default="scope">{{ formatNumber(scope.row.close) }}</template>
        </el-table-column>
        <el-table-column :label="trendView.criticalLabel" min-width="120" align="right">
          <template #default="scope">{{ formatNumber(scope.row.critical) }}</template>
        </el-table-column>
        <el-table-column label="偏离率" min-width="110" align="right">
          <template #default="scope">{{ formatPercent(getDeviationRate(scope.row)) }}</template>
        </el-table-column>
        <el-table-column label="状态" min-width="90" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'YES' ? 'success' : 'danger'" round>
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-else description="当前没有可展示的明细对象。" />
  </el-drawer>
</template>

<style scoped>
.rotation-detail {
  display: grid;
  gap: 16px;
}

.rotation-detail__header h3,
.rotation-detail__header p {
  margin: 0;
}

.rotation-detail__header p,
.rotation-detail__note {
  color: #64748b;
}

.rotation-detail__header,
.rotation-detail__tags,
.rotation-detail__summary {
  display: flex;
  gap: 12px;
}

.rotation-detail__header,
.rotation-detail__summary {
  justify-content: space-between;
  align-items: flex-start;
}

.rotation-detail__summary {
  flex-wrap: wrap;
}

.rotation-detail__metric {
  min-width: 140px;
  padding: 14px 16px;
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  background: #f8fbff;
}

.rotation-detail__metric span {
  color: #64748b;
  font-size: 13px;
}

.rotation-detail__metric strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
  color: #10233c;
}

.rotation-detail__note {
  margin: 0;
}

@media (max-width: 768px) {
  .rotation-detail__header,
  .rotation-detail__summary {
    flex-direction: column;
  }
}
</style>
