<script setup lang="ts">
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

function isPresetDisabled(presetKey: FilterPresetKey): boolean {
  return presetKey !== 'all' && props.presetCounts[presetKey] === 0;
}
</script>

<template>
  <section class="filter-card">
    <div class="filter-view-summary">
      <div>
        <p class="filter-presets__eyebrow">当前联动视图</p>
        <h3 class="filter-presets__title">{{ props.trendView.title }}</h3>
        <p class="filter-presets__tip">{{ props.trendView.description }}</p>
      </div>
      <el-tag effect="plain" round size="large" type="primary">{{ props.trendView.criticalLabel }}</el-tag>
    </div>

    <el-alert :closable="false" class="filter-view-alert" :title="props.trendViewNotice" type="info" />

    <div class="filter-grid">
      <el-input
        :model-value="props.searchTerm"
        clearable
        :placeholder="`输入代码或名称查询当前 ${props.trendView.shortLabel} 视图`"
        size="large"
        @update:model-value="emit('update:searchTerm', $event)"
      />

      <el-radio-group
        :model-value="props.statusFilter"
        class="status-filter"
        size="large"
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
        :placeholder="`选择 ${props.trendView.shortLabel} 数据时间`"
        size="large"
        @update:model-value="emit('update:selectedDataDate', $event)"
      >
        <el-option
          v-for="date in props.availableDates"
          :key="date"
          :label="`${props.trendView.shortLabel}${DATA_TIME_LABEL}：${date}`"
          :value="date"
        />
      </el-select>

      <div class="filter-actions">
        <el-button plain size="large" @click="emit('reset')">重置查询</el-button>
      </div>
    </div>

    <div class="filter-presets">
      <div class="filter-presets__head">
        <div>
          <p class="filter-presets__eyebrow">快捷预设</p>
          <h3 class="filter-presets__title">一键切到当前 {{ props.trendView.shortLabel }} 高频观察视角</h3>
        </div>
        <p class="filter-presets__tip">预设会叠加在当前 {{ props.trendView.shortLabel }} 搜索与状态范围之上。</p>
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
