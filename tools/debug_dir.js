// 点开第一个买家对话，读取消息的完整 class 路径
const { execSync } = require('child_process');
const tabs = JSON.parse(execSync('curl -s --noproxy "*" http://127.0.0.1:9222/json/list', {encoding:'utf8'}));
const tab = tabs.find(t => t.url && t.url.includes('goofish.com/im'));
const ws = new WebSocket(tab.webSocketDebuggerUrl);
let id = 0;
const pending = {};
const cdp = (method, params) => new Promise((res,rej) => {
  const i = ++id;
  pending[i] = {res,rej};
  ws.send(JSON.stringify({id:i, method, params: params||{}}));
  setTimeout(() => { if(pending[i]){delete pending[i];rej(new Error('timeout:'+method));} }, 12000);
});
ws.onmessage = e => {
  const d = JSON.parse(e.data);
  if (d.id && pending[d.id]) { pending[d.id].res(d); delete pending[d.id]; }
};

async function main() {
  await new Promise(r => ws.onopen = r);
  
  // 点开T小滚滚儿 (idx=3 based on previous list)
  await cdp('Runtime.evaluate', {returnByValue:true, expression: `
    (() => {
      const convList = document.querySelector('[class*=conv-list-scroll],[class*=conversation-list]');
      if (!convList) return 'no list';
      const items = convList.querySelectorAll('[class*=conversation-item]');
      if (items[3]) { items[3].click(); return 'clicked ' + items[3].innerText.substring(0,30); }
      return 'no item 3';
    })()`});
  
  // 等待加载
  await new Promise(r => setTimeout(r, 3000));
  
  // 读取消息结构
  const r = await cdp('Runtime.evaluate', {returnByValue:true, expression: `
    (() => {
      const main = document.querySelector('[class*=chat-main]');
      if (!main) return JSON.stringify({err: 'no main'});
      
      // 找所有 message-text 元素并查看其完整祖先链 class
      const msgs = main.querySelectorAll('[class*=message-text]');
      const result = [];
      msgs.forEach(el => {
        let cur = el;
        const path = [];
        while (cur && cur !== main) {
          if (cur.className) path.push(cur.className.substring(0,80));
          cur = cur.parentElement;
        }
        result.push({
          text: el.innerText.substring(0,50),
          // 找含 left/right 的层
          lr: path.filter(c => c.includes('left') || c.includes('right') || c.includes('msg-text'))
        });
      });
      return JSON.stringify(result.slice(-4));
    })()`});
  
  console.log(JSON.stringify(JSON.parse(r.result.result.value), null, 2));
  process.exit(0);
}
main().catch(e => { console.error(e.message); process.exit(1); });
