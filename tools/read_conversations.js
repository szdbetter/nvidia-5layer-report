const WSUrl = 'ws://127.0.0.1:9222/devtools/page/510291CC21A42B2154BDF96120E81430';
const ws = new WebSocket(WSUrl);

ws.onopen = () => {
  ws.send(JSON.stringify({
    id: 1,
    method: 'Runtime.evaluate',
    params: {
      returnByValue: true,
      expression: `(() => {
        const items = [];
        const convEls = document.querySelectorAll('[class*=session],[class*=conv],[class*=chat-item],[class*=msg-item]');
        convEls.forEach(el => {
          const nameEl = el.querySelector('[class*=name],[class*=nick],[class*=title]');
          const msgEl = el.querySelector('[class*=msg],[class*=content],[class*=text],[class*=desc]');
          const timeEl = el.querySelector('[class*=time],[class*=date]');
          items.push({
            name: nameEl ? nameEl.innerText.trim().substring(0,50) : '',
            lastMsg: msgEl ? msgEl.innerText.trim().substring(0,150) : '',
            time: timeEl ? timeEl.innerText.trim() : '',
            raw: el.innerText.substring(0,200)
          });
        });
        return JSON.stringify({total: convEls.length, items: items.slice(0,10)});
      })()`
    }
  }));
};

ws.onmessage = (e) => {
  const d = JSON.parse(e.data);
  if (d.result && d.result.result) {
    console.log(JSON.stringify(d.result.result));
  }
  process.exit(0);
};

ws.onerror = (err) => {
  console.error('WS ERROR:', err.message);
  process.exit(1);
};

setTimeout(() => {
  console.error('TIMEOUT');
  process.exit(1);
}, 12000);
