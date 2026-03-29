import type { TrendItem } from '../types';

export function normalizeCompareCodes(
  codes: readonly string[],
  items: readonly TrendItem[],
  selectedCode: string,
): string[] {
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
