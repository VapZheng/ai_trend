export type TrendStatus = 'YES' | 'NO';

export type AppPageKey = 'dashboard' | 'sector-rotation';

export type StatusFilter = TrendStatus | 'ALL';

export type TrendViewKey = 'ma5' | 'ma20';

export type FilterPresetKey =
  | 'all'
  | 'top-strength'
  | 'near-critical'
  | 'recent-switch'
  | 'breakout-continued';

export type SortKey =
  | 'rank-asc'
  | 'deviation-desc'
  | 'change-desc'
  | 'status-time-desc';

export interface FilterPresetOption {
  value: FilterPresetKey;
  label: string;
  description: string;
}

export interface TrendViewOption {
  shortLabel: string;
  criticalLabel: string;
  label: string;
  value: TrendViewKey;
}

export interface TrendViewMeta {
  criticalLabel: string;
  description: string;
  label: string;
  shortLabel: string;
  title: string;
  value: TrendViewKey;
  windowSize: number;
}

export interface TrendHistoryPoint {
  date: string;
  close: number;
  critical: number;
  status: TrendStatus;
}

export interface TrendItem {
  rank: number;
  code: string;
  name: string;
  status: TrendStatus;
  dayChangePct: number;
  close: number;
  critical: number;
  deviationRate: number;
  statusChangedAt: string;
  intervalGainPct: number;
  trendStrength: string;
  history: TrendHistoryPoint[];
}

export interface TrendDatasetView {
  key: TrendViewKey;
  label: string;
  latestDataDate: string;
  maWindow: number;
  items: TrendItem[];
}

export interface TrendDataset {
  latestDataDate: string;
  updatedAt: string;
  defaultViewKey: TrendViewKey;
  viewOrder: TrendViewKey[];
  views: Record<TrendViewKey, TrendDatasetView>;
}

export interface SectorRotationTarget {
  code: string;
  name: string;
  quoteId: string;
  securityTypeName: string;
}

export interface AutoRefreshState {
  intervalSeconds: number;
  nextRunAt: string | null;
}

export interface RefreshRun {
  source: string;
  status: string;
  startedAt: string;
  finishedAt: string | null;
  errorMessage: string | null;
}

export interface DashboardResponse {
  autoRefresh: AutoRefreshState;
  dataset: TrendDataset | null;
  lastRun: RefreshRun | null;
  isRefreshing: boolean;
}

export interface SectorRotationResponse {
  dataset: TrendDataset | null;
  isRefreshing: boolean;
  lastRun: RefreshRun | null;
  targets: SectorRotationTarget[];
}
