import { mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Run after installing Playwright and supplying the UI-5 reference HTML.
// Usage: node web/e2e/compare_reference.mjs [app-url]
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const reference = resolve(root, 'docs/ui_reference/securelex_full_feature_ui_mockup.html');
const screenshots = resolve(root, 'docs/screenshots/after_ui5');
let playwright;
try { playwright = await import('playwright'); }
catch { console.error('Playwright is not installed. Install it offline, then rerun this measurement script.'); process.exitCode = 2; }
if (!existsSync(reference)) { console.error(`Missing visual reference: ${reference}`); process.exitCode = 2; }
if (playwright && existsSync(reference)) {
  const { chromium } = playwright;
  const browser = await chromium.launch({ headless: true });
  const app = await browser.newPage();
  const mock = await browser.newPage({ colorScheme: 'dark' });
  const base = process.argv[2] || 'http://127.0.0.1:5173/';
  const report = [];
  await mkdir(screenshots, { recursive: true });
  for (const [width,height] of [[1536,1022],[1280,720]]) {
    await app.setViewportSize({width,height}); await mock.setViewportSize({width,height});
    await app.goto(base); await mock.goto(pathToFileURL(reference).href);
    const inspect = async page => page.evaluate(() => {
      const pick = selector => {const e=document.querySelector(selector);if(!e)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {height:r.height,width:r.width,fontSize:s.fontSize,padding:s.padding,background:s.backgroundColor,color:s.color};};
      return {bar:pick('.bar,header'),strip:pick('.strip,.ui5-strip'),tabs:pick('.tabs'),tab:pick('.tab'),table:pick('table'),badge:pick('.b,.ui5-badge'),horizontalOverflow:document.documentElement.scrollWidth>innerWidth};
    });
    const appMetrics=await inspect(app), referenceMetrics=await inspect(mock);
    report.push({viewport:`${width}x${height}`,reference:referenceMetrics,app:appMetrics});
    if(width===1536)await app.screenshot({path:resolve(screenshots,'app-1536x1022.png'),fullPage:true});
    if(width===1280)await app.screenshot({path:resolve(screenshots,'app-1280x720.png'),fullPage:true});
    if(width===1536)await mock.screenshot({path:resolve(screenshots,'reference-1536x1022.png'),fullPage:true});
  }
  const deltas=[];
  for(const row of report){for(const key of ['bar','strip','tabs','tab','table','badge']){const a=row.app[key],b=row.reference[key];if(!a||!b){deltas.push(`${row.viewport} ${key}: missing ${!a?'app':'reference'} element`);continue;}for(const prop of ['height','width'])if(Math.abs(a[prop]-b[prop])>2)deltas.push(`${row.viewport} ${key}.${prop}: app ${a[prop]}px, reference ${b[prop]}px`);for(const prop of ['fontSize','padding','background','color'])if(a[prop]!==b[prop])deltas.push(`${row.viewport} ${key}.${prop}: app ${a[prop]}, reference ${b[prop]}`);}}
  const appImage=await readFile(resolve(screenshots,'app-1536x1022.png'));
  const refImage=await readFile(resolve(screenshots,'reference-1536x1022.png'));
  const compare=await browser.newPage({viewport:{width:1536,height:1022}});
  await compare.setContent(`<body style="margin:0;background:#151515;color:#eee;font:12px system-ui"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><figure><figcaption>Reference</figcaption><img style="width:100%" src="data:image/png;base64,${refImage.toString('base64')}"></figure><figure><figcaption>UI-5</figcaption><img style="width:100%" src="data:image/png;base64,${appImage.toString('base64')}"></figure></div></body>`);
  await compare.screenshot({path:resolve(screenshots,'compare.png'),fullPage:true});
  console.log(JSON.stringify({measurements:report,differencesOverTwoPxOrStyle:deltas},null,2)); await browser.close();
}
