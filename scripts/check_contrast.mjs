import fs from 'node:fs';

const VIEWPORTS = [
  { width: 1280, height: 720 },
  { width: 1366, height: 768 },
  { width: 1536, height: 864 },
  { width: 1536, height: 1022 },
  { width: 1920, height: 1080 },
];

async function check() {
  const res = await fetch('http://127.0.0.1:9222/json');
  const targets = await res.json();
  const page = targets.find((t) => t.url.includes('5173'));
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let msgId = 1;
  function send(method, params = {}) {
    return new Promise((resolve) => {
      const id = msgId++;
      ws.addEventListener('message', function handler(evt) {
        const data = JSON.parse(evt.data);
        if (data.id === id) {
          ws.removeEventListener('message', handler);
          resolve(data.result);
        }
      });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  const diagCode = fs.readFileSync('web/qa/diagnostics.js', 'utf-8');
  await send('Runtime.evaluate', { expression: diagCode });

  const report = { dark: {}, light: {} };

  for (const theme of ['dark', 'light']) {
    await send('Runtime.evaluate', { expression: `document.documentElement.dataset.theme = '${theme}';` });
    await new Promise(r => setTimeout(r, 200));
    for (const vp of VIEWPORTS) {
      await send('Emulation.setDeviceMetricsOverride', { width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: false });
      await new Promise(r => setTimeout(r, 100));
      const qa = await send('Runtime.evaluate', { expression: 'window.slQA()', returnByValue: true });
      console.log(`${theme} @ ${vp.width}x${vp.height}: ${qa.result.value?.verdict} (lowContrast: ${qa.result.value?.lowContrast?.length})`);
    }
  }

  ws.close();
}
check();
