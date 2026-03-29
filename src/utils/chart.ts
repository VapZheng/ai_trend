import type { EChartsOption, SeriesOption } from 'echarts';
import type { TrendHistoryPoint, TrendItem } from '../types';

const CHART_COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#7c3aed', '#0f766e'];

export function buildComparisonOption(items: TrendItem[], criticalLabel: string): EChartsOption {
  return {
    color: CHART_COLORS,
    grid: { left: 24, right: 24, top: 56, bottom: 24, containLabel: true },
    legend: { top: 8 },
    tooltip: { trigger: 'axis', valueFormatter: (value) => `${Number(value).toFixed(2)}%` },
    xAxis: { type: 'category', data: getAxisDates(items) },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { formatter: '{value}%' },
      name: `偏离率（相对${criticalLabel}）`,
    },
    series: items.map(createDeviationSeries),
  };
}

export function getDeviationRate(point: TrendHistoryPoint): number {
  return Number((((point.close - point.critical) / point.critical) * 100).toFixed(2));
}

function getAxisDates(items: TrendItem[]): string[] {
  return items[0]?.history.map((point) => point.date) ?? [];
}

function createDeviationSeries(item: TrendItem): SeriesOption {
  return {
    name: item.name,
    type: 'line',
    smooth: true,
    symbolSize: 7,
    emphasis: { focus: 'series' },
    data: item.history.map(getDeviationRate),
  };
}
