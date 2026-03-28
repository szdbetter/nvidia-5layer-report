/**
 * wukong-monitor.js
 * 监控钉钉悟空邀请码，图片 URL 变化时 Discord 私聊通知
 *
 * 检测逻辑：
 *  - 开启监控时，先建立「基线」URL（当前状态），不发通知
 *  - 后续检查：只要图片 URL 变化，就通知 → 说明有新内容更新，用户自行确认
 *  - 橙色「限量」图 / 灰色「已领完」图均属已知非可领状态，新图才是新邀请码
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

// ─── 读取 .openclaw/.env ────────────────────────────────────
function loadEnvFile() {
  try {
    const raw = fs.readFileSync('/root/.openclaw/.env', 'utf8');
    const vars = {};
    for (const line of raw.split('\n')) {
      const m = line.match(/^([A-Z0-9_]+)=(.+)$/);
      if (m) vars[m[1]] = m[2].trim();
    }
    return vars;
  } catch { return {}; }
}
const ENV = loadEnvFile();

const STATE_FILE = path.join(__dirname, '.wukong-state.json');
const INVITE_API = 'https://hudong.alicdn.com/api/data/v2/438eae9715f945468d599660d2d92aeb.js';
const NOTIFY_USER = 'user:825020287162122302';

// ─── 状态持久化 ─────────────────────────────────────────────
function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
  catch { return { disabled: true }; } // 默认关闭
}
function saveState(s) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2));
}

// ─── 获取当前邀请码图片 URL ─────────────────────────────────
function fetchInviteImageUrl() {
  return new Promise((resolve, reject) => {
    const t = Date.now();
    const cbName = `wk_cb_${t}`;
    const url = `${INVITE_API}?t=${t}&callback=${cbName}`;
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => {
        const m = body.match(/"img_url"\s*:\s*"([^"]+)"/);
        if (m) resolve(m[1]);
        else reject(new Error('img_url not found: ' + body.slice(0, 200)));
      });
    }).on('error', reject);
  });
}

// ─── 发送 Resend 邮件通知 ───────────────────────────────────
function sendResendEmail(imageUrl) {
  return new Promise((resolve) => {
    const apiKey = ENV.RESEND_API_KEY_1;
    const to = ENV.RESEND_TO || '8044372@gmail.com';
    if (!apiKey) return resolve({ ok: false, error: 'RESEND_API_KEY_1 not set' });

    const body = JSON.stringify({
      from: 'onboarding@resend.dev',
      to: [to],
      subject: '🔔 悟空邀请码页面有更新！',
      html: `
        <h2>悟空邀请码页面有更新！</h2>
        <p>图片已更换，请确认是否有新邀请码可领取。</p>
        <p><img src="${imageUrl}" style="max-width:400px;border-radius:8px;" /></p>
        <p><a href="https://www.dingtalk.com/wukong">立即前往领取 →</a></p>
        <hr/>
        <p style="color:#999;font-size:12px">由 ClawLabs Bot 监控自动发送 | <a href="http://127.0.0.1:1980/bot">查看监控面板</a></p>
      `,
    });

    const req = https.request({
      hostname: 'api.resend.com',
      path: '/emails',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    }, (res) => {
      let data = '';
      res.on('data', d => data += d);
      res.on('end', () => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve({ ok: true, id: JSON.parse(data).id });
        } else {
          resolve({ ok: false, error: `HTTP ${res.statusCode}: ${data.slice(0, 200)}` });
        }
      });
    });
    req.on('error', e => resolve({ ok: false, error: e.message }));
    req.write(body);
    req.end();
  });
}

// ─── 发送 Discord 私聊通知 ──────────────────────────────────
function sendDiscordDM(message) {
  try {
    execSync(
      `openclaw message send --channel discord --target ${NOTIFY_USER} --message ${JSON.stringify(message)}`,
      { timeout: 15000 }
    );
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message.slice(0, 200) };
  }
}

// ─── 单次检查 ───────────────────────────────────────────────
async function checkOnce() {
  const state = loadState();
  const now = new Date().toISOString();

  if (state.disabled) {
    return { status: 'disabled', message: '监控已关闭' };
  }

  let imageUrl;
  try {
    imageUrl = await fetchInviteImageUrl();
  } catch (e) {
    const err = `获取失败: ${e.message.slice(0, 100)}`;
    state.lastCheck = now;
    state.lastError = err;
    saveState(state);
    return { status: 'error', message: err };
  }

  // 提取图片 URL 唯一标识
  const urlId = imageUrl.match(/O1CN[A-Za-z0-9_!-]+/)?.[0] || imageUrl.slice(-30);
  const prevUrlId = state.lastUrlId || '';
  const isBaseline = !prevUrlId; // 首次检查 = 建立基线，不通知
  const isNew = !isBaseline && (urlId !== prevUrlId);

  const result = {
    status: 'ok',
    imageUrl,
    urlId,
    isNew,
    isBaseline,
    checkedAt: now,
  };

  // 更新状态
  state.lastCheck = now;
  state.lastUrlId = urlId;
  state.lastImageUrl = imageUrl;
  state.lastError = null;

  // URL 变化 → 通知 + 立即 OCR（首次建立基线时不通知）
  if (isNew) {
    const msg = [
      `🔔 **悟空邀请码页面有更新！**`,
      ``,
      `🖼 图片已更换，请确认是否有新邀请码可领取`,
      `🔗 立即前往：https://www.dingtalk.com/wukong`,
      ``,
      `> 🤖 后台自动发现 | 详情：http://127.0.0.1:1980/bot`,
    ].join('\n');
    const dmResult = sendDiscordDM(msg);
    // 同时发送邮件
    sendResendEmail(imageUrl).then(emailResult => {
      const s = loadState();
      s.lastEmailResult = emailResult;
      saveState(s);
    });
    // 立即 OCR，结果缓存到 state（不阻塞返回）
    state.lastInviteCode = null;
    state.ocrStatus = 'pending';
    ocrInviteCode(imageUrl).then(rawText => {
      const s = loadState();
      // 提取邀请码
      const m = rawText.match(/邀请码[：:]\s*(.+)/);
      s.lastInviteCode = m ? m[1].split('\n')[0].trim() : rawText;
      s.ocrStatus = 'done';
      s.ocrRawText = rawText;
      saveState(s);
      console.log('[wukong] OCR done:', s.lastInviteCode);
    }).catch(e => {
      const s = loadState();
      s.ocrStatus = 'error';
      s.ocrError = e.message;
      saveState(s);
      console.log('[wukong] OCR error:', e.message);
    });
    state.lastNotify = now;
    state.lastNotifyResult = dmResult;
    result.notified = true;
    result.notifyResult = dmResult;
  } else {
    result.notified = false;
  }

  // 附带已缓存的邀请码
  result.inviteCode = state.lastInviteCode || null;
  result.ocrStatus = state.ocrStatus || null;

  saveState(state);
  return result;
}

// ─── 开关控制 ────────────────────────────────────────────────
function enableMonitor() {
  const state = loadState();
  delete state.disabled;
  delete state.disabledAt;
  // 清除上次 URL，下次检查建立新基线（避免误通知当前已知图）
  delete state.lastUrlId;
  state.enabledAt = new Date().toISOString();
  saveState(state);
  return { ok: true, message: '悟空监控已开启，正在建立基线…' };
}

function disableMonitor() {
  const state = loadState();
  state.disabled = true;
  state.disabledAt = new Date().toISOString();
  saveState(state);
  return { ok: true, message: '悟空监控已关闭' };
}

function getMonitorState() {
  const state = loadState();
  return {
    enabled: !state.disabled,
    disabled: !!state.disabled,
    disabledAt: state.disabledAt || null,
    enabledAt: state.enabledAt || null,
    lastCheck: state.lastCheck || null,
    lastUrlId: state.lastUrlId || null,
    lastImageUrl: state.lastImageUrl || null,
    lastError: state.lastError || null,
    lastNotify: state.lastNotify || null,
    baselineSet: !!(state.lastUrlId), // 是否已建立基线
    lastInviteCode: state.lastInviteCode || null,
    ocrStatus: state.ocrStatus || null,
  };
}

// ─── OCR 邀请码（MiniMax VL-01）────────────────────────────
function ocrInviteCode(imageUrl) {
  return new Promise((resolve, reject) => {
    const apiKey = ENV.MINIMAX_API_KEY;
    if (!apiKey) return reject(new Error('MINIMAX_API_KEY not set'));

    // Gemini Flash — 免费、快、Vision 能力强
    const geminiKey = ENV.GEMINI_API_KEY;
    if (!geminiKey) return reject(new Error('GEMINI_API_KEY not set'));

    // 下载图片转 base64
    https.get(imageUrl, (imgRes) => {
      const chunks = [];
      imgRes.on('data', d => chunks.push(d));
      imgRes.on('end', () => {
        const buf = Buffer.concat(chunks);
        const base64 = buf.toString('base64');
        const mimeType = imageUrl.includes('.png') ? 'image/png' : 'image/jpeg';

        const body = JSON.stringify({
          contents: [{
            parts: [
              { inline_data: { mime_type: mimeType, data: base64 } },
              { text: '严格OCR：逐字识别图中"当前邀请码："右侧的每一个汉字。图中文字很大很清晰，请仔细看每个字的笔画，不要跳过任何字，不要合并，不要猜测。只输出这几个汉字，不要输出其他任何内容。' }
            ]
          }],
          generationConfig: {
            temperature: 0,
            thinkingConfig: { thinkingBudget: 0 }
          }
        });

        const req = https.request({
          hostname: 'generativelanguage.googleapis.com',
          path: `/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiKey}`,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(body),
          },
        }, (res) => {
          let data = '';
          res.on('data', d => data += d);
          res.on('end', () => {
            try {
              console.log('[wukong-ocr] status:', res.statusCode, 'raw:', data.slice(0, 300));
              const parsed = JSON.parse(data);
              const text = (parsed.candidates?.[0]?.content?.parts?.[0]?.text || '').trim();
              resolve(text);
            } catch (e) {
              reject(new Error('OCR parse error: ' + data.slice(0, 300)));
            }
          });
        });
        req.on('error', reject);
        req.write(body);
        req.end();
      });
    }).on('error', reject);
  });
}

module.exports = { checkOnce, enableMonitor, disableMonitor, getMonitorState, ocrInviteCode };
