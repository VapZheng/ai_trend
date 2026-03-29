<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import type { TrendItem, TrendViewMeta } from '../types';
import { formatPercent, formatNumber } from '../utils/formatters';
import { buildComparisonOption } from '../utils/chart';

const props = defineProps<{
  activeItem: TrendItem | null;
  compareCodes: string[];
  items: TrendItem[];
  recentCompareCodes: string[];
  trendView: TrendViewMeta;
}>();

const emit = defineEmits<{
  'update:compareCodes': [value: string[]];
}>();

const chartElement = ref<HTMLDivElement | null>(null);
const pendingCompareCode = ref('');
let chartInstance: echarts.ECharts | null = null;

const itemMap = computed(() => new Map(props.items.map((item) => [item.code, item])));

const comparisonItems = computed(() => {
  if (!props.activeItem) {
    return [];
  }

  return buildUniqueCodes([props.activeItem.code, ...props.compareCodes])
    .map((code) => itemMap.value.get(code) ?? null)
    .filter((item): item is TrendItem => item !== null);
});

const extraCompareItems = computed(() => {
  if (!props.activeItem) {
    return [];
  }

  return comparisonItems.value.filter((item) => item.code !== props.activeItem?.code);
});

const candidateItems = computed(() => {
  const excludedCodes = new Set([
    props.activeItem?.code ?? '',
    ...props.compareCodes,
  ]);

  return props.items.filter((item) => !excludedCodes.has(item.code));
});

const recentCompareItems = computed(() => {
  const excludedCodes = new Set([
    props.activeItem?.code ?? '',
    ...props.compareCodes,
  ]);

  return buildUniqueCodes(props.recentCompareCodes)
    .map((code) => itemMap.value.get(code) ?? null)
    .filter((item): item is TrendItem => item !== null && !excludedCodes.has(item.code));
});

const insightText = computed(() => {
  if (!props.activeItem) {
    return '请选择一个指数查看走势细节。';
  }

  const relation = props.activeItem.status === 'YES' ? '高于' : '低于';
  const deviationText = formatPercent(Math.abs(props.activeItem.deviationRate));
  const compareCount = extraCompareItems.value.length;
  return `当前焦点指数 ${props.activeItem.name} 现价 ${formatNumber(props.activeItem.close)}，${relation}${props.trendView.criticalLabel} ${deviationText}，当前同屏对比 ${compareCount} 个指数。`;
});

function buildChart() {
  if (comparisonItems.value.length === 0) {
    chartInstance?.clear();
    return;
  }

  if (!chartElement.value) {
    return;
  }

  chartInstance ??= echarts.init(chartElement.value);
  chartInstance.setOption(buildComparisonOption(comparisonItems.value, props.trendView.criticalLabel), true);
}

function handleResize() {
  chartInstance?.resize();
}

function handleCompareCodesChange(nextCodes: string[]) {
  emit('update:compareCodes', nextCodes);
}

function handleCompareCodeSelect(code?: string) {
  if (!code || props.compareCodes.includes(code) || code === props.activeItem?.code) {
    pendingCompareCode.value = '';
    return;
  }

  handleCompareCodesChange([...props.compareCodes, code]);
  pendingCompareCode.value = '';
}

function handleCompareCodeRemove(code: string) {
  handleCompareCodesChange(props.compareCodes.filter((value) => value !== code));
}

function resetCompareCodes() {
  handleCompareCodesChange([]);
}

async function syncChart() {
  await nextTick();
  buildChart();
  chartInstance?.resize();
}

watch(comparisonItems, syncChart, { deep: true, flush: 'post' });
onMounted(() => {
  syncChart();
  window.addEventListener('resize', handleResize);
});
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});

function buildUniqueCodes(codes: string[]): string[] {
  return Array.from(new Set(codes));
}
</script>

<template>
  <section class="chart-card">
    <div class="table-head">
      <div>
        <h3>{{ activeItem?.name ?? `${trendView.shortLabel} 趋势图表` }}</h3>
        <p>{{ activeItem?.code ?? `从左侧 ${trendView.shortLabel} 趋势清单选择指数` }}</p>
      </div>
      <div class="table-head__meta">
        <el-tag effect="plain" round size="large" type="primary">{{ trendView.label }}</el-tag>
        <el-tag v-if="activeItem" :type="activeItem.status === 'YES' ? 'success' : 'danger'" round>
          {{ activeItem.status }}
        </el-tag>
      </div>
    </div>

    <div class="chart-toolbar">
      <p class="chart-note">图表显示各指数相对 {{ trendView.criticalLabel }} 的偏离率走势，可搜索加入对比，或在左侧清单一键加入。</p>

      <div class="compare-control">
        <el-select
          :model-value="pendingCompareCode"
          class="compare-search"
          clearable
          filterable
          placeholder="搜索代码或名称加入对比"
          size="large"
          @change="handleCompareCodeSelect"
          @update:model-value="pendingCompareCode = $event ?? ''"
        >
          <el-option
            v-for="item in candidateItems"
            :key="item.code"
            :label="`${item.name} · ${item.code}`"
            :value="item.code"
          >
            <div class="compare-option">
              <span>{{ item.name }}</span>
              <span class="compare-option__meta">{{ item.code }}</span>
            </div>
          </el-option>
        </el-select>

        <el-button plain size="large" @click="resetCompareCodes">仅看当前指数</el-button>
      </div>

      <div class="compare-section">
        <span class="compare-section__label">当前对比</span>
        <div class="compare-chip-list">
          <span v-if="activeItem" class="compare-chip compare-chip--primary">
            当前：{{ activeItem.name }}
          </span>
          <el-tag
            v-for="item in extraCompareItems"
            :key="item.code"
            closable
            effect="plain"
            round
            size="large"
            @close="handleCompareCodeRemove(item.code)"
          >
            {{ item.name }} · {{ item.code }}
          </el-tag>
        </div>
      </div>

      <div v-if="recentCompareItems.length > 0" class="compare-section">
        <span class="compare-section__label">最近加入</span>
        <div class="recent-compare__list">
          <el-button
            v-for="item in recentCompareItems"
            :key="item.code"
            plain
            size="small"
            @click="handleCompareCodeSelect(item.code)"
          >
            {{ item.name }}
          </el-button>
        </div>
      </div>
    </div>

    <div v-show="comparisonItems.length > 0" ref="chartElement" class="chart-stage"></div>
    <div v-show="comparisonItems.length === 0" class="chart-empty">请选择一个指数查看走势</div>

    <div class="chart-footnote">
      <p>{{ insightText }}</p>
      <div v-if="activeItem" class="chart-metrics">
        <span>日涨幅 {{ formatPercent(activeItem.dayChangePct) }}</span>
        <span>状态切换 {{ activeItem.statusChangedAt }}</span>
        <span>区间涨幅 {{ formatPercent(activeItem.intervalGainPct) }}</span>
      </div>
    </div>
  </section>
</template>
