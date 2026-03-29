import { ref, computed } from 'vue';
import type * as echarts from 'echarts';

export interface ChartInteractionOptions {
  enableZoom?: boolean;
  enableTooltip?: boolean;
  enableDataZoom?: boolean;
  tooltipFormatter?: (params: any) => string;
}

export function useChartInteraction(options: ChartInteractionOptions = {}) {
  const {
    enableZoom = true,
    enableTooltip = true,
    enableDataZoom = true,
    tooltipFormatter,
  } = options;

  const zoomLevel = ref(1);
  const isZoomed = computed(() => zoomLevel.value > 1);

  // 缩放图表
  const zoomChart = (chart: echarts.ECharts, level: number) => {
    if (!enableZoom) return;

    zoomLevel.value = level;
    const option = chart.getOption();

    if (option && option.series) {
      // 更新图表缩放
      chart.setOption({
        ...option,
        animation: true,
        animationDuration: 300,
      });
    }
  };

  // 重置缩放
  const resetZoom = (chart: echarts.ECharts) => {
    zoomLevel.value = 1;
    chart.dispatchAction({
      type: 'restore',
    });
  };

  // 配置工具提示
  const getTooltipConfig = () => {
    if (!enableTooltip) return {};

    return {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      formatter: tooltipFormatter || defaultTooltipFormatter,
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: '#777',
      textStyle: {
        color: '#fff',
      },
      transitionDuration: 0.2,
    };
  };

  // 配置数据缩放
  const getDataZoomConfig = () => {
    if (!enableDataZoom) return [];

    return [
      {
        type: 'slider',
        show: true,
        yAxisIndex: [0],
        left: '93%',
        start: 0,
        end: 100,
        textStyle: {
          color: '#8884d8',
        },
      },
      {
        type: 'inside',
        yAxisIndex: [0],
        start: 0,
        end: 100,
      },
    ];
  };

  // 默认工具提示格式化
  const defaultTooltipFormatter = (params: any) => {
    if (!Array.isArray(params)) {
      params = [params];
    }

    let result = `<div style="padding: 8px;">`;
    result += `<p style="margin: 0 0 8px 0; font-weight: 600;">${params[0]?.axisValue || ''}</p>`;

    params.forEach((param: any) => {
      result += `<p style="margin: 4px 0; color: ${param.color};">
        ${param.seriesName}: <strong>${param.value}</strong>
      </p>`;
    });

    result += `</div>`;
    return result;
  };

  // 配置图表交互选项
  const getChartInteractionOptions = () => {
    return {
      tooltip: getTooltipConfig(),
      dataZoom: getDataZoomConfig(),
    };
  };

  return {
    zoomLevel,
    isZoomed,
    zoomChart,
    resetZoom,
    getTooltipConfig,
    getDataZoomConfig,
    getChartInteractionOptions,
  };
}
