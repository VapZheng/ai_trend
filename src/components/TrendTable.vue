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
.table-card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 24px;
  box-shadow: var(--shadow-md);
  padding: 20px;
  transition: all 200ms ease-out;
}

.table-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.table-head h3 {
  margin: 0 0 8px;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 600;
}

.table-head p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.table-head__meta {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.desktop-table {
  overflow-x: auto;
}

.mobile-list {
  display: none;
  flex-direction: column;
  gap: 12px;
}

.mobile-card {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-bg-secondary);
  cursor: pointer;
  transition: all 150ms ease-out;
  text-align: left;
  font-size: 13px;
}

.mobile-card:hover {
  border-color: var(--color-primary);
  background: var(--color-bg-tertiary);
  box-shadow: var(--shadow-sm);
}

.mobile-card--active {
  border-color: var(--color-primary);
  background: rgba(37, 99, 235, 0.08);
  box-shadow: inset 3px 0 0 var(--color-primary);
}

@media (prefers-color-scheme: dark) {
  .mobile-card--active {
    background: rgba(37, 99, 235, 0.15);
  }
}

html.dark-mode .mobile-card--active {
  background: rgba(37, 99, 235, 0.15);
}

.mobile-card--compared {
  opacity: 0.7;
}

.mobile-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.mobile-card__head strong {
  display: block;
  color: var(--color-text-primary);
  font-weight: 600;
  margin-bottom: 4px;
}

.mobile-card__head p {
  margin: 0;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.mobile-card__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.mobile-card__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.mobile-card__hint {
  color: var(--color-text-tertiary);
  font-size: 13px;
}

:deep(.trend-table) {
  background: transparent;
  color: var(--color-text-primary);
}

:deep(.trend-table .el-table__header) {
  background: var(--color-bg-secondary);
}

:deep(.trend-table .el-table__header th) {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

:deep(.trend-table .el-table__body tr) {
  background: transparent;
  transition: all 150ms ease-out;
}

:deep(.trend-table .el-table__body tr:hover > td) {
  background: var(--color-bg-secondary);
}

:deep(.trend-table .el-table__body td) {
  background: transparent;
  border-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

:deep(.trend-row--active td) {
  background: rgba(37, 99, 235, 0.08);
}

@media (prefers-color-scheme: dark) {
  :deep(.trend-row--active td) {
    background: rgba(37, 99, 235, 0.15);
  }
}

html.dark-mode :deep(.trend-row--active td) {
  background: rgba(37, 99, 235, 0.15);
}

:deep(.trend-row--compared td.el-table__cell) {
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.strength-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rank-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-lighter);
  color: var(--color-primary);
  font-weight: 600;
  font-size: 12px;
}

@media (prefers-color-scheme: dark) {
  .rank-number {
    background: rgba(37, 99, 235, 0.2);
  }
}

html.dark-mode .rank-number {
  background: rgba(37, 99, 235, 0.2);
}

@media (max-width: 768px) {
  .desktop-table {
    display: none;
  }

  .mobile-list {
    display: flex;
  }

  .mobile-card__actions {
    display: grid;
  }

  .mobile-card__actions .el-button {
    width: 100%;
  }
}
</style>
