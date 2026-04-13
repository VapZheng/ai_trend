<script setup lang="ts">
import AppHeader from './AppHeader.vue';
import FilterBar from './FilterBar.vue';
import SummaryCards from './SummaryCards.vue';
import TrendChart from './TrendChart.vue';
import TrendTable from './TrendTable.vue';
import { useDashboardViewModel } from '../composables/useDashboardViewModel';

const {
  activeDatasetView,
  activeTrendView,
  activeTrendViewMeta,
  autoRefresh,
  availableDates,
  compareCodes,
  dataset,
  errorMessage,
  handleCompareCodesChange,
  handleSelect,
  handleToggleCompare,
  handleTrendViewChange,
  isLoading,
  items,
  marketOverview,
  presetCounts,
  recentCompareCodes,
  resetFilters,
  searchTerm,
  selectedDataDate,
  selectedItem,
  selectedPreset,
  serverRefreshing,
  sortKey,
  statusFilter,
  trendViewNotice,
  trendViewOptions,
  visibleItems,
} = useDashboardViewModel();
</script>

<template>
  <template v-if="isLoading">
    <el-skeleton :rows="10" animated />
  </template>

  <template v-else>
    <el-alert v-if="errorMessage" :closable="false" :title="errorMessage" class="page-alert" type="error" />

    <template v-if="dataset">
      <AppHeader
        :active-trend-view="activeTrendView"
        :auto-refresh="autoRefresh ?? null"
        :is-refreshing="Boolean(serverRefreshing)"
        :latest-data-date="activeDatasetView?.latestDataDate ?? dataset.latestDataDate"
        :selected-data-date="selectedDataDate"
        :trend-view-description="activeTrendViewMeta.description"
        :trend-view-label="activeTrendViewMeta.label"
        :trend-view-options="trendViewOptions"
        :updated-at="dataset.updatedAt"
        @update:active-trend-view="handleTrendViewChange"
      />

      <SummaryCards :market="marketOverview" :trend-view="activeTrendViewMeta" />

      <FilterBar
        :available-dates="availableDates"
        :preset-counts="presetCounts"
        :trend-view="activeTrendViewMeta"
        :trend-view-notice="trendViewNotice"
        v-model:selected-data-date="selectedDataDate"
        v-model:selected-preset="selectedPreset"
        v-model:search-term="searchTerm"
        v-model:sort-key="sortKey"
        v-model:status-filter="statusFilter"
        @reset="resetFilters"
      />

      <section class="content-grid">
        <TrendTable
          :compare-codes="compareCodes"
          :items="visibleItems"
          :selected-code="selectedItem?.code ?? ''"
          :trend-view="activeTrendViewMeta"
          @select="handleSelect"
          @toggle-compare="handleToggleCompare"
        />

        <TrendChart
          :active-item="selectedItem"
          :compare-codes="compareCodes"
          :items="items"
          :recent-compare-codes="recentCompareCodes"
          :trend-view="activeTrendViewMeta"
          @update:compare-codes="handleCompareCodesChange"
        />
      </section>
    </template>

    <el-empty v-else description="当前还没有趋势数据，请等待自动拉取或先完成数据生成。" />
  </template>
</template>
