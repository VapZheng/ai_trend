import type { TrendItem } from '../types';
import { formatPercent } from './formatters';

interface BuildMarketOverviewOptions {
  items: readonly TrendItem[];
  criticalLabel: string;
}

interface StrongestItemOverview {
  code: string;
  deviationRate: number;
  name: string;
  trendStrength: string;
}

export interface MarketOverview {
  averageDeviation: number;
  conclusionNote: string;
  conclusionTitle: string;
  noCount: number;
  noRatio: number;
  strongestItem: StrongestItemOverview | null;
  temperatureLabel: string;
  totalCount: number;
  yesCount: number;
  yesRatio: number;
}

export function buildMarketOverview(options: BuildMarketOverviewOptions): MarketOverview {
  const { criticalLabel, items } = options;
  const totalCount = items.length;
  const yesCount = items.filter((item) => item.status === 'YES').length;
  const noCount = totalCount - yesCount;
  const averageDeviation = getAverageDeviation(items);
  const strongestItem = getStrongestItem(items);

  return {
    averageDeviation,
    conclusionNote: getConclusionNote(totalCount, yesCount, noCount, averageDeviation, strongestItem, criticalLabel),
    conclusionTitle: getConclusionTitle(totalCount, yesCount, noCount, criticalLabel),
    noCount,
    noRatio: getRatio(noCount, totalCount),
    strongestItem,
    temperatureLabel: getTemperatureLabel(averageDeviation, criticalLabel),
    totalCount,
    yesCount,
    yesRatio: getRatio(yesCount, totalCount),
  };
}

export function getRunSourceLabel(source?: string | null): string {
  if (!source) {
    return '--';
  }

  if (source === 'manual') {
    return '手动触发';
  }

  if (source === 'scheduler') {
    return '自动取数';
  }

  if (source === 'cli') {
    return '命令行';
  }

  return source;
}

export function getRunStatusLabel(status?: string | null): string {
  if (!status) {
    return '--';
  }

  return status === 'success' ? '成功' : '失败';
}

function getAverageDeviation(items: readonly TrendItem[]): number {
  if (items.length === 0) {
    return 0;
  }

  const totalDeviation = items.reduce((sum, item) => sum + item.deviationRate, 0);
  return totalDeviation / items.length;
}

function getStrongestItem(items: readonly TrendItem[]): StrongestItemOverview | null {
  const strongestItem = items.reduce<TrendItem | null>((currentStrongest, item) => {
    if (!currentStrongest || item.deviationRate > currentStrongest.deviationRate) {
      return item;
    }

    return currentStrongest;
  }, null);

  if (!strongestItem) {
    return null;
  }

  return {
    code: strongestItem.code,
    deviationRate: strongestItem.deviationRate,
    name: strongestItem.name,
    trendStrength: strongestItem.trendStrength,
  };
}

function getRatio(count: number, totalCount: number): number {
  if (totalCount === 0) {
    return 0;
  }

  return count / totalCount;
}

function getConclusionTitle(
  totalCount: number,
  yesCount: number,
  noCount: number,
  criticalLabel: string,
): string {
  if (totalCount === 0) {
    return '当前筛选下暂无市场结论';
  }

  if (yesCount === totalCount) {
    return `全线站上 ${criticalLabel}，市场强势`;
  }

  if (noCount === totalCount) {
    return `全线跌破 ${criticalLabel}，市场承压`;
  }

  if (yesCount === noCount) {
    return `${criticalLabel} 视角下多空均衡，市场分化`;
  }

  return yesCount > noCount ? `${criticalLabel} 视角 YES 占优，市场偏强` : `${criticalLabel} 视角 NO 占优，市场承压`;
}

function getTemperatureLabel(averageDeviation: number, criticalLabel: string): string {
  if (averageDeviation > 0) {
    return `相对 ${criticalLabel} 整体温度偏热`;
  }

  if (averageDeviation < 0) {
    return `相对 ${criticalLabel} 整体温度偏冷`;
  }

  return `相对 ${criticalLabel} 整体温度中性`;
}

function getConclusionNote(
  totalCount: number,
  yesCount: number,
  noCount: number,
  averageDeviation: number,
  strongestItem: StrongestItemOverview | null,
  criticalLabel: string,
): string {
  if (totalCount === 0) {
    return '当前筛选范围内没有可展示的指数，请调整筛选条件后再看市场结论。';
  }

  const strongestLabel = strongestItem
    ? `最强标的是 ${strongestItem.name}（${strongestItem.code}）。`
    : '当前没有可用的最强标的信息。';

  return `${totalCount} 个指数中 ${yesCount} 个 YES、${noCount} 个 NO，平均偏离率相对 ${criticalLabel} 为 ${formatPercent(averageDeviation)}，${strongestLabel}`;
}
