/**
 * 闲鱼电影票 IM 自动回复 v4
 * 安全过滤：只处理近期电影票相关对话
 */
const { execSync } = require('child_process');

function getWSUrl() {
  const tabs = JSON.parse(execSync('curl -s --noproxy "*" http://127.0.0.1:9222/json/list', {encoding:'utf8'}));
  const tab = tabs.find(t => t.url && t.url.includes('goofish.com/im'));
  if (!tab) throw new Error('No goofish tab found');
  console.log('Tab:', tab.id, tab.url.substring(0,50));
  return tab.webSocketDebuggerUrl;
}

let msgId = 0;
const pending = {};

function cdp(ws, method, params) {
  return new Promise((res, rej) => {
    const id = ++msgId;
    pending[id] = { res, rej };
    ws.send(JSON.stringify({ id, method, params: params || {} }));
    setTimeout(() => { if (pending[id]) { delete pending[id]; rej(new Error('timeout:' + method)); } }, 15000);
  });
}

async function evalJS(ws, expr, awaitP) {
  const r = await cdp(ws, 'Runtime.evaluate', { expression: expr, awaitPromise: !!awaitP, returnByValue: true });
  if (r.result && r.result.result) return r.result.result.value;
  throw new Error('evalJS failed');
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// 判断时间字符串是否是"最近"（今天内或昨天）
function isRecent(timeStr) {
  if (!timeStr) return false;
  const t = timeStr.trim();
  // 最近：X分钟前、X小时前、刚刚、今天、昨天、03-17、03-18（当月内）
  if (t.includes('分钟前') || t.includes('小时前') || t.includes('刚刚')) return true;
  if (t.includes('今天') || t.includes('昨天')) return true;
  // 日期格式 MM-DD，如 03-17
  const mdMatch = t.match(/^(\d{2})-(\d{2})$/);
  if (mdMatch) {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const mMonth = parseInt(mdMatch[1]);
    const mDay = parseInt(mdMatch[2]);
    // 当月内的都算近期
    if (mMonth === month && mDay >= day - 3) return true;
  }
  return false;
}

// 判断对话内容是否与电影票相关
function isMovieRelated(preview) {
  const keywords = ['电影', '影城', '影院', '场次', '座位', '选座', '排', '票', '出票', '取票', '优惠价', '截图'];
  return keywords.some(k => preview.includes(k));
}

async function getConversations(ws) {
  const raw = await evalJS(ws, `
    (() => {
      const convList = document.querySelector('[class*=conv-list-scroll],[class*=conversation-list]');
      if (!convList) return JSON.stringify([]);
      const items = convList.querySelectorAll('[class*=conversation-item]');
      const result = [];
      items.forEach((el, idx) => {
        const lines = el.innerText.trim().split('\\n').map(l => l.trim()).filter(l => l.length > 0);
        result.push({ idx, name: lines[0] || '', preview: lines.slice(1).join(' '), lines });
      });
      return JSON.stringify(result);
    })()`);
  return JSON.parse(raw || '[]');
}

async function openConvAndWait(ws, idx) {
  const before = await evalJS(ws, `document.querySelector('[class*=chat-main]')?.innerText?.substring(0,50) || ''`);
  await evalJS(ws, `
    (() => {
      const convList = document.querySelector('[class*=conv-list-scroll],[class*=conversation-list]');
      if (!convList) return false;
      const items = convList.querySelectorAll('[class*=conversation-item]');
      if (items[${idx}]) { items[${idx}].click(); return true; }
      return false;
    })()`);
  for (let i = 0; i < 10; i++) {
    await sleep(500);
    const after = await evalJS(ws, `document.querySelector('[class*=chat-main]')?.innerText?.substring(0,50) || ''`);
    if (after !== before && after.length > 10) break;
  }
  await sleep(500);
}

async function getChatMessages(ws) {
  const raw = await evalJS(ws, `
    (() => {
      const chatMain = document.querySelector('[class*=chat-main]');
      if (!chatMain) return JSON.stringify({ msgs: [] });
      // 文字消息
      const textEls = [...chatMain.querySelectorAll('[class*=message-text-left],[class*=message-text-right]')];
      
      // 图片消息：找 image-container，判断父元素方向
      const imgEls = [...chatMain.querySelectorAll('[class*=image-container]')];
      
      const allItems = [];
      
      textEls.forEach(el => {
        allItems.push({ el, text: el.innerText.trim(), isMe: el.className.includes('right') });
      });
      
      imgEls.forEach(el => {
        // 往上找含 left/right 的父元素
        let cur = el.parentElement;
        let isMe = null;
        for (let i=0; i<10 && cur && cur !== chatMain; i++) {
          if (cur.className && cur.className.includes('right')) { isMe = true; break; }
          if (cur.className && cur.className.includes('left')) { isMe = false; break; }
          cur = cur.parentElement;
        }
        allItems.push({ el, text: '[图片]', isMe: isMe === true });
      });
      
      // 按 DOM 顺序排序
      const allSelectorEls = [...chatMain.querySelectorAll('[class*=message-text-left],[class*=message-text-right],[class*=image-container]')];
      const msgs = allSelectorEls.map(domEl => {
        const found = allItems.find(item => item.el === domEl);
        return found && found.text.length > 0 ? { text: found.text.substring(0,300), isMe: found.isMe } : null;
      }).filter(Boolean);
      return JSON.stringify({ msgs: msgs.slice(-10) });
    })()`);
  const data = JSON.parse(raw || '{"msgs":[]}');
  return data.msgs || [];
}

async function sendMessage(ws, text) {
  // 模拟真人打字：随机延迟 3-8 秒再发出
  const typingDelay = 3000 + Math.floor(Math.random() * 5000);
  console.log(`  [typing] 等待 ${Math.round(typingDelay/1000)}s 模拟打字...`);
  await sleep(typingDelay);

  const esc = text.replace(/\\/g,'\\\\').replace(/`/g,'\\`').replace(/\$/g,'\\$').replace(/'/g,"\\'");
  const typed = await evalJS(ws, `
    (() => {
      const inp = document.querySelector('.ant-input,[class*=textarea-no-border]');
      if (!inp) return 'NO_INPUT';
      inp.focus();
      const s = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');
      if (s && s.set) s.set.call(inp,'${esc}'); else inp.value='${esc}';
      inp.dispatchEvent(new Event('input',{bubbles:true}));
      return 'TYPED';
    })()`);
  if (typed !== 'TYPED') return typed;
  await sleep(300 + Math.floor(Math.random() * 500));
  return evalJS(ws, `
    (() => {
      const sb = document.querySelector('[class*=sendbox-bottom]');
      if (sb) { const btn = sb.querySelector('button'); if (btn) { btn.click(); return 'SENT'; } }
      return 'NO_BTN';
    })()`);
}

function checkShowtime(msgs) {
  // 只检查最新1条买家消息，不扫全部历史
  const last = msgs[msgs.length - 1];
  if (!last || last.isMe) return { ok: true, reason: 'no_buyer_msg' };
  
  // 图片消息不做时间检测，直接通过
  if (last.text === '[图片]' || last.text.trim() === '') {
    return { ok: true, reason: 'image_no_check' };
  }
  
  const text = last.text;
  const pats = [
    /(\d{1,2})月(\d{1,2})日[^\d]{0,5}(\d{1,2}):(\d{2})/,
    /(\d{2})-(\d{2})[^\d]{0,5}(\d{1,2}):(\d{2})/,
  ];
  const now = new Date();
  for (const pat of pats) {
    const m = text.match(pat);
    if (!m) continue;
    const date = new Date(now.getFullYear(), parseInt(m[1])-1, parseInt(m[2]), parseInt(m[3]), parseInt(m[4]));
    const diffMin = (date - now) / 60000;
    if (diffMin < 0) return { ok: false, reason: `场次已过期(${m[0]})` };
    if (diffMin < 45) return { ok: false, reason: `距开场仅${Math.round(diffMin)}分钟` };
    return { ok: true, reason: `距开场${Math.round(diffMin)}分钟` };
  }
  return { ok: true, reason: 'no_showtime' };
}

// 判断买家消息是否是电影票咨询意图（包含图片消息）
function isTicketInquiry(text) {
  // 图片消息 = 买家发了截图，视为选座咨询，直接触发
  if (!text || text.trim() === '' || text.includes('[图片]') || text.includes('图片')) return true;
  const t = text.toLowerCase();
  const keywords = ['电影', '影城', '影院', '场次', '选座', '座位', '票', '出票', '取票', '优惠', '价格', '多少钱', '截图', '几块', '能便宜', '代买', '代购', '帮买', '内部价'];
  return keywords.some(k => t.includes(k));
}

function generateReply(msgs) {
  if (!msgs || msgs.length === 0) return null;
  const last = msgs[msgs.length - 1];
  if (!last || last.isMe === true) return null;

  // 只回复电影票购买咨询相关消息
  if (!isTicketInquiry(last.text)) {
    console.log('  [SKIP non-inquiry]', last.text.substring(0, 50));
    return null;
  }

  const check = checkShowtime(msgs);
  if (!check.ok) { console.log('  [SKIP showtime]', check.reason); return null; }
  if (check.reason !== 'no_showtime') console.log('  [TIME OK]', check.reason);

  const recent = msgs.slice(-3).map(m => (m.isMe ? '我:' : '买家:') + m.text.substring(0, 80)).join('\n');
  const prompt = `你是闲鱼电影票卖家客服。根据最近对话，用30字内自然口语回复买家（可用emoji）。若买家发了[图片]，视为发来了选座截图，回复收到正在查询优惠价。若无需回复或话题已结束，只输出：NO_REPLY\n\n${recent}\n\n直接输出回复，不加前缀：`;

  try {
    const f = '/tmp/xy_p_' + Date.now() + '.txt';
    require('fs').writeFileSync(f, prompt);
    const result = execSync(
      `/Users/ai/.local/bin/claude --model claude-haiku-4-5 --print "$(cat ${f})" < /dev/null`,
      { timeout: 25000, encoding: 'utf8', shell: '/bin/bash' }
    ).trim();
    try { require('fs').unlinkSync(f); } catch(e) {}
    if (!result || result.toUpperCase().includes('NO_REPLY')) return null;
    return result.substring(0, 150);
  } catch(e) {
    console.error('  [LLM ERR]', e.message.substring(0, 80));
    const t = last.text.toLowerCase();
    if (t.includes('多少钱') || t.includes('价格')) return '麻烦把选座截图发我，我马上查优惠价 😊';
    if (t.includes('截图') || t.includes('座位') || t.includes('选座')) return '收到截图～正在查优惠价，稍等 😊 先别下单';
    return null;
  }
}

async function main() {
  const wsUrl = getWSUrl();
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = e => rej(new Error('WS err:' + e.message));
    setTimeout(() => rej(new Error('connect timeout')), 10000);
  });
  ws.onmessage = e => {
    try { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id].res(d); delete pending[d.id]; } } catch(err) {}
  };

  console.log('Connected!');
  const convs = await getConversations(ws);
  console.log('Total convs:', convs.length);

  // 过滤：只处理最近有消息的对话（放宽内容过滤，包含图片消息的也要处理）
  const toProcess = convs.filter(c => {
    // 跳过系统通知类
    const SKIP_KEYWORDS = ['30分钟内回复', '不在线回复', '开启不在线', '系统消息', '兑好礼', '平台消息'];
    if (SKIP_KEYWORDS.some(k => c.preview.includes(k))) {
      console.log(`  [SKIP system] ${c.name} | ${c.preview.substring(0,40)}`);
      return false;
    }
    // 时间过滤：必须是最近的
    const timeStr = c.lines.find(l => l.match(/前|今天|昨天|\d{2}-\d{2}/) );
    if (!timeStr || !isRecent(timeStr)) {
      console.log(`  [SKIP old] ${c.name} | ${timeStr || 'no time'}`);
      return false;
    }
    // 图片消息直接通过（买家发截图）
    if (c.preview.includes('[图片]') || c.preview.includes('图片')) {
      console.log(`  [PASS image] ${c.name}`);
      return true;
    }
    // 电影票相关关键词
    if (isMovieRelated(c.preview)) {
      console.log(`  [PASS movie] ${c.name}`);
      return true;
    }
    console.log(`  [SKIP non-movie] ${c.name} | ${c.preview.substring(0,50)}`);
    return false;
  });

  console.log('Qualified convs:', toProcess.map(c => c.name));

  for (const conv of toProcess) {
    console.log('\n[OPEN]', conv.name);
    await openConvAndWait(ws, conv.idx);
    const msgs = await getChatMessages(ws);
    console.log('  msgs:', msgs.slice(-3).map(m => (m.isMe?'[ME]':'[BUY]') + ' ' + m.text.substring(0,60)));
    const reply = generateReply(msgs);
    if (reply) {
      console.log('  => SEND:', reply.substring(0, 100));
      const r = await sendMessage(ws, reply);
      console.log('  result:', r);
      await sleep(2000);
    } else {
      console.log('  => skip');
    }
  }

  console.log('\n=== DONE ===');
  ws.close();
  process.exit(0);
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
