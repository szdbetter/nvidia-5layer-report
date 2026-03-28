// Intercept IM API calls by refreshing the page and capturing network requests
const ws = new WebSocket('ws://127.0.0.1:9222/devtools/page/510291CC21A42B2154BDF96120E81430');
const captured = [];
let msgId = 0;

function send(method, params) {
  msgId++;
  ws.send(JSON.stringify({ id: msgId, method, params }));
  return msgId;
}

ws.onopen = () => {
  // Enable network interception
  send('Network.enable', {});
  
  // After 2 sec, trigger a page navigation to force IM API calls
  setTimeout(() => {
    send('Page.navigate', { url: 'https://www.goofish.com/im' });
  }, 500);
  
  // After 12 sec, inject JS to call IM via XHR (bypasses CORS differently)
  setTimeout(() => {
    send('Runtime.evaluate', {
      expression: `(async () => {
        // Use XMLHttpRequest instead of fetch - might bypass CORS
        return await new Promise((resolve) => {
          const xhr = new XMLHttpRequest();
          xhr.withCredentials = true;
          xhr.open('GET', 'https://www.goofish.com/api/mtop/social/im/queryConversationList.htm', true);
          xhr.onload = () => resolve(xhr.status + ':' + xhr.responseText.substring(0, 500));
          xhr.onerror = () => resolve('XHR ERR: ' + xhr.status);
          xhr.send();
        });
      })()`,
      awaitPromise: true
    });
  }, 5000);
};

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  
  // Capture network responses
  if (msg.method === 'Network.responseReceived') {
    const url = msg.params.response.url;
    if (url.includes('mtop') || url.includes('/im') || url.includes('xtalk') || url.includes('idle')) {
      captured.push({ url, status: msg.params.response.status });
      console.error('CAPTURED URL:', url, msg.params.response.status);
    }
  }
  
  if (msg.method === 'Network.loadingFinished') {
    // Try to get body for captured requests
  }
  
  // Print evaluate results
  if (msg.id && msg.result && msg.result.result) {
    console.log('RESULT_' + msg.id + ':', JSON.stringify(msg.result.result));
  }
};

setTimeout(() => {
  console.log('CAPTURED_URLS:', JSON.stringify(captured));
  process.exit(0);
}, 15000);
