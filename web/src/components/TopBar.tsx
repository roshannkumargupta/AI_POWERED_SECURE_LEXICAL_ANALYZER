import React from 'react';
import {
  Shield,
  Play,
  Wand2,
  Download,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import { LanguageInfo, SampleItem } from '../api/client';

interface TopBarProps {
  language: string;
  languages: LanguageInfo[];
  onChangeLanguage: (lang: string) => void;
  isAnalyzing: boolean;
  onAnalyze: () => void;
  onFixAll: () => void;
  onDownload: () => void;
  samples: SampleItem[];
  onSelectSample: (sample: SampleItem) => void;
  healthScore: number | null;
}

export const TopBar: React.FC<TopBarProps> = ({
  language,
  languages,
  onChangeLanguage,
  isAnalyzing,
  onAnalyze,
  onFixAll,
  onDownload,
  samples,
  onSelectSample,
  healthScore,
}) => {
  const [isSampleMenuOpen, setIsSampleMenuOpen] = React.useState(false);
  const sampleMenuRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sampleMenuRef.current && !sampleMenuRef.current.contains(e.target as Node)) {
        setIsSampleMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const scoreColor =
    healthScore === null
      ? 'var(--muted)'
      : healthScore >= 80
      ? 'var(--success)'
      : healthScore >= 50
      ? 'var(--medium)'
      : 'var(--critical)';

  return (
    <header style={containerStyle}>
      {/* Brand Identity */}
      <div style={brandGroupStyle}>
        <div style={logoIconStyle}>
          <Shield size={18} color="#FFFFFF" />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span style={brandTitleStyle}>SecureLex</span>
          <span style={brandBadgeStyle}>IDE</span>
        </div>
      </div>

      {/* Middle Controls */}
      <div style={middleControlsStyle}>
        {/* Language Selector */}
        <div style={selectorWrapperStyle}>
          <label htmlFor="lang-select" style={visuallyHiddenStyle}>Language</label>
          <select
            id="lang-select"
            value={language}
            onChange={(e) => onChangeLanguage(e.target.value)}
            style={selectStyle}
            aria-label="Select target programming language"
          >
            <option value="auto">Auto-Detect</option>
            {languages.map((l) => (
              <option key={l.id} value={l.id}>
                {l.display_name}
              </option>
            ))}
          </select>
          <ChevronDown size={12} color="var(--muted)" style={selectArrowStyle} />
        </div>

        {/* Samples Menu Dropdown */}
        <div style={{ position: 'relative' }} ref={sampleMenuRef}>
          <button
            style={secondaryButtonStyle}
            onClick={() => setIsSampleMenuOpen(!isSampleMenuOpen)}
            aria-label="Open code samples menu"
          >
            <span>Samples</span>
            <ChevronDown size={12} />
          </button>

          {isSampleMenuOpen && (
            <div style={dropdownMenuStyle}>
              <div style={dropdownHeaderStyle}>Select Code Preset</div>
              {samples.map((s) => (
                <button
                  key={s.id}
                  style={dropdownItemStyle}
                  onClick={() => {
                    onSelectSample(s);
                    setIsSampleMenuOpen(false);
                  }}
                >
                  <span style={dropdownItemTitleStyle}>{s.title}</span>
                  <span style={dropdownItemSubStyle}>{s.filename}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Action Buttons */}
      <div style={rightActionsStyle}>
        {healthScore !== null && (
          <div style={{ ...scoreBadgeStyle, borderColor: `${scoreColor}40`, color: scoreColor }}>
            <span style={{ fontSize: '10px', color: 'var(--muted)' }}>SCORE</span>
            <span style={{ fontWeight: 700, fontFamily: 'var(--font-code)' }}>{healthScore}</span>
          </div>
        )}

        {/* Analyze Button */}
        <button
          style={primaryButtonStyle}
          onClick={onAnalyze}
          disabled={isAnalyzing}
          title="Analyze Code (Ctrl+Enter)"
          aria-label="Analyze Code"
        >
          {isAnalyzing ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Play size={14} fill="currentColor" />
          )}
          <span>Analyze</span>
          <kbd style={kbdStyle}>Ctrl+↵</kbd>
        </button>

        {/* Fix All Button */}
        <button
          style={fixAllButtonStyle}
          onClick={onFixAll}
          title="Apply All Safe & Verified Fixes Iteratively"
          aria-label="Fix All Safe Issues"
        >
          <Wand2 size={14} />
          <span>Fix all ✓</span>
        </button>

        {/* Download Button */}
        <button
          style={iconButtonStyle}
          onClick={onDownload}
          title="Download Source Code (Ctrl+S)"
          aria-label="Download Source Code"
        >
          <Download size={15} />
        </button>
      </div>
    </header>
  );
};

const containerStyle: React.CSSProperties = {
  height: '48px',
  minHeight: '48px',
  maxHeight: '48px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 16px',
  backgroundColor: 'var(--panel)',
  borderBottom: '1px solid var(--border)',
  zIndex: 30,
};

const brandGroupStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

const logoIconStyle: React.CSSProperties = {
  width: '28px',
  height: '28px',
  borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--accent)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  boxShadow: '0 2px 8px rgba(79, 140, 255, 0.4)',
};

const brandTitleStyle: React.CSSProperties = {
  fontSize: '15px',
  fontWeight: 700,
  letterSpacing: '-0.3px',
  color: 'var(--text)',
};

const brandBadgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 700,
  padding: '1px 5px',
  backgroundColor: 'var(--panel-2)',
  color: 'var(--accent)',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
};

const middleControlsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
};

const selectorWrapperStyle: React.CSSProperties = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
};

const visuallyHiddenStyle: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  border: 0,
};

const selectStyle: React.CSSProperties = {
  appearance: 'none',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  padding: '5px 28px 5px 10px',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
  outline: 'none',
};

const selectArrowStyle: React.CSSProperties = {
  position: 'absolute',
  right: '8px',
  pointerEvents: 'none',
};

const secondaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '5px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text-secondary)',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
};

const dropdownMenuStyle: React.CSSProperties = {
  position: 'absolute',
  top: 'calc(100% + 6px)',
  left: 0,
  width: '240px',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
  display: 'flex',
  flexDirection: 'column',
  padding: '6px',
  zIndex: 100,
};

const dropdownHeaderStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--muted)',
  textTransform: 'uppercase',
  padding: '6px 8px',
};

const dropdownItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start',
  padding: '6px 8px',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
  textAlign: 'left',
  transition: 'background-color var(--transition-fast)',
};

const dropdownItemTitleStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text)',
};

const dropdownItemSubStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
};

const rightActionsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

const scoreBadgeStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '4px 10px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
};

const primaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'var(--accent)',
  color: '#FFFFFF',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: '0 2px 6px rgba(79, 140, 255, 0.3)',
};

const fixAllButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'rgba(61, 220, 151, 0.15)',
  border: '1px solid rgba(61, 220, 151, 0.4)',
  color: 'var(--success)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
};

const iconButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '6px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  cursor: 'pointer',
};

const kbdStyle: React.CSSProperties = {
  fontSize: '10px',
  opacity: 0.8,
  backgroundColor: 'rgba(0, 0, 0, 0.25)',
  padding: '1px 4px',
  borderRadius: '2px',
  marginLeft: '2px',
};
