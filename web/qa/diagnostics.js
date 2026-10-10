// UI-7 read-only browser diagnostics. Load the app and call window.slQA().
// This script only reads computed styles, dimensions and hit targets.
(() => {
  const rgb = (value) => {
    const match = value.match(/rgba?\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)(?:,\s*([\d.]+))?\)/i);
    return match ? [Number(match[1]), Number(match[2]), Number(match[3]), match[4] === undefined ? 1 : Number(match[4])] : null;
  };
  const luminance = ([r, g, b]) => {
    const channel = (part) => { const value = part / 255; return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  };
  const contrast = (foreground, background) => {
    const a = luminance(foreground); const b = luminance(background);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };
  const backgroundFor = (element) => {
    // Composite translucent layers over the nearest opaque ancestor. Treating
    // rgba highlight tints as opaque produced false contrast failures.
    const isLight = document.documentElement.dataset.theme === 'light';
    let composed = isLight ? [255, 255, 255, 1] : [26, 26, 25, 1];
    const ancestors = [];
    for (let node = element; node && node !== document.documentElement; node = node.parentElement) ancestors.push(node);
    for (const node of ancestors.reverse()) {
      const color = rgb(getComputedStyle(node).backgroundColor);
      if (!color || color[3] <= 0) continue;
      const alpha = color[3];
      composed = [0, 1, 2].map((i) => Math.round(color[i] * alpha + composed[i] * (1 - alpha))).concat(1);
    }
    return composed;
  };
  const nameOf = (element) => {
    const label = element.getAttribute('aria-label') || element.getAttribute('title') || element.textContent?.trim().replace(/\s+/g, ' ').slice(0, 55);
    return `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ''}${typeof element.className === 'string' && element.className ? `.${element.className.trim().split(/\s+/).slice(0, 2).join('.')}` : ''}${label ? ` [${label}]` : ''}`;
  };
  window.slQA = () => {
    const lowContrast = []; const blackOnDark = []; const nativeControls = [];
    const textNodes = document.querySelectorAll('body *');
    for (const element of textNodes) {
      if (!element.getClientRects().length || !element.textContent?.trim()) continue;
      const style = getComputedStyle(element); const foreground = rgb(style.color);
      if (!foreground || foreground[3] < 0.95) continue;
      const background = backgroundFor(element); const ratio = contrast(foreground, background);
      const fontSize = parseFloat(style.fontSize);
      if (foreground[0] < 2 && foreground[1] < 2 && foreground[2] < 2 && luminance(background) < 0.3) blackOnDark.push({ element: nameOf(element), color: style.color, background: `rgb(${background.slice(0, 3).join(', ')})` });
      if (ratio < 4.5 && fontSize >= 10 && lowContrast.length < 120) lowContrast.push({ element: nameOf(element), color: style.color, background: `rgb(${background.slice(0, 3).join(', ')})`, ratio: Math.round(ratio * 100) / 100, fontSize: style.fontSize });
    }
    for (const element of document.querySelectorAll('button,input,select,textarea,option')) {
      if (!element.getClientRects().length) continue;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      if (rect.width <= 1 || rect.height <= 1 || (element.matches('textarea') && element.closest('.monaco-editor'))) continue;
      const isLight = document.documentElement.dataset.theme === 'light';
      const rootScheme = getComputedStyle(document.documentElement).colorScheme;
      const validScheme = isLight
        ? (style.colorScheme.includes('light') || rootScheme.includes('light'))
        : (style.colorScheme.includes('dark') || rootScheme.includes('dark'));
      const controlColor = rgb(style.color);
      if (!validScheme || (!isLight && controlColor && controlColor[0] < 2 && controlColor[1] < 2 && controlColor[2] < 2)) nativeControls.push({ element: nameOf(element), color: style.color, colorScheme: style.colorScheme, rootColorScheme: rootScheme });
    }
    const scrollBugs = []; const scrollAreas = [];
    for (const element of document.querySelectorAll('body *')) {
      if (!element.getClientRects().length) continue;
      const style = getComputedStyle(element); const rect = element.getBoundingClientRect();
      const scrollableY = /(auto|scroll)/.test(style.overflowY) && element.scrollHeight > element.clientHeight + 2;
      const scrollableX = /(auto|scroll)/.test(style.overflowX) && element.scrollWidth > element.clientWidth + 2;
      if (scrollableY || scrollableX) {
        const x = Math.max(0, Math.min(innerWidth - 1, rect.left + Math.min(rect.width / 2, 20)));
        const y = Math.max(0, Math.min(innerHeight - 1, rect.top + Math.min(rect.height / 2, 20)));
        const hit = document.elementFromPoint(x, y);
        const covered = Boolean(hit && !element.contains(hit) && hit !== element);
        const record = { element: nameOf(element), overflow: `${style.overflowX}/${style.overflowY}`, client: `${element.clientWidth}x${element.clientHeight}`, scroll: `${element.scrollWidth}x${element.scrollHeight}`, covered };
        scrollAreas.push(record);
        if (covered) scrollBugs.push({ ...record, issue: 'covered scroll area', hit: hit ? nameOf(hit) : null });
      }
      const intentionallyHidden = element.matches('label,.monaco-editor textarea.inputarea') || rect.width <= 1 || rect.height <= 1;
      if (!intentionallyHidden && style.overflowY === 'hidden' && element.scrollHeight > element.clientHeight + 8 && !element.querySelector('[style*="overflow"]')) scrollBugs.push({ element: nameOf(element), issue: 'content clipped by overflow:hidden', clientHeight: element.clientHeight, scrollHeight: element.scrollHeight });
    }
    const pageScroll = { vertical: document.documentElement.scrollHeight > innerHeight + 2, horizontal: document.documentElement.scrollWidth > innerWidth + 2, document: `${document.documentElement.scrollWidth}x${document.documentElement.scrollHeight}`, viewport: `${innerWidth}x${innerHeight}` };
    const result = { viewport: { width: innerWidth, height: innerHeight }, colorScheme: getComputedStyle(document.documentElement).colorScheme, counts: { lowContrast: lowContrast.length, blackOnDark: blackOnDark.length, nativeControls: nativeControls.length, scrollBugs: scrollBugs.length, scrollAreas: scrollAreas.length, pageScroll: Number(pageScroll.vertical || pageScroll.horizontal) }, lowContrast, blackOnDark, nativeControls, scrollBugs, scrollAreas, pageScroll };
    result.verdict = result.counts.lowContrast === 0 && result.counts.blackOnDark === 0 && result.counts.nativeControls === 0 && result.counts.scrollBugs === 0 && !pageScroll.vertical && !pageScroll.horizontal ? 'PASS' : 'FAIL';
    return result;
  };
  const report = () => console.info(`SLQA_JSON:${JSON.stringify(window.slQA())}`);
  window.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.shiftKey && event.altKey && event.key === 'F9') {
      event.preventDefault();
      report();
    }
  });
  if (new URLSearchParams(location.search).has('ui7qa')) window.setTimeout(report, 1200);
})();
