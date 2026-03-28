/**
 * bot-monitor.js
 * Bot channel session 分析模块（供 server.js 调用）
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SESSION_DIR = '/root/.openclaw/agents/primary/sessions';
const LCM_DB = '/root/.openclaw/lcm.db';

// ─── 时间工具 ──────────────────────────────────────────────
function parseTs(ts) {
  if (!ts) return null;
  if (typeof ts === 'number' && ts > 1e9) return new Date(ts);
  if (typeof ts === 'string') {
    const d = new Date(ts);
    return isNaN(d) ? null : d;
  }
  return null;
}

function fmtIdle(ms) {
  const s = ms / 1000;
  if (s < 60) return `${Math.round(s)}秒前`;
  if (s < 3600) return `${Math.round(s / 60)}分钟前`;
  if (s < 86400) return `${(s / 3600).toFixed(1)}小时前`;
  return `${Math.round(s / 86400)}天前`;
}

// ─── Session 发现 ────────────────────────────────────────────
function discoverChannels() {
  const channelMap = new Map(); // channelId → { file, mtime }
  const files = fs.readdirSync(SESSION_DIR);
  for (const f of files) {
    if (f.includes('.deleted.') || f.includes('.reset.') || f.endsWith('.lock')) continue;
    const m = f.match(/topic-(\d+)\.jsonl$/);
    if (!m) continue;
    const channelId = m[1];
    const fullPath = path.join(SESSION_DIR, f);
    const mtime = fs.statSync(fullPath).mtimeMs;
    if (!channelMap.has(channelId) || mtime > channelMap.get(channelId).mtime) {
      channelMap.set(channelId, { file: f, mtime });
    }
  }
  return channelMap;
}

// ─── Session 解析 ────────────────────────────────────────────
function parseSession(filename) {
  const filepath = path.join(SESSION_DIR, filename);
  const lines = fs.readFileSync(filepath, 'utf8').split('\n');
  const events = [];
  for (const line of lines) {
    const t = line.trim();
    if (!t) continue;
    try { events.push(JSON.parse(t)); } catch {}
  }
  return events;
}

function getText(content) {
  if (Array.isArray(content)) {
    return content.filter(c => c?.type === 'text').map(c => c.text).join(' ');
  }
  return typeof content === 'string' ? content : '';
}

function analyzeEvents(events) {
  const result = {
    firstTs: null, lastTs: null,
    lastRole: null, lastText: '',
    lastTool: null, lastError: null,
    aborts: [], errors: [],
    model: null, last5: [],
  };

  for (const ev of events) {
    const ts = parseTs(ev.timestamp);
    if (ts) {
      if (!result.firstTs) result.firstTs = ts;
      result.lastTs = ts;
    }

    if (ev.type === 'message') {
      const msg = ev.message || {};
      const role = msg.role || '';
      const text = getText(msg.content || '');
      const toolName = msg.toolName || '';
      let isError = msg.isError || false;

      if (text) {
        const firstLine = text.split('\n')[0].trim();
        // 插件注册日志 / openclaw 内部日志 → 不算错误
        const isFalsePositive = firstLine.startsWith('[plugins]') ||
          firstLine.startsWith('[skills]') ||
          firstLine.startsWith('[lcm]') ||
          firstLine.match(/^\{.*subsystem/);
        if (isFalsePositive) { isError = false; }
        // 文本内容推断真实错误（仅限 toolResult，不对 assistant 消息做推断）
        else if (!isError && role === 'toolResult') {
          if (firstLine.startsWith('Error:') ||
              firstLine.startsWith('❌') ||
              firstLine.includes('Missing required file') ||
              firstLine.startsWith('ENOENT') ||
              firstLine.startsWith('Command failed')) {
            isError = true;
          }
        }
      }

      result.lastRole = role;
      if (text) result.lastText = text;
      if (toolName) result.lastTool = toolName;
      if (isError && text) {
        result.errors.push({ ts, tool: toolName, text: text.slice(0, 300) });
        result.lastError = text.slice(0, 300);
      }

      result.last5.push({ ts, role, text: text.slice(0, 200), tool: toolName, isError });
      if (result.last5.length > 5) result.last5.shift();

    } else if (ev.type === 'custom') {
      const ct = ev.customType || '';
      const data = ev.data || {};
      const model = data.model || data.modelId;
      if (model) result.model = model;
      if (ct === 'openclaw:prompt-error') {
        result.aborts.push({ ts, model: data.model, error: data.error || '' });
      }
    }
  }
  return result;
}

// ─── 诊断 ────────────────────────────────────────────────────
function diagnose(analysis, idleMs, hasLock) {
  const { lastError, aborts, lastRole } = analysis;

  if (lastError) {
    if (lastError.includes('easyclaw') || lastError.includes('Missing required file')) {
      return {
        status: 'error', label: '工具缺失',
        reason: `依赖文件缺失：${lastError.slice(0, 80)}`,
        fix: '已修复 ppt-nano，在 Discord 发消息让 bot 重试',
        fixCmd: null,
      };
    }
    if (/rate.?limit/i.test(lastError)) {
      return {
        status: 'error', label: '速率限制',
        reason: 'API 请求超出速率限制',
        fix: '等待 60 秒后重试，或切换模型',
        fixCmd: null,
      };
    }
    if (/overload|503/i.test(lastError)) {
      return {
        status: 'warn', label: 'API 过载',
        reason: 'API 服务暂时过载',
        fix: '等待后重试或切换到备用模型',
        fixCmd: null,
      };
    }
    if (/timeout/i.test(lastError)) {
      return {
        status: 'warn', label: '请求超时',
        reason: '工具执行超时',
        fix: '检查网络或重新触发任务',
        fixCmd: null,
      };
    }
    return {
      status: 'error', label: '工具报错',
      reason: lastError.slice(0, 100),
      fix: '查看错误详情，在 Discord 重新触发任务',
      fixCmd: null,
    };
  }

  if (aborts.length > 0) {
    const last = aborts[aborts.length - 1];
    if (last.error === 'aborted') {
      return {
        status: 'warn', label: '生成中断',
        reason: `LLM 生成被打断（${last.model || '?'}），通常因 gateway 重启`,
        fix: '在 Discord 发"继续"让 bot 重新生成',
        fixCmd: null,
      };
    }
  }

  if (hasLock) {
    return { status: 'ok', label: '运行中', reason: '有锁，bot 正在处理中', fix: '等待完成', fixCmd: null };
  }

  const idleMins = idleMs / 60000;
  if (idleMins > 60) {
    return { status: 'idle', label: '空闲', reason: `已空闲 ${fmtIdle(idleMs)}`, fix: '正常待机', fixCmd: null };
  }
  if (lastRole === 'assistant') {
    return { status: 'ok', label: '正常', reason: `最近有回复，${fmtIdle(idleMs)}`, fix: '无需处理', fixCmd: null };
  }

  return {
    status: 'unknown', label: '未知',
    reason: `最后事件 ${fmtIdle(idleMs)}，角色：${lastRole || '?'}`,
    fix: '尝试在 Discord 发消息触发 bot',
    fixCmd: null,
  };
}

// ─── 从 session 提取频道元信息 ───────────────────────────────
function extractChannelMeta(events) {
  for (const ev of events.slice(0, 30)) {
    if (ev.type !== 'message') continue;
    const text = getText(ev.message?.content || '');
    if (!text) continue;

    // thread_label: "Discord thread #main › 资料一键转视频学习"
    const threadMatch = text.match(/"thread_label"\s*:\s*"Discord thread #([^›"]+)›?\s*([^"]+)"/);
    if (threadMatch) {
      const category = threadMatch[1].trim().replace(/^#/, '');
      const name = threadMatch[2].trim();
      return { name, category: category || 'main' };
    }
    // conversation_label: "Guild #美股专区 channel id:..."
    const convMatch = text.match(/"conversation_label"\s*:\s*"Guild #([^"c][^"]+?) channel id:/);
    if (convMatch) {
      return { name: convMatch[1].trim(), category: '' };
    }
  }
  return { name: '', category: '' };
}

// ─── 从 reset 备份文件提取元信息 ──────────────────────────────
function extractMetaFromResets(channelId) {
  try {
    const files = fs.readdirSync(SESSION_DIR);
    const resets = files
      .filter(f => f.includes(`-topic-${channelId}.jsonl.reset.`))
      .sort().reverse(); // newest first
    for (const f of resets.slice(0, 3)) {
      try {
        const lines = fs.readFileSync(path.join(SESSION_DIR, f), 'utf8').split('\n');
        const evs = [];
        for (const line of lines) {
          const t = line.trim();
          if (!t) continue;
          try { evs.push(JSON.parse(t)); } catch {}
        }
        const meta = extractChannelMeta(evs);
        if (meta.name) return meta;
      } catch {}
    }
  } catch {}
  return { name: '', category: '' };
}

// ─── 单 Channel 完整扫描 ─────────────────────────────────────
function scanChannel(channelId, sessionFile) {
  const now = Date.now();
  const lockPath = path.join(SESSION_DIR, sessionFile + '.lock');
  const hasLock = fs.existsSync(lockPath);

  let events = [];
  try { events = parseSession(sessionFile); } catch (e) {
    return {
      channelId, sessionFile,
      eventCount: 0, firstTs: null, lastTs: null, idleMs: 0,
      model: null, hasLock: false, errors: [], aborts: [], last5: [],
      diagnosis: { status: 'error', label: '读取失败', reason: e.message, fix: '检查 session 文件', fixCmd: null },
    };
  }

  const analysis = analyzeEvents(events);
  const idleMs = analysis.lastTs ? (now - analysis.lastTs.getTime()) : 999999999;
  const diagnosis = diagnose(analysis, idleMs, hasLock);
  let meta = extractChannelMeta(events);
  if (!meta.name) meta = extractMetaFromResets(channelId);

  return {
    channelId, sessionFile,
    channelName: meta.name,
    channelCategory: meta.category,
    eventCount: events.length,
    firstTs: analysis.firstTs?.toISOString() || null,
    lastTs: analysis.lastTs?.toISOString() || null,
    idleMs, idleLabel: fmtIdle(idleMs),
    model: analysis.model,
    hasLock,
    errors: analysis.errors.slice(-2),
    aborts: analysis.aborts.slice(-2),
    last5: analysis.last5,
    diagnosis,
  };
}

// ─── 全量扫描（返回数组）────────────────────────────────────
function scanAll() {
  const channels = discoverChannels();
  const results = [];
  for (const [channelId, { file }] of channels) {
    results.push(scanChannel(channelId, file));
  }
  // 排序：error > warn > unknown > ok > idle
  const order = { error: 0, warn: 1, unknown: 2, ok: 3, idle: 4 };
  results.sort((a, b) => (order[a.diagnosis.status] ?? 9) - (order[b.diagnosis.status] ?? 9));
  return results;
}

// ─── Gateway 状态 ────────────────────────────────────────────
function gatewayStatus() {
  let pid = null;
  let rpc = false;
  try {
    pid = execSync('pgrep -f "openclaw.*gateway"', { timeout: 3000 }).toString().trim().split('\n')[0] || null;
  } catch {}
  try {
    execSync('curl -s --max-time 2 http://127.0.0.1:1979/ > /dev/null 2>&1', { timeout: 4000 });
    rpc = true;
  } catch {}
  const ok = !!(pid && rpc);
  return { ok, pid, rpc };
}

// ─── Discord 预警 ─────────────────────────────────────────────
const ALERT_STATE_FILE = path.join(__dirname, '.alert-state.json');

function loadAlertState() {
  try { return JSON.parse(fs.readFileSync(ALERT_STATE_FILE, 'utf8')); } catch { return {}; }
}

function saveAlertState(state) {
  try { fs.writeFileSync(ALERT_STATE_FILE, JSON.stringify(state, null, 2)); } catch {}
}

// 构造预警消息文本
function buildAlertMessage(ch) {
  const d = ch.diagnosis;
  const statusEmoji = { error: '🚨', warn: '⚠️', unknown: '❓' }[d.status] || '📢';
  const name = ch.channelName ? `${ch.channelCategory ? ch.channelCategory + ' / ' : ''}${ch.channelName}` : ch.channelId;
  const lines = [
    `${statusEmoji} **Channel Bot 预警**`,
    `> 频道：**${name}**（\`${ch.channelId}\`）`,
    `> 状态：**${d.label}**`,
    ``,
    `**📋 问题详情**`,
    `> ${d.reason.slice(0, 200)}`,
    ``,
    `**🔧 处理方案**`,
    `> ${d.fix}`,
    ``,
    `> 🤖 *此消息由后台扫描自动发送*`,
    `> 🔗 详细监控：http://127.0.0.1:1980/bot`,
  ];
  return lines.join('\n');
}

// 发送预警到 Discord 频道
function sendAlert(channelId, message) {
  try {
    execSync(
      `openclaw message send --channel discord --target ${channelId} --message ${JSON.stringify(message)}`,
      { timeout: 15000 }
    );
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message.slice(0, 200) };
  }
}

// 检查是否需要发预警（状态变化 or 首次出现错误），并发送
// 返回 { sent: bool, channelId, result? }
function checkAndAlert(ch) {
  const state = loadAlertState();
  const prev = state[ch.channelId];
  const cur = ch.diagnosis.status;

  // 只对 error / warn 发送
  if (cur !== 'error' && cur !== 'warn') {
    // 如果之前是错误，清除状态（已恢复）
    if (prev && (prev.status === 'error' || prev.status === 'warn')) {
      delete state[ch.channelId];
      saveAlertState(state);
    }
    return { sent: false };
  }

  // 已发过同状态+同label → 不重复发
  if (prev && prev.status === cur && prev.label === ch.diagnosis.label) {
    return { sent: false, reason: 'already_alerted' };
  }

  const msg = buildAlertMessage(ch);
  const result = sendAlert(ch.channelId, msg);

  // 记录本次发送状态
  state[ch.channelId] = {
    status: cur,
    label: ch.diagnosis.label,
    alertedAt: new Date().toISOString(),
    ok: result.ok,
  };
  saveAlertState(state);

  return { sent: true, ok: result.ok, error: result.error };
}

// 全量扫描 + 预警
function scanAllAndAlert() {
  const channels = scanAll();
  const alerts = [];
  for (const ch of channels) {
    if (ch.diagnosis.status === 'error' || ch.diagnosis.status === 'warn') {
      const r = checkAndAlert(ch);
      if (r.sent) alerts.push({ channelId: ch.channelId, name: ch.channelName, ok: r.ok, error: r.error });
    }
  }
  return { channels, alerts };
}

// 手动对单个频道强制发送预警（忽略去重）
function forceAlert(channelId) {
  const channels = scanAll();
  const ch = channels.find(c => c.channelId === channelId);
  if (!ch) return { ok: false, error: 'channel not found' };
  const msg = buildAlertMessage(ch);
  const result = sendAlert(ch.channelId, msg);
  if (result.ok) {
    const state = loadAlertState();
    state[channelId] = {
      status: ch.diagnosis.status,
      label: ch.diagnosis.label,
      alertedAt: new Date().toISOString(),
      ok: true,
    };
    saveAlertState(state);
  }
  return result;
}

function getAlertState() {
  return loadAlertState();
}

module.exports = {
  scanAll, scanAllAndAlert, scanChannel, discoverChannels, gatewayStatus, fmtIdle,
  checkAndAlert, forceAlert, getAlertState,
};
