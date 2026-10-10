// Browser-side UI-7 metric reader. Enable with ?ui7metrics=1 and inspect the
// SLUI_METRICS console output at 1280x720, 1366x768 and 1536x1022.
// The intended ref_metrics.json is missing; values below are only those stated
// in prompt section C3 and are explicitly marked as prompt-derived.
const expected = {
  topbar: { height: 49 }, select: { width: 110, height: 26 },
  analyze: { height: 32 }, fixall: { height: 32 }, strip: { width: 34 },
  tabs: { height: 35 }, legend: { height: 24 }, filter: { height: 31 }, status: { height: 35 },
};
const selectors = {
  topbar: '[data-qa="topbar"]', select: '[data-qa="select-language"]',
  analyze: '[data-qa="btn-analyze"]', fixall: '[data-qa="btn-fixall"]',
  strip: '[data-qa="strip"]', tabs: '[data-qa="tabs"]', legend: '[data-qa="legend-row"]',
  filter: '[data-qa="filter-row"]', status: '[data-qa="status"]',
};
export function measureUiReference() {
  const width = innerWidth;
  const height = innerHeight;
  const baseScale = Math.max(1, Math.min(2, width / 768, height / 480));
  const scale = Number(getComputedStyle(document.documentElement).getPropertyValue('--ui-scale')) || baseScale;
  const rows = [];
  for (const [name, selector] of Object.entries(selectors)) {
    const element = document.querySelector(selector);
    if (!element) { rows.push({ name, status: 'MISSING' }); continue; }
    const rect = element.getBoundingClientRect();
    for (const [dimension, actualPx] of [['width', rect.width], ['height', rect.height]]) {
      if (expected[name][dimension] === undefined) continue;
      const actualDu = actualPx / scale;
      const targetDu = expected[name][dimension];
      const errorPercent = Math.abs(actualDu - targetDu) / targetDu * 100;
      rows.push({ name, dimension, targetDu, actualDu: Math.round(actualDu * 10) / 10, errorPercent: Math.round(errorPercent * 10) / 10, status: errorPercent <= 6 ? 'PASS' : 'FAIL' });
    }
  }
  return { source: 'prompt C3 fallback; not extracted from absent ref_metrics.json', viewport: `${width}x${height}`, baseScale, rows, verdict: rows.every((row) => row.status === 'PASS') ? 'PASS' : 'FAIL' };
}
if (new URLSearchParams(location.search).has('ui7metrics')) console.info(`SLUI_METRICS:${JSON.stringify(measureUiReference())}`);
