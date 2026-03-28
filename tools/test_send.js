// 测试发送：打开爱酷的峻熠对话，发一条跟进消息
const WSUrl = 'ws://127.0.0.1:9222/devtools/page/510291CC21A42B2154BDF96120E81430';
let msgId = 0;
const pending = {};

function cdp(ws, method, params) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    pending[id] = { resolve, reject };
    ws.send(JSON.stringify({ id, method, params: params || {} }));
    setTimeout(() => { if (pending[id]) { delete pending[id]; reject(new Error('timeout:' + method)); } }, 15000);
  });
}

async function evalJS(ws, expr, awaitPromise) {
  const r = await cdp(ws, 'Runtime.evaluate', { expression: expr, awaitPromise: !!awaitPromise, returnByValue: true });
  return r.result && r.result.result ? r.result.result.value : null;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const ws = new WebSocket(WSUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; setTimeout(() => rej(new Error('timeout')), 8000); });
  ws.onmessage = e => { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id].resolve(d); delete pending[d.id]; } };

  console.log('Connected');

  // 点击爱酷的峻熠 (idx=3)
  await evalJS(ws, `(() => { const els = document.querySelectorAll('[class*=conversation-item]'); if(els[3]) { els[3].click(); return true; } return false; })()`);
  await sleep(2000);

  // 读取最新消息
  const msgs = await evalJS(ws, `(() => { const els = document.querySelectorAll('[class*=message-text]'); const r=[]; els.forEach(el => r.push({isMe: el.className.includes('right'), text: el.innerText.trim().substring(0,100)})); return JSON.stringify(r.slice(-5)); })()`);
  console.log('Current messages:', JSON.parse(msgs || '[]').map(m => (m.isMe?'[ME]':'[BUY]') + ' ' + m.text));

  // 找到输入框
  const inputFound = await evalJS(ws, `(() => { const inp = document.querySelector('.ant-input'); return inp ? 'found:' + inp.tagName : 'not found'; })()`);
  console.log('Input:', inputFound);

  // 输入文字
  const testMsg = '亲～您的优惠已帮您保留，方便的话尽快下单哦，座位比较抢手 😊';
  const typed = await evalJS(ws, `(() => {
    const inp = document.querySelector('.ant-input');
    if (!inp) return 'NO_INPUT';
    inp.focus();
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
    if (setter && setter.set) setter.set.call(inp, ${JSON.stringify(testMsg)});
    else inp.value = ${JSON.stringify(testMsg)};
    inp.dispatchEvent(new Event('input', {bubbles:true}));
    return 'TYPED:' + inp.value.substring(0,30);
  })()`);
  console.log('Typed:', typed);
  await sleep(500);

  // 找到发送按钮
  const btns = await evalJS(ws, `(() => {
    const sb = document.querySelector('[class*=sendbox-bottom]');
    if (!sb) return 'no sendbox';
    const btns = sb.querySelectorAll('button');
    return JSON.stringify([...btns].map(b => b.className.substring(0,40) + '|' + b.innerText));
  })()`);
  console.log('Send buttons:', btns);

  // 点击发送
  const sent = await evalJS(ws, `(() => {
    const sb = document.querySelector('[class*=sendbox-bottom]');
    if (sb) {
      const btn = sb.querySelector('button');
      if (btn) { btn.click(); return 'SENT via button'; }
    }
    // Enter key fallback
    const inp = document.querySelector('.ant-input');
    if (inp) {
      inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
      return 'SENT via Enter';
    }
    return 'FAILED';
  })()`);
  console.log('Send result:', sent);

  ws.close();
  process.exit(0);
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
