import React, { useState } from 'react';
import { computeUiScale } from '../utils/uiScale';
import type { ThemeMode } from '../theme/theme';

interface FlyoutHelpProps {
  themeMode?: ThemeMode;
  onThemeChange?: (mode: ThemeMode) => void;
  analyzeWhileTyping?: boolean;
  onToggleAnalyzeWhileTyping?: (enabled: boolean) => void;
  engine?: { parser?: string; ml_mode?: string; ml_model_id?: string; ml_reason?: string } | null;
}

export const FlyoutHelp: React.FC<FlyoutHelpProps> = ({
  themeMode = 'dark',
  onThemeChange = () => {},
  analyzeWhileTyping = false,
  onToggleAnalyzeWhileTyping,
  engine,
}) => {
  const [interfaceSize, setInterfaceSize] = useState(() => {
    try {
      return localStorage.getItem('securelex-interface-size') || '1';
    } catch {
      return '1';
    }
  });

  const changeInterfaceSize = (value: string) => {
    setInterfaceSize(value);
    try {
      localStorage.setItem('securelex-interface-size', value);
    } catch {
      /* storage may be blocked */
    }
    const scale = computeUiScale(
      window.innerWidth,
      window.innerHeight,
      Number(value) as 0.85 | 1 | 1.15
    );
    document.documentElement.style.setProperty('--ui-scale', String(scale));
    document.documentElement.style.setProperty('--ui-frame-size', `${100 / scale}%`);
  };

  return (
    <div className="ui6-help">
      <div className="ui6-flyout-section">
        <label htmlFor="securelex-interface-size">INTERFACE SIZE</label>
      </div>
      <div className="ui6-shortcut">
        <span>Scale the workspace</span>
        <select
          id="securelex-interface-size"
          aria-label="Interface size"
          value={interfaceSize}
          onChange={(event) => changeInterfaceSize(event.target.value)}
        >
          <option value="0.85">Compact</option>
          <option value="1">Reference</option>
          <option value="1.15">Large</option>
        </select>
      </div>
      <div className="ui6-flyout-section">APPEARANCE</div>
      <div className="ui6-theme-options" role="radiogroup" aria-label="Appearance">
        {(['dark', 'light', 'system'] as const).map((choice) => (
          <button
            key={choice}
            type="button"
            role="radio"
            aria-checked={themeMode === choice}
            className="ui6-theme-option"
            onClick={() => onThemeChange(choice)}
          >
            {choice[0].toUpperCase() + choice.slice(1)}
          </button>
        ))}
      </div>
      <div className="ui6-flyout-section">ANALYSIS SETTINGS</div>
      <div
        className="ui6-shortcut"
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <span>Analyze while typing</span>
        <input
          type="checkbox"
          id="setting-analyze-typing"
          aria-label="Analyze while typing"
          checked={Boolean(analyzeWhileTyping)}
          onChange={(e) => onToggleAnalyzeWhileTyping?.(e.target.checked)}
          style={{ cursor: 'pointer', width: 16, height: 16 }}
        />
      </div>
      <div className="ui6-flyout-section">KEYBOARD SHORTCUTS</div>
      {[
        ['Ctrl+Enter', 'Analyze'],
        ['Ctrl+.', 'Quick fix'],
        ['F8 / Shift+F8', 'Next / previous problem'],
        ['Ctrl+B', 'Toggle last panel'],
        ['Ctrl+N', 'New file'],
        ['Ctrl+O', 'Open file'],
        ['Ctrl+S', 'Save / download'],
        ['Ctrl+W', 'Close file'],
        ['Ctrl+Shift+P', 'Command palette'],
      ].map(([key, label]) => (
        <div className="ui6-shortcut" key={key}>
          <span>{label}</span>
          <kbd>{key}</kbd>
        </div>
      ))}
      <div className="ui6-flyout-section">TIPS</div>
      <p>Samples open as editable files.</p>
      <p>Click a token row or code range to inspect its evidence.</p>
      <p>Only verified safe fixes can be applied automatically.</p>
      <div className="ui6-flyout-section">ENGINE</div>
      <p>Parser: Python ast; other languages lexer-only</p>
      <p>
        ML status:{' '}
        {engine?.ml_mode === 'on'
          ? `on — model ${engine.ml_model_id || 'id not reported'}`
          : `off — reason: ${engine?.ml_reason || 'not provided by the API'}`}
      </p>
    </div>
  );
};
