import type {
  FilterPresetOption,
  SortKey,
  StatusFilter,
} from './types';

export const STATUS_OPTIONS: Array<{ label: string; value: StatusFilter }> = [
  { label: '全部', value: 'ALL' },
  { label: 'YES', value: 'YES' },
  { label: 'NO', value: 'NO' },
];

export const SORT_OPTIONS: Array<{ label: string; value: SortKey }> = [
  { label: '趋势强度', value: 'rank-asc' },
  { label: '偏离率', value: 'deviation-desc' },
  { label: '当日涨幅', value: 'change-desc' },
  { label: '状态转变时间', value: 'status-time-desc' },
];

export const FILTER_PRESET_TOP_RANK_LIMIT = 10;

export const FILTER_PRESET_NEAR_CRITICAL_MAX_DEVIATION = 2;

export const FILTER_PRESET_RECENT_SWITCH_DAYS = 5;

export const FILTER_PRESET_OPTIONS: FilterPresetOption[] = [
  {
    value: 'all',
    label: '全部指数',
    description: '不额外收窄当前结果',
  },
  {
    value: 'top-strength',
    label: '趋势前十',
    description: '按趋势强度排名前 10',
  },
  {
    value: 'near-critical',
    label: '临界附近',
    description: '偏离率位于 ±2% 内',
  },
  {
    value: 'recent-switch',
    label: '近 5 日转向',
    description: '状态切换发生在近 5 日',
  },
  {
    value: 'breakout-continued',
    label: '突破延续',
    description: 'YES 且区间涨幅为正',
  },
];

export const DATA_TIME_LABEL = '数据时间';

export const AUTO_REFRESH_INTERVAL_SECONDS = 10;

export const AUTO_REFRESH_CONSTRAINT_NOTE = '默认每 10 秒自动取数；若单次抓取超过 10 秒，下一轮会在当前抓取完成后顺延执行，避免并发写入。';
