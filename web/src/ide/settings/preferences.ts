export interface UserPreferences {
  fontSize: number;
  theme: 'dark' | 'light' | 'system';
  wordWrap: 'on' | 'off';
  minimap: boolean;
  tabSize: number;
  highlightUnicode: boolean;
  autoAnalyze: boolean;
  defaultLanguage: 'cpp' | 'python' | 'java' | 'javascript';
  panelSizes: {
    sidebarWidth: number;
    bottomHeight: number;
    assistantWidth: number;
  };
  sidebarCollapsed: boolean;
  assistantCollapsed: boolean;
  bottomCollapsed: boolean;
  bottomMaximized: boolean;
}

export const DEFAULT_PREFERENCES: UserPreferences = {
  fontSize: 13,
  theme: 'dark',
  wordWrap: 'on',
  minimap: true,
  tabSize: 4,
  highlightUnicode: true,
  autoAnalyze: false,
  defaultLanguage: 'cpp',
  panelSizes: {
    sidebarWidth: 220,
    bottomHeight: 280,
    assistantWidth: 447,
  },
  sidebarCollapsed: false,
  assistantCollapsed: false,
  bottomCollapsed: false,
  bottomMaximized: false,
};

const PREFERENCES_STORAGE_KEY = 'securelex.ide.preferences.v2';
const AUTO_ANALYZE_KEY = 'securelex.ide.autoAnalyze.v1';

export function readPreferences(storage: Pick<Storage, 'getItem'> = localStorage): UserPreferences {
  try {
    const raw = storage.getItem(PREFERENCES_STORAGE_KEY);
    if (!raw) {
      // Check legacy autoAnalyze key
      const legacyAuto = storage.getItem(AUTO_ANALYZE_KEY) === 'true';
      return { ...DEFAULT_PREFERENCES, autoAnalyze: legacyAuto };
    }
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_PREFERENCES,
      ...parsed,
      panelSizes: {
        ...DEFAULT_PREFERENCES.panelSizes,
        ...(parsed.panelSizes || {}),
      },
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function writePreferences(
  prefs: Partial<UserPreferences>,
  storage: Pick<Storage, 'setItem' | 'getItem'> = localStorage
): UserPreferences {
  try {
    const current = readPreferences(storage);
    const updated: UserPreferences = {
      ...current,
      ...prefs,
      panelSizes: {
        ...current.panelSizes,
        ...(prefs.panelSizes || {}),
      },
    };
    storage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(updated));
    if (prefs.autoAnalyze !== undefined) {
      storage.setItem(AUTO_ANALYZE_KEY, String(prefs.autoAnalyze));
    }
    return updated;
  } catch {
    return { ...DEFAULT_PREFERENCES, ...prefs };
  }
}

// Backward-compatible helpers
export function readAutoAnalyze(storage: Pick<Storage, 'getItem'> = localStorage): boolean {
  try {
    return readPreferences(storage).autoAnalyze;
  } catch {
    return false;
  }
}

export function writeAutoAnalyze(
  value: boolean,
  storage: Pick<Storage, 'setItem' | 'getItem'> = localStorage
): void {
  try {
    writePreferences({ autoAnalyze: value }, storage);
  } catch {
    /* Keep setting for session */
  }
}
