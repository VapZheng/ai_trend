<script setup lang="ts">
import type { TrendItem, TrendViewMeta } from '../types';
import { formatDate, formatNumber, formatPercent } from '../utils/formatters';
import { getStatusTagType, getStrengthTagType } from '../utils/trends';

const props = defineProps<{
  compareCodes: string[];
  items: TrendItem[];
  selectedCode: string;
  trendView: TrendViewMeta;
}>();

const emit = defineEmits<{
  select: [item: TrendItem];
  'toggle-compare': [item: TrendItem];
}>();

function handleSelect(item: TrendItem) {
  emit('select', item);
}

function handleToggleCompare(item: TrendItem) {
  emit('toggle-compare', item);
}

function isCompared(code: string): boolean {
  return props.compareCodes.includes(code);
}

function getCompareActionLabel(item: TrendItem): string {
  if (item.code === props.selectedCode) {
    return '当前指数';
  }

  return isCompared(item.code) ? '移除对比' : '加入对比';
}

function getMobileHint(item: TrendItem): string {
  if (item.code === props.selectedCode) {
    return '当前主图';
  }

  return isCompared(item.code) ? '已加入对比' : '点卡片查看走势';
}

function rowClassName({ row }: { row: TrendItem }) {
  const classNames = ['trend-row'];

  if (row.code === props.selectedCode) {
    classNames.push('trend-row--active');
  }

  if (isCompared(row.code)) {
    classNames.push('trend-row--compared');
  }

  return classNames.join(' ');
}
</script>

<template>
  <section class="table-card">
    <div class="table-head">
      <div>
        <h3>{{ props.trendView.shortLabel }} 趋势清单</h3>
        <p>当前按 {{ props.trendView.criticalLabel }} 展示，点击行切换主图，用按钮一键加入或移除右侧对比。</p>
      </div>
      <div class="table-head__meta">
        <el-tag effect="plain" round size="large" type="primary">{{ props.trendView.label }}</el-tag>
        <el-tag effect="plain" round type="info">共 {{ items.length }} 个标的</el-tag>
      </div>
    </div>

    <div class="desktop-table">
      <el-table class="trend-table" size="small" :data="items" :row-class-name="rowClassName" @row-click="handleSelect">
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
        <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />

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

        <el-table-column :label="props.trendView.criticalLabel" min-width="120" align="right">
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

        <el-table-column label="对比" min-width="110" align="center">
          <template #default="scope">
            <el-button
              :disabled="scope.row.code === selectedCode"
              plain
              size="small"
              @click.stop="handleToggleCompare(scope.row)"
            >
              {{ getCompareActionLabel(scope.row) }}
            </el-button>
          </template>
        </el-table-column>

      </el-table>
    </div>

    <div class="mobile-list">
      <button
        v-for="item in items"
        :key="item.code"
        :class="[
          'mobile-card',
          {
            'mobile-card--active': item.code === selectedCode,
            'mobile-card--compared': compareCodes.includes(item.code),
          },
        ]"
        type="button"
        @click="handleSelect(item)"
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
          <span>{{ props.trendView.shortLabel }}临界 {{ formatNumber(item.critical) }}</span>
          <span>偏离 {{ formatPercent(item.deviationRate) }}</span>
          <span>区间 {{ formatPercent(item.intervalGainPct) }}</span>
        </div>

        <div class="mobile-card__actions">
          <span class="mobile-card__hint">{{ getMobileHint(item) }}</span>
          <el-button :disabled="item.code === selectedCode" plain size="small" @click.stop="handleToggleCompare(item)">
            {{ getCompareActionLabel(item) }}
          </el-button>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.mobile-card__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.mobile-card__actions {
  margin-top: 12px;
}

.mobile-card__hint {
  color: #64748b;
  font-size: 13px;
}

:deep(.trend-row--compared td.el-table__cell) {
  box-shadow: inset 3px 0 0 rgba(59, 130, 246, 0.9);
}

@media (max-width: 768px) {
  .mobile-card__actions {
    display: grid;
  }

  .mobile-card__actions .el-button {
    width: 100%;
  }
}
</style>
