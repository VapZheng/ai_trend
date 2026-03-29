<script setup lang="ts">
import { computed } from 'vue';
import {
  DATA_TIME_LABEL,
  FILTER_PRESET_OPTIONS,
  SORT_OPTIONS,
  STATUS_OPTIONS,
} from '../constants';
import type { FilterPresetKey, SortKey, StatusFilter, TrendViewMeta } from '../types';

const props = defineProps<{
  availableDates: string[];
  presetCounts: Record<FilterPresetKey, number>;
  searchTerm: string;
  selectedDataDate: string;
  selectedPreset: FilterPresetKey;
  sortKey: SortKey;
  statusFilter: StatusFilter;
  trendView: TrendViewMeta;
  trendViewNotice: string;
}>();

const emit = defineEmits<{
  'update:selectedDataDate': [value: string];
  'update:selectedPreset': [value: FilterPresetKey];
  'update:searchTerm': [value: string];
  'update:sortKey': [value: SortKey];
  'update:statusFilter': [value: StatusFilter];
  reset: [];
}>();

const activeFiltersCount = computed(() => {
  let count = 0;
  if (props.searchTerm) count++;
  if (props.statusFilter !== 'all') count++;
  if (props.sortKey !== 'default') count++;
  if (props.selectedDataDate) count++;
  return count;
});

function isPresetDisabled(presetKey: FilterPresetKey): boolean {
  return presetKey !== 'all' && props.presetCounts[presetKey] === 0;
}
</script>

<template>
  <section class="filter-card">
    <transition name="fade">
      <div v-if="activeFiltersCount > 0" class="active-filters">
        <span class="active-filters__label">已应用 {{ activeFiltersCount }} 个过滤</span>
        <el-button link type="primary" size="small" @click="emit('reset')">清除全部</el-button>
      </div>
    </transition>

    <div class="filter-grid">
      <el-input
        :model-value="props.searchTerm"
        clearable
        :placeholder="`输入代码或名称查询`"
        size="large"
        aria-label="搜索代码或名称"
        @update:model-value="emit('update:searchTerm', $event)"
      />

      <el-radio-group
        :model-value="props.statusFilter"
        class="status-filter"
        size="large"
        aria-label="按状态过滤"
        @update:model-value="emit('update:statusFilter', $event)"
      >
        <el-radio-button
          v-for="option in STATUS_OPTIONS"
          :key="option.value"
          :label="option.value"
        >
          {{ option.label }}
        </el-radio-button>
      </el-radio-group>

      <el-select
        :model-value="props.sortKey"
        placeholder="排序方式"
        size="large"
        aria-label="选择排序方式"
        @update:model-value="emit('update:sortKey', $event)"
      >
        <el-option
          v-for="option in SORT_OPTIONS"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>

      <el-select
        :model-value="props.selectedDataDate"
        class="date-filter"
        :placeholder="`选择数据时间`"
        size="large"
        aria-label="选择数据时间"
        @update:model-value="emit('update:selectedDataDate', $event)"
      >
        <el-option
          v-for="date in props.availableDates"
          :key="date"
          :label="date"
          :value="date"
        />
      </el-select>

      <div class="filter-actions">
        <el-button plain size="large" aria-label="重置所有过滤条件" @click="emit('reset')">重置</el-button>
      </div>
    </div>

    <div class="filter-presets">
      <div class="filter-presets__head">
        <p class="filter-presets__eyebrow">快捷预设</p>
      </div>

      <div class="preset-list">
        <button
          v-for="preset in FILTER_PRESET_OPTIONS"
          :key="preset.value"
          :class="['preset-chip', { 'preset-chip--active': preset.value === props.selectedPreset }]"
          :disabled="isPresetDisabled(preset.value)"
          type="button"
          @click="emit('update:selectedPreset', preset.value)"
        >
          <div class="preset-chip__top">
            <span class="preset-chip__label">{{ preset.label }}</span>
            <el-tag class="preset-chip__count" effect="plain" round size="small" type="info">
              {{ props.presetCounts[preset.value] }}
            </el-tag>
          </div>
          <span class="preset-chip__description">{{ preset.description }}</span>
        </button>
      </div>
    </div>
  </section>
</template>
