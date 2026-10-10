# UI-5 implementation map

The attached phase brief names `docs/ui_reference/securelex_full_feature_ui_mockup.html` and `target.png`. Neither file exists in this checkout, so this map follows the explicit element and token specifications in the brief. Exact mockup DOM selectors, unmapped mockup elements, and visual deltas cannot be measured until those reference files are supplied.

| Brief element | React component / implementation | Data source | Status |
|---|---|---|---|
| SecureLex brand and shield | `TopBar` | Static branding | live now |
| File name pill and file dropdown | `TopBar` | Workspace filename and file actions | live now; pill styling is approximate |
| Language selector | `TopBar` | `/api/languages`, selected workspace language | live now |
| Analyze and Fix all | `TopBar` | Analyzer state and verified safe fixes | live now |
| 34 px Files strip button | `App` `.ui5-strip` | Workspace sidebar state | live now; toggles shared flyout |
| Samples strip button | `App` `.ui5-strip` | Sample catalogue | live now; opens the same existing sidebar flyout |
| Help strip button | `App` `.ui5-strip` | Shortcut dialog | live now |
| Files/Samples flyout content | Existing `Sidebar` in `.ui5-flyout` | Workspace files and samples API | live now; UI-6 can split the flyouts |
| Monaco editor | `EditorPane` | Workspace source and analysis findings | live now |
| Editor syntax colors and selection | `securelex-dark` theme | Monaco model | live now |
| Inline insecure/lexical/selected decorations | `tokens.css` classes | Token/finding ranges | not available in this build, shown hidden; decoration application remains UI-6 |
| Safe / insecure / lexical legend | `App` `.ui5-legend` | Static labels | live now |
| Tokens tab | `FindingPanel` + `TokensPanel` + `model/adapt.ts` | API token and finding ranges | live now |
| Taint path tab | `FindingPanel` and `TaintPath` | Selected finding `taint_path` | live now |
| ML insights tab | `FindingPanel` and `MlInsights` | Engine metadata and insights endpoint | live now |
| Summary tab | `FindingPanel` and `ScoreRing` | API summary, findings, engine metadata | live now |
| Explanation panel | `App` `.ui5-explanation` | Selected finding explanation/message | live now; empty state when no selection |
| Bottom filter bar | `App` `.ui5-filter` | Severity counts from API findings | live now as frame/count chips; full filtering belongs to UI-6 |
| Status bar | `StatusBar` | Engine, cursor, analysis state | live now |
| Responsive stacked panes | `ui5.css` breakpoint at 1100 px | Viewport dimensions | live now; needs visual browser measurement |
| Per-file tabs when multiple files open | No tab row in this phase | Workspace open-file count | not available in this build, shown hidden |
| Exact mockup icon font | `lucide-react` icons | Bundled local package | not available in this build, replaced per brief |
| Parser details for non-Python languages | Engine metadata | API `engine.parser` | not available in this build, shown as `lexer-only` |

## Lexer kinds represented in the saved API samples

The Python, Java, JavaScript, and C samples use real analyzer payloads in `docs/api_samples/`. Those response files currently contain `IDENTIFIER`, `KEYWORD`, `STRING`, `OPERATOR`, `PUNCTUATION`, `PREPROCESSOR`, `WHITESPACE`, and `NEWLINE`. The adapter also maps `IDENT`, `CHAR`, `CHARACTER`, `NUMBER`, `INTEGER`, `FLOAT`, `DELIMITER`, `COMMENT`, `ERROR`, `INDENT`, and `DEDENT`. `FUNCTION`, `NAME`, `CALL`, and `PREPROCESSOR` are accepted for compatibility across plugin revisions. Any kind not listed maps safely to `OTHER`. Vitest checks all four saved response files and the unknown-kind fallback.

## Replaced UI-2/UI-3 structures

- Permanent sidebar column is replaced by the always-visible icon strip and overlay flyout.
- The right-side `Finding` tab is removed from the visible tab strip; finding explanation now lives in the bottom explanation panel, while taint path has its own tab.
- The resizable bottom Problems drawer is removed and replaced by the 38 px finding filter bar.
- The old token inspector's security derivation remains available for legacy detail helpers, while its table rows use the pure UI-5 `TokenRow` adapter and primary-range security rule.
- The editor filename breadcrumb row and minimap control are removed from the editor surface; the top bar retains the active file name.
