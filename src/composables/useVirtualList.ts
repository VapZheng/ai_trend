import { computed, ref } from 'vue';

export interface VirtualListOptions {
  itemHeight: number;
  bufferSize?: number;
  containerHeight?: number;
}

export function useVirtualList<T>(
  items: T[],
  options: VirtualListOptions,
) {
  const { itemHeight, bufferSize = 5, containerHeight = 600 } = options;

  const scrollTop = ref(0);

  // 计算可见范围
  const visibleRange = computed(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop.value / itemHeight) - bufferSize);
    const endIndex = Math.min(
      items.length,
      Math.ceil((scrollTop.value + containerHeight) / itemHeight) + bufferSize,
    );

    return { startIndex, endIndex };
  });

  // 获取可见项
  const visibleItems = computed(() => {
    const { startIndex, endIndex } = visibleRange.value;
    return items.slice(startIndex, endIndex).map((item, index) => ({
      item,
      index: startIndex + index,
    }));
  });

  // 获取偏移量
  const offsetY = computed(() => {
    return visibleRange.value.startIndex * itemHeight;
  });

  // 处理滚动
  const handleScroll = (event: Event) => {
    const target = event.target as HTMLElement;
    scrollTop.value = target.scrollTop;
  };

  // 总高度
  const totalHeight = computed(() => items.length * itemHeight);

  return {
    visibleItems,
    offsetY,
    totalHeight,
    handleScroll,
    visibleRange,
  };
}
