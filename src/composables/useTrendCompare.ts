import { computed, ref, watch, type Ref } from 'vue';
import type { TrendItem } from '../types';

export function useTrendCompare(items: Ref<TrendItem[]>, visibleItems: Ref<TrendItem[]>) {
  const selectedCode = ref('');
  const compareCodes = ref<string[]>([]);
  const recentCompareCodes = ref<string[]>([]);

  const selectedItem = computed(() => {
    return visibleItems.value.find((item) => item.code === selectedCode.value) ?? visibleItems.value[0] ?? null;
  });

  watchVisibleItems(visibleItems, selectedCode);
  watchSelectedItem(selectedItem, compareCodes);
  watchItems(items, selectedCode, compareCodes, recentCompareCodes);

  function handleSelect(item: TrendItem) {
    selectedCode.value = item.code;
  }

  function handleToggleCompare(item: TrendItem) {
    if (item.code === selectedCode.value) {
      return;
    }

    if (compareCodes.value.includes(item.code)) {
      compareCodes.value = compareCodes.value.filter((code) => code !== item.code);
      return;
    }

    compareCodes.value = [...compareCodes.value, item.code];
    rememberRecentCompareCode(recentCompareCodes, item.code);
  }

  function handleCompareCodesChange(nextCodes: string[]) {
    const normalizedCodes = normalizeCompareCodes(nextCodes, items.value, selectedCode.value);

    normalizedCodes
      .filter((code) => !compareCodes.value.includes(code))
      .forEach((code) => rememberRecentCompareCode(recentCompareCodes, code));

    compareCodes.value = normalizedCodes;
  }

  return {
    compareCodes,
    handleCompareCodesChange,
    handleSelect,
    handleToggleCompare,
    recentCompareCodes,
    selectedItem,
  };
}

function watchVisibleItems(visibleItems: Ref<TrendItem[]>, selectedCode: Ref<string>) {
  watch(
    visibleItems,
    (nextItems) => {
      if (!nextItems.some((item) => item.code === selectedCode.value)) {
        selectedCode.value = nextItems[0]?.code ?? '';
      }
    },
    { immediate: true },
  );
}

function watchSelectedItem(
  selectedItem: Readonly<Ref<TrendItem | null>>,
  compareCodes: Ref<string[]>,
) {
  watch(
    selectedItem,
    (item) => {
      if (!item) {
        compareCodes.value = [];
        return;
      }

      compareCodes.value = compareCodes.value.filter((code) => code !== item.code);
    },
    { immediate: true },
  );
}

function watchItems(
  items: Ref<TrendItem[]>,
  selectedCode: Ref<string>,
  compareCodes: Ref<string[]>,
  recentCompareCodes: Ref<string[]>,
) {
  watch(items, (nextItems) => {
    const validCodes = new Set(nextItems.map((item) => item.code));

    compareCodes.value = compareCodes.value.filter((code) => validCodes.has(code) && code !== selectedCode.value);
    recentCompareCodes.value = recentCompareCodes.value.filter((code) => validCodes.has(code));
  });
}

function rememberRecentCompareCode(recentCompareCodes: Ref<string[]>, code: string) {
  recentCompareCodes.value = [code, ...recentCompareCodes.value.filter((value) => value !== code)];
}

function normalizeCompareCodes(codes: string[], items: TrendItem[], selectedCode: string): string[] {
  const validCodes = new Set(items.map((item) => item.code));
  const uniqueCodes = new Set<string>();

  return codes.filter((code) => {
    if (!validCodes.has(code) || code === selectedCode || uniqueCodes.has(code)) {
      return false;
    }

    uniqueCodes.add(code);
    return true;
  });
}
