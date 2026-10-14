const AUTO_ANALYZE_KEY = 'securelex.ide.autoAnalyze.v1';
export function readAutoAnalyze(storage: Pick<Storage, 'getItem'> = localStorage): boolean {
  try {
    return storage.getItem(AUTO_ANALYZE_KEY) === 'true';
  } catch {
    return false;
  }
}
export function writeAutoAnalyze(
  value: boolean,
  storage: Pick<Storage, 'setItem'> = localStorage
): void {
  try {
    storage.setItem(AUTO_ANALYZE_KEY, String(value));
  } catch {
    /* Keep the setting for this session. */
  }
}
