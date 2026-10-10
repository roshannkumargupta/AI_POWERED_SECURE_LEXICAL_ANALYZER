import fs from 'node:fs';

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

  const qa = await send('Runtime.evaluate', {
    expression: 'document.documentElement.dataset.theme = "dark"; window.slQA()',
    returnByValue: true
  });
  console.log('verdict:', qa.result.value?.verdict);
  console.log('blackOnDark:', qa.result.value?.blackOnDark);
  console.log('lowContrast count:', qa.result.value?.lowContrast?.length);
  if (qa.result.value?.lowContrast?.length) {
    console.log('lowContrast elements:', qa.result.value.lowContrast.slice(0, 5));
  }
  console.log('nativeControls:', qa.result.value?.nativeControls);
  console.log('scrollBugs:', qa.result.value?.scrollBugs);
  ws.close();
}
check();
