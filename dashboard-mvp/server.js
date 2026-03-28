const express = require('express');
const path = require('path');
const fs   = require('fs');
const { execSync } = require('child_process');
const db = require('./db');
const { getProjectMissions, PROJECTS_DIR } = require('./adapters');
const botMonitor = require('./bot-monitor');
const wukongMonitor = require('./wukong-monitor');
const taskMgr = require('./task-manager');

const app = express();
const PORT = process.env.PORT || 1980;
const WORKSPACE_ROOT = path.resolve(__dirname, '..');

app.get('/macro', (req, res) => res.sendFile('public/macro.html', { root: __dirname }));

app.use('/static', express.static(path.join(__dirname, 'public')));
app.use('/', express.static(path.join(__dirname, 'public')));
app.use('/project-files', express.static(PROJECTS_DIR));
app.use('/workspace-files', express.static(WORKSPACE_ROOT));
app.use(express.json({ limit: '10mb' }));

function q(sql, params = []) { return db.prepare(sql).all(...params); }
function g(sql, params = []) { return db.prepare(sql).get(...params); }

// ── Cron status from openclaw CLI ─────────────────────────────────────────────
// Read cron jobs directly from Gateway state file (fastest, no WS needed)
async function getCronJobs() {
  try {
    const raw = fs.readFileSync('/root/.openclaw/cron/jobs.json', 'utf8');
    const data = JSON.parse(raw);
    const jobs = data.jobs || (Array.isArray(data) ? data : []);
    return jobs.map(j => ({
      id: j.id,
      name: j.name || j.id,
      enabled: j.enabled,
      schedule: j.schedule?.kind === 'cron'  ? `${j.schedule.expr} (${j.schedule.tz||'UTC'})`
              : j.schedule?.kind === 'every' ? `每 ${Math.round((j.schedule.everyMs||0)/60000)}min`
              : j.schedule?.kind === 'at'    ? j.schedule.at
              : JSON.stringify(j.schedule),
      lastStatus: j.state?.lastRunStatus || j.state?.lastStatus,
      lastRunAt: j.state?.lastRunAtMs ? new Date(j.state.lastRunAtMs).toISOString() : null,
      nextRunAt: j.state?.nextRunAtMs ? new Date(j.state.nextRunAtMs).toISOString() : null,
      consecutiveErrors: j.state?.consecutiveErrors || 0,
      lastError: j.state?.lastError || null,
    }));
  } catch (e) {
    return [];
  }
}

// ── OpenViking health ─────────────────────────────────────────────────────────
function getOVHealth() {
  try {
    const res = execSync('curl -s http://127.0.0.1:1933/health', { timeout: 3000 }).toString();
    const d = JSON.parse(res);
    return { ok: d.status === 'ok', raw: d };
  } catch {
    return { ok: false, raw: null };
  }
}

// ── Poly macro result ─────────────────────────────────────────────────────────
function getPolyMacroResult() {
  try {
    const p = '/tmp/poly_macro_result.json';
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch { return null; }
}

// ── Bot monitor status ────────────────────────────────────────────────────────
function getBotMonitorStatus() {
  try {
    const p = '/tmp/bot_monitor_status.json';
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch { return null; }
}

// ── Fiona daemon result ───────────────────────────────────────────────────────
function getFionaResult() {
  try {
    const p = '/tmp/poly_latest_result.json';
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch { return null; }
}

// ── Project list from /root/.openclaw/projects ────────────────────────────────
function getProjectList() {
  const PROJ = '/root/.openclaw/projects';
  try {
    return fs.readdirSync(PROJ, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => {
        const dir = path.join(PROJ, d.name);
        const task = tryRead(path.join(dir, 'task.md'));
        const issue = tryRead(path.join(dir, 'issue.md'));
        const done = (task.match(/\[Done\]/gi) || []).length;
        const todo = (task.match(/\[ \]/gi) || []).length;
        const openIssues = (issue.match(/^### /gm) || []).length - (issue.match(/## CLOSED/i) ? (issue.split('## CLOSED')[1].match(/^### /gm) || []).length : 0);
        return {
          id: d.name,
          name: d.name,
          taskDone: done,
          taskTodo: todo,
          pct: done + todo > 0 ? Math.round(done * 100 / (done + todo)) : 0,
          openIssues,
          hasRoadmap: fs.existsSync(path.join(dir, 'roadmap.md')),
        };
      });
  } catch { return []; }
}

function tryRead(p) {
  try { return fs.readFileSync(p, 'utf8'); } catch { return ''; }
}

// ── API Routes ────────────────────────────────────────────────────────────────

app.get('/api/summary', (req, res) => {
  const allMissions = getProjectMissions();
  const projectMissions = allMissions.map(m => ({
    id: m.id, name: m.name, owner: m.owner, priority: m.priority, status: m.status,
    current_phase: m.current_phase, next_action: m.next_action, updated_at: m.updated_at,
    progress_done: m.progress_done, progress_total: m.progress_total, progress_pct: m.progress_pct,
    risk_level: m.risk_level, docs: m.docs, source: 'project-docs',
    work_content: m.work_content, sop_summary: m.sop_summary, assignment_summary: m.assignment_summary,
  }));
  const rte = q('SELECT * FROM runtime_entities');
  const mem = q('SELECT * FROM memories');
  const art = q('SELECT * FROM artifacts');
  const rsk = q('SELECT * FROM risks');
  res.json({
    projectBase: PROJECTS_DIR,
    missions: projectMissions,
    counts: {
      missions: projectMissions.length,
      runtime: rte.length,
      memories: mem.length,
      artifacts: art.length,
      risks: rsk.length,
      projectDocs: allMissions.length,
    }
  });
});

// Alias: /api/missions/:id (old app.js compatibility)
app.get('/api/missions/:id', (req, res) => {
  const missions = getProjectMissions();
  const m = missions.find(x => x.id === req.params.id);
  if (!m) return res.status(404).json({ error: 'not found' });
  const resources = q('SELECT * FROM mission_resources WHERE mission_id = ?', [m.id]);
  const assignments = q('SELECT * FROM mission_assignments WHERE mission_id = ?', [m.id]);
  const artifacts = q('SELECT * FROM artifacts WHERE mission_id = ?', [m.id]);
  const risks = q('SELECT * FROM risks WHERE mission_id = ?', [m.id]);
  const events = q('SELECT * FROM mission_events WHERE mission_id = ? ORDER BY created_at DESC LIMIT 20', [m.id]);
  const memories = q('SELECT * FROM memories WHERE mission_id = ?', [m.id]);
  res.json({ mission: m, resources, assignments, artifacts, risks, events, memories,
    taskStats: m.taskStats, docFiles: m.docFiles, projectDocs: m.docs,
    sopSummary: m.sop_summary, assignmentSummary: m.assignment_summary });
});

app.get('/api/mission/:id', (req, res) => {
  const missions = getProjectMissions();
  const m = missions.find(x => x.id === req.params.id);
  if (!m) return res.status(404).json({ error: 'not found' });
  res.json(m);
});

app.get('/api/runtime', async (req, res) => {
  const cron = await getCronJobs();
  const ov   = getOVHealth();
  const poly = getPolyMacroResult();
  const fiona = getFionaResult();
  const botMonitor = getBotMonitorStatus();
  res.json({ cron, openviking: ov, poly_macro: poly, fiona_daemon: fiona, bot_monitor: botMonitor, ts: new Date().toISOString() });
});

app.get('/api/projects', (req, res) => {
  res.json(getProjectList());
});

app.get('/api/file', (req, res) => {
  const { p } = req.query;
  if (!p || !p.startsWith('/root/.openclaw')) return res.status(403).json({ error: 'forbidden' });
  try {
    res.type('text/plain').send(fs.readFileSync(p, 'utf8'));
  } catch { res.status(404).json({ error: 'not found' }); }
});

// Write task event (for agent to update project progress)
app.post('/api/event', (req, res) => {
  const { project, event_type, event_text, source } = req.body;
  if (!project || !event_text) return res.status(400).json({ error: 'missing fields' });
  const PROJ = '/root/.openclaw/projects';
  const evFile = path.join(PROJ, project, 'events.jsonl');
  const entry = JSON.stringify({ ts: new Date().toISOString(), event_type: event_type || 'update', event_text, source: source || 'agent' });
  fs.appendFileSync(evFile, entry + '\n');
  res.json({ ok: true });
});

app.get('/api/events/:project', (req, res) => {
  const PROJ = '/root/.openclaw/projects';
  const evFile = path.join(PROJ, req.params.project, 'events.jsonl');
  if (!fs.existsSync(evFile)) return res.json([]);
  const lines = fs.readFileSync(evFile, 'utf8').trim().split('\n').filter(Boolean);
  const events = lines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  res.json(events.reverse().slice(0, 50));
});

// ── Iran War Arbitrage ───────────────────────────────────────────────────────
app.get('/iran-arb', (req, res) => res.sendFile('public/iran-arb.html', { root: __dirname }));

// ── Cross-market reference prices ────────────────────────────────────────────
app.get('/api/iran-reference', async (req, res) => {
  const CACHE = '/tmp/iran_ref_cache.json';
  try {
    if (fs.existsSync(CACHE)) {
      const c = JSON.parse(fs.readFileSync(CACHE, 'utf8'));
      if (Date.now() - c.fetched_at < 300000) return res.json(c); // 5min cache
    }
  } catch {}

  const sources = [];

  // 1. Manifold Markets — 只取有明确截止日期且与Polymarket问题对齐的盘口
  // 精确映射表：Manifold问题 → Polymarket slug + 为什么有套利空间的解释
  const MANIFOLD_POLY_MAP = [
    {
      manifold_url: 'https://manifold.markets/IrmiPolonsky/usa-x-iran-ceasefire-by-end-of-marc',
      poly_slug: 'us-x-iran-ceasefire-by-march-31',
      deadline: '2026-03-31',
      why_underpriced: '两个市场问题几乎完全相同（美伊停战到3月31日），若价差>5%说明一方定价偏误。Manifold流动性低易被小额推动，Polymarket流动性更高更权威。',
    },
    {
      manifold_url: 'https://manifold.markets/apol/will-the-regime-of-iran-fall-by-the',
      poly_slug: 'will-the-iranian-regime-fall-by-march-31',
      deadline: '2026-03-31',
      why_underpriced: '两个市场问题相同（伊朗政权3月31日前倒台）。政权倒台定义略有差异（Manifold可能更宽松），若Manifold更高说明Polymarket低估了政权更迭风险。',
    },
    {
      manifold_url: 'https://manifold.markets/HenriConfucius/will-mojtaba-khamenei-be-confirmed',
      poly_slug: 'iran-leadership-change-by-march-31',
      deadline: '2026-03-31',
      why_underpriced: 'Manifold问的是Khamenei确认死亡（门槛更高），Polymarket问的是领导层更迭（门槛更低）。若Manifold(确认死亡)> Polymarket(领导层更迭)，则Polymarket严重低估。',
    },
    {
      manifold_url: 'https://manifold.markets/ScottO/iran-government-falls-before-end-of',
      poly_slug: 'will-the-iranian-regime-fall-by-march-31',
      deadline: '2026-03-31',
      why_underpriced: '问题本质相同（伊朗政府3月底前倒台）。价差反映两个预测社区的不同信息来源和用户群体。',
    },
  ];

  try {
    for (const mapping of MANIFOLD_POLY_MAP) {
      try {
        const mSlug = mapping.manifold_url.split('/').pop();
        const r = await fetch(`https://api.manifold.markets/v0/slug/${mSlug}`);
        const m = await r.json();
        if (m.probability == null) continue;
        sources.push({
          platform: 'Manifold',
          question: m.question,
          probability: m.probability,
          url: m.url || mapping.manifold_url,
          deadline: mapping.deadline,
          poly_slug: mapping.poly_slug,
          why_underpriced: mapping.why_underpriced,
          volume: m.volume || 0,
          unique_traders: m.uniqueBettorCount || 0,
        });
      } catch {}
    }
  } catch (e) { sources.push({ platform: 'Manifold', error: e.message }); }

  // 2. Polymarket Gamma cross-search (compare ceasefire vs conflict_ends internally)
  // Already covered in iran-arbitrage, but add logical computed baselines
  const logicalBounds = computeLogicalBounds();

  const result = {
    ok: true,
    sources,
    logical_bounds: logicalBounds,
    fetched_at: Date.now(),
    fetch_time: new Date().toISOString(),
  };
  fs.writeFileSync(CACHE, JSON.stringify(result));
  res.json(result);
});

function mapToPolySlugs(question) {
  const q = question.toLowerCase();
  const maps = [];
  if (/ceasefire.*march|march.*ceasefire/i.test(question)) maps.push('us-x-iran-ceasefire-by-march-31');
  if (/ceasefire.*april|april.*ceasefire/i.test(question)) maps.push('us-x-iran-ceasefire-by-april-30-194');
  if (/regime.*fall|fall.*regime/i.test(question)) {
    maps.push('will-the-iranian-regime-fall-by-march-31');
    maps.push('will-the-iranian-regime-fall-by-april-30');
  }
  if (/boots.*ground|ground.*iran|forces.*enter/i.test(question)) maps.push('us-forces-enter-iran-by-march-31-222-191-243-517-878-439-519');
  if (/leadership.*change|supreme.*leader/i.test(question)) maps.push('iran-leadership-change-by-april-30');
  if (/nuclear.*deal|nuke.*deal/i.test(question)) maps.push('us-iran-nuclear-deal-by-march-31');
  return maps;
}

function computeLogicalBounds() {
  // Hard logical constraints between Polymarket markets
  return [
    {
      id: 'ceasefire_conflict_monotone',
      description: '停战 ≤ 冲突结束 (停战定义更严格，需双方正式宣布)',
      rule: 'ceasefire.yes ≤ conflict_ends.yes',
      source_url: 'https://polymarket.com — 停战需双方政府公告，冲突结束只需14天无交火',
      a_slug: 'us-x-iran-ceasefire-by-april-30-194',
      b_slug: 'iran-x-israelus-conflict-ends-by-april-30-766-662',
      expected_relation: 'A ≤ B',
    },
    {
      id: 'trump_end_ops_vs_ceasefire',
      description: '特朗普宣布结束行动 ≥ 正式停战 (宣布只需单方面声明)',
      rule: 'trump_end_ops.yes ≥ ceasefire.yes',
      source_url: 'https://polymarket.com — 结束行动=Trump公告即可，停战需伊朗同意',
      a_slug: 'trump-announces-end-of-military-operations-against-iran-by-march-31st',
      b_slug: 'us-x-iran-ceasefire-by-march-31',
      expected_relation: 'A ≥ B',
    },
    {
      id: 'regime_fall_vs_leadership_change',
      description: '政权倒台 ≤ 领导层更迭 (倒台是更迭的子集)',
      rule: 'regime_fall.yes ≤ leadership_change.yes',
      source_url: 'https://polymarket.com — 政权倒台必然导致领导层更迭，反之不然',
      a_slug: 'will-the-iranian-regime-fall-by-april-30',
      b_slug: 'iran-leadership-change-by-april-30',
      expected_relation: 'A ≤ B',
    },
    {
      id: 'ceasefire_june_vs_dec',
      description: '6月停战 ≤ 12月停战 (包含关系)',
      rule: 'ceasefire_jun.yes ≤ ceasefire_dec.yes',
      source_url: 'https://polymarket.com — 前者是后者的子集',
      a_slug: 'us-x-iran-ceasefire-by-june-30-752',
      b_slug: 'us-x-iran-ceasefire-by-december-31',
      expected_relation: 'A ≤ B',
    },
  ];
}

app.get('/api/iran-markets', async (req, res) => {
  try {
    // Use tag_slug=iran for comprehensive Iran-related markets
    const r1 = await fetch(`https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100&tag_slug=iran`);
    const d1 = await r1.json();
    // Also search hormuz separately
    const r2 = await fetch(`https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&tag_slug=geopolitics`);
    const d2 = await r2.json();
    const allEvents = [...(Array.isArray(d1)?d1:[]), ...(Array.isArray(d2)?d2:[])];
    // dedup by id
    const seen = new Set();
    const events = allEvents.filter(e => {
      const k = e.id || e.slug;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
    // filter relevant to Iran/Hormuz
    const iranKw = /iran|ceasefire|hormuz|persian|khamenei|military.operation/i;
    const filtered = events.filter(e => iranKw.test(e.title || '') || iranKw.test(e.description || ''));
    const result = filtered.map(e => ({
      id: e.id,
      slug: e.slug,
      title: e.title,
      description: (e.description || '').slice(0, 500),
      endDate: e.endDate,
      volume: e.volume,
      liquidity: e.liquidity,
      markets: (e.markets || []).map(m => ({
        id: m.id,
        question: m.question,
        slug: m.slug,
        yes_price: m.outcomePrices ? parseFloat(Array.isArray(m.outcomePrices) ? m.outcomePrices[0] : JSON.parse(m.outcomePrices)[0]) : null,
        no_price: m.outcomePrices ? parseFloat(Array.isArray(m.outcomePrices) ? m.outcomePrices[1] : JSON.parse(m.outcomePrices)[1]) : null,
        volume: m.volume,
        liquidity: m.liquidity,
        endDate: m.endDate || e.endDate,
      }))
    }));
    res.json({ ok: true, count: result.length, events: result, ts: new Date().toISOString() });
  } catch (e) {
    res.json({ ok: false, error: e.message, events: [] });
  }
});

app.get('/api/iran-arbitrage', async (req, res) => {
  try {
    // fetch markets first
    const r = await fetch(`http://localhost:${PORT}/api/iran-markets`);
    const { events } = await r.json();
    const opportunities = [];
    const analysis = [];

    // 1. 单调性检验：同事件组按截止日期，yes_price 应单调递增
    for (const ev of events) {
      const markets = (ev.markets || [])
        .filter(m => m.yes_price !== null && m.endDate)
        .sort((a, b) => new Date(a.endDate) - new Date(b.endDate));
      for (let i = 0; i < markets.length - 1; i++) {
        const m1 = markets[i], m2 = markets[i + 1];
        const gap = m2.yes_price - m1.yes_price;
        if (gap < -0.02) { // violation: later date has LOWER prob
          opportunities.push({
            type: 'monotonicity_violation',
            severity: Math.abs(gap) > 0.05 ? 'HIGH' : 'MEDIUM',
            event: ev.title,
            market_a: { slug: m1.slug, question: m1.question, endDate: m1.endDate, yes: m1.yes_price },
            market_b: { slug: m2.slug, question: m2.question, endDate: m2.endDate, yes: m2.yes_price },
            edge: Math.abs(gap),
            description: `${m1.endDate?.slice(0,10)} YES(${(m1.yes_price*100).toFixed(1)}%) > ${m2.endDate?.slice(0,10)} YES(${(m2.yes_price*100).toFixed(1)}%) — 违反单调性`,
            action: `BUY ${m2.endDate?.slice(0,10)} YES @ ${(m2.yes_price*100).toFixed(1)}¢ | SELL ${m1.endDate?.slice(0,10)} YES @ ${(m1.yes_price*100).toFixed(1)}¢`,
            expected_roi: `${(Math.abs(gap)*100).toFixed(1)}%`
          });
        }
        // also flag large positive jumps as potential overpricing
        if (gap > 0.25) {
          analysis.push({
            type: 'large_jump',
            event: ev.title,
            from: `${m1.endDate?.slice(0,10)} ${(m1.yes_price*100).toFixed(1)}%`,
            to: `${m2.endDate?.slice(0,10)} ${(m2.yes_price*100).toFixed(1)}%`,
            gap: `+${(gap*100).toFixed(1)}%`,
            note: '日期跳跃巨大，可能存在定价分歧'
          });
        }
      }
    }

    // 2. 逻辑一致性检验
    const flatMarkets = events.flatMap(e => (e.markets||[]).map(m => ({...m, eventTitle: e.title})));
    const ceasefire3 = flatMarkets.find(m => /ceasefire.*march|march.*ceasefire/i.test(m.question));
    const ceasefire4 = flatMarkets.find(m => /ceasefire.*april|april.*ceasefire/i.test(m.question));
    const forcesMar = flatMarkets.find(m => /forces.*enter.*march|enter.*iran.*march/i.test(m.question));
    const forcesDec = flatMarkets.find(m => /forces.*enter.*dec|enter.*iran.*dec/i.test(m.question));
    const endOps = flatMarkets.find(m => /end.*military.*operation|announce.*end/i.test(m.question));

    if (ceasefire3 && forcesMar) {
      const ceasefireP = ceasefire3.yes_price;
      const forcesP = forcesMar.yes_price;
      // ceasefire implies end of direct conflict, forces entering implies escalation — negative correlation expected
      const corr_note = `停战(${(ceasefireP*100).toFixed(1)}%) + 美军进入伊朗(${(forcesP*100).toFixed(1)}%) = ${((ceasefireP+forcesP)*100).toFixed(1)}%`;
      if (ceasefireP + forcesP > 0.55) {
        opportunities.push({
          type: 'logical_inconsistency',
          severity: 'MEDIUM',
          description: `逻辑矛盾：停战概率 + 美军进入伊朗概率之和过高`,
          detail: corr_note,
          action: '若认为两者互斥：做空概率之和偏高的那一方',
          expected_roi: 'N/A — 需方向判断'
        });
      }
      analysis.push({ type: 'correlation_check', note: corr_note });
    }

    // 3. 汇总单调性数据用于前端展示
    const monotonicity_table = [];
    for (const ev of events) {
      const markets = (ev.markets || [])
        .filter(m => m.yes_price !== null && m.endDate)
        .sort((a, b) => new Date(a.endDate) - new Date(b.endDate));
      if (markets.length > 1) {
        monotonicity_table.push({
          event: ev.title,
          series: markets.map(m => ({ date: m.endDate?.slice(0,10), yes: m.yes_price, question: m.question })),
          is_monotone: markets.every((m, i) => i === 0 || m.yes_price >= markets[i-1].yes_price - 0.01)
        });
      }
    }

    res.json({ ok: true, opportunities, analysis, monotonicity_table, ts: new Date().toISOString() });
  } catch (e) {
    res.json({ ok: false, error: e.message, opportunities: [], analysis: [] });
  }
});

app.get('/api/iran-rules', async (req, res) => {
  const CACHE_FILE = '/tmp/iran_rules_cache.json';
  // check cache
  try {
    if (fs.existsSync(CACHE_FILE)) {
      const cache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
      if (Date.now() - cache.ts < 3600000) return res.json(cache);
    }
  } catch {}

  try {
    const r = await fetch(`http://localhost:${PORT}/api/iran-markets`);
    const { events } = await r.json();

    // Load API key from .env
    let apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      try {
        const envContent = fs.readFileSync('/root/.openclaw/.env', 'utf8');
        const match = envContent.match(/ANTHROPIC_API_KEY=([^\n]+)/);
        if (match) apiKey = match[1].trim();
      } catch {}
    }

    if (!apiKey) {
      return res.json({ ok: false, error: 'ANTHROPIC_API_KEY not found', rules: [] });
    }

    const rules = [];
    for (const ev of events.slice(0, 6)) { // limit to 6 events to save tokens
      const desc = ev.description || ev.title;
      const marketList = (ev.markets||[]).map(m => `- ${m.question} (YES: ${(m.yes_price||0)*100}%)`).join('\n');
      const prompt = `You are a prediction market analyst. Analyze this Polymarket event and its markets.

Event: ${ev.title}
Description: ${desc}
Markets:
${marketList}

Respond in JSON with this exact structure:
{
  "trigger_conditions": "精确触发Yes的条件（中文）",
  "gray_areas": "歧义点和边缘案例（中文）",
  "logical_relation": "与其他美伊战争盘口的逻辑关联（中文）",
  "resolution_risk": "解析风险，官方认定标准的不确定性（中文）",
  "key_entities": ["关键实体列表"]
}`;

      try {
        const apiRes = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 500,
            messages: [{ role: 'user', content: prompt }]
          })
        });
        const apiData = await apiRes.json();
        const content = apiData.content?.[0]?.text || '';
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        const parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : { error: 'parse failed', raw: content };
        rules.push({ event_id: ev.id, title: ev.title, slug: ev.slug, ...parsed });
      } catch (e) {
        rules.push({ event_id: ev.id, title: ev.title, slug: ev.slug, error: e.message });
      }
    }

    const result = { ok: true, rules, ts: Date.now() };
    fs.writeFileSync(CACHE_FILE, JSON.stringify(result));
    res.json(result);
  } catch (e) {
    res.json({ ok: false, error: e.message, rules: [] });
  }
});

// ── 闲鱼电影票 Proxy → localhost:8765 ────────────────────────────────────────
const http = require('http');
app.use('/ticket', (req, res) => {
  const targetPath = req.url || '/';
  // express.json() may have already parsed the body; re-serialize if needed
  let bodyData = null;
  if (req.body && Object.keys(req.body).length > 0) {
    bodyData = JSON.stringify(req.body);
  }
  const headers = { ...req.headers, host: '127.0.0.1:8765' };
  if (bodyData) {
    headers['content-length'] = Buffer.byteLength(bodyData).toString();
    headers['content-type'] = 'application/json';
  }
  const options = {
    hostname: '127.0.0.1',
    port: 8765,
    path: targetPath,
    method: req.method,
    headers,
  };
  const proxy = http.request(options, proxyRes => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });
  proxy.on('error', () => res.status(502).json({ error: 'Ticket backend unavailable' }));
  if (bodyData) {
    proxy.write(bodyData);
    proxy.end();
  } else {
    req.pipe(proxy, { end: true });
  }
});

// ── Smart Money Proxy → localhost:8766 ──────────────────────────────────────
app.use('/smartmoney', (req, res) => {
  // Strip /smartmoney prefix — backend expects paths starting with /
  const targetPath = req.url === '/' || req.url === '' ? '/' : req.url;
  let bodyData = null;
  if (req.body && Object.keys(req.body).length > 0) {
    bodyData = JSON.stringify(req.body);
  }
  const smHeaders = { ...req.headers, host: '127.0.0.1:8766' };
  if (bodyData) {
    smHeaders['content-length'] = Buffer.byteLength(bodyData).toString();
    smHeaders['content-type'] = 'application/json';
  }
  const smOptions = {
    hostname: '127.0.0.1', port: 8766, path: targetPath,
    method: req.method, headers: smHeaders,
  };
  const smProxy = http.request(smOptions, proxyRes => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });
  smProxy.on('error', () => res.status(502).json({ error: 'Smart Money backend unavailable' }));
  if (bodyData) { smProxy.write(bodyData); smProxy.end(); }
  else { req.pipe(smProxy, { end: true }); }
});

// ════════════════════════════════════════════════════════════
// Bot Monitor API
// ════════════════════════════════════════════════════════════

app.get('/api/bot/gateway', (req, res) => {
  res.json(botMonitor.gatewayStatus());
});

app.get('/api/bot/channels', (req, res) => {
  try {
    const results = botMonitor.scanAll();
    res.json({ ok: true, channels: results, ts: new Date().toISOString() });
  } catch (e) {
    res.json({ ok: false, error: e.message, channels: [] });
  }
});

// SSE 扫描流：逐个 channel 推送结果，实现扫描动画效果
app.get('/api/bot/scan', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const send = (data) => res.write(`data: ${JSON.stringify(data)}\n\n`);

  try {
    const gw = botMonitor.gatewayStatus();
    send({ type: 'gateway', data: gw });

    const channels = botMonitor.discoverChannels();
    const total = channels.size;
    send({ type: 'total', data: total });

    let idx = 0;
    for (const [channelId, { file }] of channels) {
      const result = botMonitor.scanChannel(channelId, file);
      send({ type: 'channel', data: result, idx, total });
      idx++;
    }
    send({ type: 'done', ts: new Date().toISOString() });
  } catch (e) {
    send({ type: 'error', message: e.message });
  }
  res.end();
});

app.post('/api/bot/restart-gateway', (req, res) => {
  try {
    execSync('openclaw gateway restart', { timeout: 15000 });
    res.json({ ok: true, message: 'Gateway 已重启' });
  } catch (e) {
    res.json({ ok: false, error: e.message });
  }
});

app.post('/api/bot/reset-session/:channelId', (req, res) => {
  const { channelId } = req.params;
  try {
    const channels = botMonitor.discoverChannels();
    const entry = channels.get(channelId);
    if (!entry) return res.json({ ok: false, error: '未找到 session' });

    const SESSION_DIR = '/root/.openclaw/agents/primary/sessions';
    const oldPath = path.join(SESSION_DIR, entry.file);
    const newPath = oldPath.replace('.jsonl', `.reset.${new Date().toISOString().replace(/[:.]/g, '-')}.jsonl`);
    fs.renameSync(oldPath, newPath);

    // 删除 lock（如果有）
    const lockPath = oldPath + '.lock';
    if (fs.existsSync(lockPath)) fs.unlinkSync(lockPath);

    res.json({ ok: true, message: `Session 已重置：${entry.file}` });
  } catch (e) {
    res.json({ ok: false, error: e.message });
  }
});

// ─── 预警接口 ──────────────────────────────────────────────────
// 触发全量扫描并自动发送预警（状态变化时）
app.post('/api/bot/alert-scan', (req, res) => {
  try {
    const { channels, alerts } = botMonitor.scanAllAndAlert();
    res.json({ ok: true, scanned: channels.length, alerts });
  } catch (e) {
    res.json({ ok: false, error: e.message });
  }
});

// 对指定频道强制发送预警（忽略去重，用于手动测试）
app.post('/api/bot/alert/:channelId', (req, res) => {
  try {
    const result = botMonitor.forceAlert(req.params.channelId);
    res.json(result);
  } catch (e) {
    res.json({ ok: false, error: e.message });
  }
});

// 查看当前预警状态记录
app.get('/api/bot/alert-state', (req, res) => {
  res.json(botMonitor.getAlertState());
});

// ─── 悟空 Token 鉴权（外网访问保护）─────────────────────────────
const WUKONG_TOKEN = 'wk2026';
function wukongAuth(req, res, next) {
  // 通过 Cloudflare Tunnel 的请求带有 cf-connecting-ip header
  const isTunnel = !!req.headers['cf-connecting-ip'];
  if (!isTunnel) return next(); // 本地直连免验证
  // 外网需要 token
  const token = req.query.token || req.headers['x-wukong-token'];
  if (token === WUKONG_TOKEN) return next();
  return res.status(403).json({ error: 'forbidden' });
}

// ─── 悟空邀请码监控 ────────────────────────────────────────────
app.post('/api/wukong/ocr', wukongAuth, async (req, res) => {
  const { imageUrl } = req.body || {};
  if (!imageUrl) return res.status(400).json({ error: 'missing imageUrl' });
  try {
    const rawText = await wukongMonitor.ocrInviteCode(imageUrl);
    // 从 OCR 文本中提取邀请码：取"邀请码"或冒号后的第一段文字
    let inviteCode = rawText;
    const m = rawText.match(/邀请码[：:]\s*(.+)/);
    if (m) inviteCode = m[1].split('\n')[0].trim();
    res.json({ ok: true, inviteCode, rawText });
  } catch (e) {
    res.json({ ok: false, error: e.message, inviteCode: '' });
  }
});

app.get('/api/wukong/state', wukongAuth, (req, res) => {
  res.json(wukongMonitor.getMonitorState());
});

app.post('/api/wukong/check', wukongAuth, async (req, res) => {
  try {
    const result = await wukongMonitor.checkOnce();
    res.json(result);
  } catch (e) {
    res.json({ status: 'error', message: e.message });
  }
});

app.post('/api/wukong/enable', wukongAuth, (req, res) => {
  res.json(wukongMonitor.enableMonitor());
});

app.post('/api/wukong/disable', wukongAuth, (req, res) => {
  res.json(wukongMonitor.disableMonitor());
});

app.get('/wukong', (req, res) => res.sendFile('public/wukong.html', { root: __dirname }));
app.get('/bot', (req, res) => res.sendFile('public/bot.html', { root: __dirname }));
app.get('/elon2', (req, res) => res.sendFile('public/elon2.html', { root: __dirname }));
app.get('/elon', async (req, res) => {
  const fs2 = require('fs');
  const https2 = require('https');
  let html = fs2.readFileSync(path.join(__dirname, 'public/elon-tracker.html'), 'utf8');
  // Server-side pre-fetch xtracker data and inject as window.__SSR_DATA__
  try {
    const data = await new Promise((resolve, reject) => {
      const url = 'https://xtracker.polymarket.com/api/trackings/d861bacb-6108-45d6-9a14-47b9e58ea095?includeStats=true';
      https2.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 8000 }, (r) => {
        let d = '';
        r.on('data', c => d += c);
        r.on('end', () => { try { resolve(JSON.parse(d)); } catch(e) { reject(e); } });
      }).on('error', reject).on('timeout', () => reject(new Error('timeout')));
    });
    // Inject SSR data as window var (for chart updates)
    const ssrScript = `<script>window.__SSR_DATA__ = ${JSON.stringify(data)};</script>`;
    html = html.replace('</head>', ssrScript + '\n</head>');
    // Also directly replace placeholder values in HTML for instant render
    const stats = data.data && data.data.stats;
    if (stats) {
      const total = stats.total || 0;
      const CYCLE_START = new Date('2026-03-20T16:00:00Z');
      const now2 = new Date();
      const daysElapsed = Math.max(0, (now2 - CYCLE_START) / (1000*60*60*24));
      const pct = Math.min(100, daysElapsed / 7 * 100);
      const pace = daysElapsed > 0 ? Math.round(total / daysElapsed * 7) : 0;
      html = html.replace(
        '<div class="stat-value" id="cur-total">—</div>',
        `<div class="stat-value" id="cur-total">${total}</div>`
      );
      html = html.replace(
        /id="cur-days">.*?<\/div>/,
        `id="cur-days">${daysElapsed.toFixed(1)} / 7 天</div>`
      );
      html = html.replace(
        /id="progress-pct">.*?%/,
        `id="progress-pct">${pct.toFixed(1)}%`
      );
      html = html.replace(
        /id="progress-fill" style="width: *0?%/,
        `id="progress-fill" style="width: ${pct.toFixed(1)}%`
      );
      // Pre-calculate day5 estimate and update input default value
      const day5Est = Math.min(449, Math.max(100, Math.round(total / daysElapsed * 5)));
      html = html.replace(
        /id="day5input" value="[0-9]+"/,
        `id="day5input" value="${day5Est}"`
      );
      // SSR prediction result
      const COND_TABLE_SSR = [
        {day5min:100,day5max:149,mean:194,ciLow:130,ciHigh:258},
        {day5min:150,day5max:199,mean:265,ciLow:181,ciHigh:349},
        {day5min:200,day5max:249,mean:315,ciLow:231,ciHigh:399},
        {day5min:250,day5max:299,mean:379,ciLow:295,ciHigh:463},
        {day5min:300,day5max:349,mean:427,ciLow:307,ciHigh:547},
        {day5min:350,day5max:399,mean:518,ciLow:428,ciHigh:608},
        {day5min:400,day5max:449,mean:555,ciLow:503,ciHigh:607},
      ];
      const predRow = COND_TABLE_SSR.find(r => day5Est >= r.day5min && day5Est <= r.day5max);
      if (predRow) {
        html = html.replace(
          'id="pred-result"></span>',
          `id="pred-result">📍 Day7 预测均值: <strong style="color:var(--green);font-size:16px;">${predRow.mean}</strong> 条 | 95%CI: [${predRow.ciLow}, ${predRow.ciHigh}]</span>`
        );
        // Update the prediction summary card
        html = html.replace(
          /<div class="stat-value" [^>]*>—<\/div>\s*<div class="stat-sub"[^>]*>95% CI: —<\/div>/,
          `<div class="stat-value" style="color:var(--green);font-size:36px;font-weight:900;">${predRow.mean}</div><div class="stat-sub" id="cur-pred-ci">95% CI: [${predRow.ciLow}, ${predRow.ciHigh}]</div>`
        );
      }
    }
  } catch(e) {
    console.error('[SSR] xtracker prefetch failed:', e.message);
  }
  res.setHeader('Content-Type', 'text/html');
  res.send(html);
});

// Elon Poly daemon status API
app.get('/api/elon-poly/status', async (req, res) => {
  try {
    const fs = require('fs');
    const { execSync } = require('child_process');

    // 策略引擎状态
    let strategy = {};
    try { strategy = JSON.parse(fs.readFileSync('/tmp/elon_strategy.json', 'utf8')); } catch(e) {}

    // daemon 进程状态
    let daemonRunning = false;
    let daemonPid = null;
    try {
      daemonPid = fs.readFileSync('/tmp/elon_poly_daemon.pid', 'utf8').trim();
      execSync(`kill -0 ${daemonPid} 2>/dev/null`);
      daemonRunning = true;
    } catch(e) { daemonRunning = false; }

    // systemd 状态
    let systemdStatus = 'unknown';
    try {
      const out = execSync('systemctl is-active elon-poly 2>/dev/null').toString().trim();
      systemdStatus = out;
    } catch(e) { systemdStatus = 'inactive'; }

    // 最近决策日志
    let recentDecisions = [];
    try {
      const log = fs.readFileSync('/root/.openclaw/workspace/projects/elon-poly/decision_log.jsonl', 'utf8');
      const lines = log.trim().split('\n').slice(-10);
      recentDecisions = lines.map(l => { try { return JSON.parse(l); } catch(e) { return null; } }).filter(Boolean);
    } catch(e) {}

    // orderbook 数据点数
    let obCount = 0;
    try {
      const ob = fs.readFileSync('/root/.openclaw/workspace/projects/elon-poly/orderbook_snapshots.jsonl', 'utf8');
      obCount = ob.trim().split('\n').length;
    } catch(e) {}

    res.json({
      daemon: { running: daemonRunning, pid: daemonPid, systemd: systemdStatus },
      strategy: strategy,
      dataCollection: { orderbookSnapshots: obCount },
      recentDecisions: recentDecisions,
    });
  } catch(e) { res.status(500).json({ error: e.message }); }
});

// Proxy: Gamma API for Polymarket event data
app.get('/api/xtracker/gamma/:eventId', async (req, res) => {
  try {
    const eventId = req.params.eventId;
    const https = require('https');
    const url = `https://gamma-api.polymarket.com/events/${eventId}`;
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (r) => {
      let data = '';
      r.on('data', c => data += c);
      r.on('end', () => {
        try { res.json(JSON.parse(data)); } catch(e) { res.status(500).json({ error: 'parse error' }); }
      });
    }).on('error', e => res.status(500).json({ error: e.message }));
  } catch(e) { res.status(500).json({ error: e.message }); }
});

// Proxy: xtracker API (avoids CORS/GFW issues from browser)
app.get('/api/xtracker/tracking', async (req, res) => {
  try {
    const id = req.query.id || 'd861bacb-6108-45d6-9a14-47b9e58ea095';
    const https = require('https');
    const url = `https://xtracker.polymarket.com/api/trackings/${id}?includeStats=true`;
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (r) => {
      let data = '';
      r.on('data', c => data += c);
      r.on('end', () => {
        try { res.json(JSON.parse(data)); } catch(e) { res.status(500).json({ error: 'parse error', raw: data.slice(0,200) }); }
      });
    }).on('error', e => res.status(500).json({ error: e.message }));
  } catch(e) { res.status(500).json({ error: e.message }); }
});

// Proxy: elon live state from local trader
app.get('/api/elon/state', (req, res) => {
  try {
    const state = JSON.parse(fs.readFileSync('/tmp/elon_trader_state.json', 'utf8'));
    res.json(state);
  } catch(e) { res.status(500).json({ error: e.message }); }
});

// ── Web Scraper ──────────────────────────────────────────────────────────────
// Read API keys from ~/.openclaw/.env — supports multiple FIRECRAWL keys for rotation
const _envKeys = (() => { try {
  const c = fs.readFileSync(path.join(process.env.HOME, '.openclaw', '.env'), 'utf-8');
  const get = (k) => { const m = c.match(new RegExp(`^${k}=(.+)$`, 'm')); return m ? m[1].trim() : ''; };
  // Collect all FIRECRAWL_API_KEY, FIRECRAWL_API_KEY2, FIRECRAWL_API_KEY3, etc.
  const fcKeys = [...c.matchAll(/^FIRECRAWL_API_KEY\d*=(.+)$/gm)].map(m => m[1].trim()).filter(Boolean);
  return { firecrawlKeys: fcKeys, tavily: get('TAVILY_API_KEY_1') };
} catch { return { firecrawlKeys: [], tavily: '' }; } })();

const FIRECRAWL_KEYS = _envKeys.firecrawlKeys.length ? _envKeys.firecrawlKeys : (process.env.FIRECRAWL_API_KEY ? [process.env.FIRECRAWL_API_KEY] : []);
let _fcKeyIndex = 0;
function getFirecrawlKey() {
  if (FIRECRAWL_KEYS.length === 0) return '';
  const key = FIRECRAWL_KEYS[_fcKeyIndex % FIRECRAWL_KEYS.length];
  _fcKeyIndex++;
  return key;
}
const TAVILY_KEY = process.env.TAVILY_API_KEY_1 || _envKeys.tavily;

function sanitizeFilename(title) {
  return title.replace(/[\/\\:*?"<>|]/g, '_').replace(/\s+/g, ' ').trim().slice(0, 100);
}

// Scrape via Firecrawl + get remaining credits — rotates keys automatically
async function scrapeFirecrawl(url, cookie) {
  const key = getFirecrawlKey();
  const scrapeBody = { url, formats: ['markdown'], waitFor: 5000 };
  if (cookie) scrapeBody.headers = { Cookie: cookie };
  const [scrapeResp, creditResp] = await Promise.all([
    fetch('https://api.firecrawl.dev/v1/scrape', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(scrapeBody),
      signal: AbortSignal.timeout(60000),
    }),
    fetch('https://api.firecrawl.dev/v1/team/credit-usage', {
      headers: { 'Authorization': `Bearer ${key}` },
      signal: AbortSignal.timeout(5000),
    }).catch(() => null),
  ]);
  const data = await scrapeResp.json();
  if (!scrapeResp.ok || !data.success) throw new Error(data.error || `Firecrawl 错误 (${scrapeResp.status})`);
  let creditsRemaining = null;
  if (creditResp?.ok) {
    const cd = await creditResp.json();
    creditsRemaining = cd.data?.remaining_credits ?? null;
  }
  const markdown = data.data?.markdown || '';
  const rawTitle = data.data?.metadata?.title || '';
  const title = rawTitle.replace(/\s*[-–|].*?(Feishu|Docs|飞书).*$/i, '').trim() || 'untitled';
  return { title, markdown, creditsUsed: 1, creditsRemaining };
}

// Scrape via Tavily (MiniMax framework, Claude corrected)
async function scrapeTavily(url) {
  const resp = await fetch('https://api.tavily.com/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: TAVILY_KEY, urls: [url] }),
    signal: AbortSignal.timeout(60000),
  });
  const data = await resp.json();
  const result = data.results?.[0];
  if (!result) throw new Error(data.error || 'Tavily 未返回结果');
  const content = result.raw_content || result.content || '';
  const titleMatch = content.match(/^#\s+(.+)$/m);
  const title = titleMatch ? titleMatch[1].trim() : 'untitled';
  return { title, markdown: content, creditsUsed: 1, creditsRemaining: null };
}

// Download images from markdown into {articleDir}/images/, rewrite to relative paths
async function downloadImagesToDir(markdown, articleDir) {
  const imagesDir = path.join(articleDir, 'images');
  const imgRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  const matches = [...markdown.matchAll(imgRegex)];
  const httpImages = matches.filter(m => /^https?:\/\//.test(m[2]));
  if (httpImages.length === 0) return { markdown, imageCount: 0 };

  fs.mkdirSync(imagesDir, { recursive: true });
  let newMd = markdown;
  let downloaded = 0;

  for (let i = 0; i < httpImages.length; i++) {
    const [fullMatch, alt, imgUrl] = httpImages[i];
    try {
      const resp = await fetch(imgUrl, { signal: AbortSignal.timeout(15000) });
      if (!resp.ok) continue;
      const ct = resp.headers.get('content-type') || '';
      const ext = ct.includes('png') ? '.png' : ct.includes('gif') ? '.gif' : ct.includes('webp') ? '.webp' : '.jpg';
      const filename = `img_${String(i + 1).padStart(3, '0')}${ext}`;
      const buffer = Buffer.from(await resp.arrayBuffer());
      fs.writeFileSync(path.join(imagesDir, filename), buffer);
      newMd = newMd.split(fullMatch).join(`![${alt}](./images/${filename})`);
      downloaded++;
    } catch { /* skip failed images */ }
  }
  return { markdown: newMd, imageCount: downloaded };
}

app.get('/scraper', (req, res) => res.sendFile('public/scraper.html', { root: __dirname }));

// Image proxy — bypass referer-based hotlink protection, auto-upgrade http→https
app.get('/api/scraper/imgproxy', async (req, res) => {
  let url = req.query.url;
  if (!url) return res.status(400).send('missing url');
  // Try https first (many CDNs reject http but accept https)
  const tryUrls = [url];
  if (url.startsWith('http://')) tryUrls.unshift(url.replace('http://', 'https://'));
  for (const u of tryUrls) {
    try {
      const r = await fetch(u, { signal: AbortSignal.timeout(15000) });
      if (r.ok) {
        res.set('Content-Type', r.headers.get('content-type') || 'image/jpeg');
        res.set('Cache-Control', 'public, max-age=86400');
        return res.send(Buffer.from(await r.arrayBuffer()));
      }
    } catch {}
  }
  res.status(502).send('proxy error');
});

// Quota check — queries all Firecrawl keys and sums remaining credits
app.get('/api/scraper/quota', async (req, res) => {
  const result = {};
  try {
    if (FIRECRAWL_KEYS.length > 0) {
      const checks = await Promise.all(FIRECRAWL_KEYS.map(async (key) => {
        try {
          const r = await fetch('https://api.firecrawl.dev/v1/team/credit-usage', {
            headers: { 'Authorization': `Bearer ${key}` },
            signal: AbortSignal.timeout(5000),
          });
          if (r.ok) { const d = await r.json(); return d.data?.remaining_credits ?? 0; }
          return 0;
        } catch { return 0; }
      }));
      const total = checks.reduce((a, b) => a + b, 0);
      result.firecrawl = `${FIRECRAWL_KEYS.length} 个 key，共剩余 ${total} credits`;
    }
  } catch { result.firecrawl = '查询超时'; }
  try {
    if (TAVILY_KEY) {
      result.tavily = '按量计费（$5/1000次）';
    }
  } catch {}
  res.json(result);
});

app.post('/api/scraper/scrape', async (req, res) => {
  const { url, cookie } = req.body;
  if (!url) return res.status(400).json({ error: '请输入 URL' });

  const isWechat = /mp\.weixin\.qq\.com/.test(url);

  try {
    let result;
    if (isWechat) {
      if (!TAVILY_KEY) return res.status(500).json({ error: 'TAVILY_API_KEY 未配置（微信需要 Tavily）' });
      result = await scrapeTavily(url);
    } else {
      if (FIRECRAWL_KEYS.length === 0) return res.status(500).json({ error: 'FIRECRAWL_API_KEY 未配置' });
      result = await scrapeFirecrawl(url, cookie);
    }

    res.json({ ...result, url, engine: isWechat ? 'tavily' : 'firecrawl' });
  } catch (err) {
    if (err.name === 'TimeoutError') return res.status(504).json({ error: '抓取超时' });
    res.status(500).json({ error: err.message });
  }
});

// Save: create {title}/ directory with index.md + images/
app.post('/api/scraper/save', async (req, res) => {
  const { markdown, title, saveDir } = req.body;
  if (!markdown || !title) return res.status(400).json({ error: '缺少 markdown 或 title' });
  const baseDir = (saveDir || '').replace(/^~/, process.env.HOME) || path.join(process.env.HOME, '.openclaw', 'docs');
  const articleDir = path.join(baseDir, sanitizeFilename(title));
  try {
    fs.mkdirSync(articleDir, { recursive: true });
    // Clean blob: URLs, then download real images
    const cleanedMd = markdown.replace(/!\[([^\]]*)\]\(blob:[^)]+\)/g, '*[图片无法提取]*');
    const imgResult = await downloadImagesToDir(cleanedMd, articleDir);
    // Write index.md
    const mdPath = path.join(articleDir, 'index.md');
    fs.writeFileSync(mdPath, imgResult.markdown, 'utf-8');
    res.json({ success: true, filepath: mdPath, imageCount: imgResult.imageCount, articleDir });
  } catch (err) {
    res.status(500).json({ error: `保存失败: ${err.message}` });
  }
});

// Export as self-contained HTML with base64 images (MiniMax draft, Claude reviewed)
app.post('/api/scraper/export-html', async (req, res) => {
  const { markdown, title } = req.body;
  if (!markdown || !title) return res.status(400).json({ error: '缺少 markdown 或 title' });

  // Simple markdown→html (no external deps)
  function md2html(md) {
    let h = md;
    // Code blocks first (before escaping)
    const codeBlocks = [];
    h = h.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const escaped = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      codeBlocks.push(`<pre><code>${escaped.trim()}</code></pre>`);
      return `%%CODEBLOCK_${codeBlocks.length - 1}%%`;
    });
    h = h.replace(/`([^`]+)`/g, (_, c) => `<code>${c.replace(/</g,'&lt;')}</code>`);
    // Remove blob: images (can't be downloaded), keep real URLs
    h = h.replace(/!\[([^\]]*)\]\(blob:[^)]+\)/g, '<em style="color:#999">[图片无法提取]</em>');
    h = h.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
    h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    h = h.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    h = h.replace(/(<li>.*<\/li>\n?)+/gs, '<ul>$&</ul>');
    h = h.replace(/^---$/gm, '<hr>');
    // Paragraphs
    h = h.split(/\n\n+/).map(p => {
      p = p.trim();
      if (!p || /^<(h[1-6]|ul|ol|pre|hr|li|img)/.test(p) || /^%%CODEBLOCK/.test(p)) return p;
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('\n');
    // Restore code blocks
    codeBlocks.forEach((block, i) => { h = h.replace(`%%CODEBLOCK_${i}%%`, block); });
    return h;
  }

  // Download image → base64 data URI
  async function imgToBase64(url) {
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(15000) });
      if (!r.ok) return url;
      const mime = r.headers.get('content-type') || 'image/jpeg';
      const b64 = Buffer.from(await r.arrayBuffer()).toString('base64');
      return `data:${mime};base64,${b64}`;
    } catch { return url; }
  }

  try {
    let html = md2html(markdown);
    // Collect and replace all image srcs in parallel
    const imgMatches = [...html.matchAll(/src="(https?:\/\/[^"]+)"/g)];
    if (imgMatches.length > 0) {
      const urls = imgMatches.map(m => m[1]);
      const b64s = await Promise.all(urls.map(imgToBase64));
      urls.forEach((u, i) => { html = html.split(`src="${u}"`).join(`src="${b64s[i]}"`); });
    }

    const fullHtml = `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${title.replace(/</g,'&lt;')}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7;max-width:860px;margin:0 auto;padding:24px 40px;color:#24292e}
h1,h2,h3{margin-top:24px;margin-bottom:12px;font-weight:600}
h1{font-size:2em;border-bottom:1px solid #eaecef;padding-bottom:.3em}
h2{font-size:1.5em;border-bottom:1px solid #eaecef;padding-bottom:.3em}
img{max-width:100%;height:auto;display:block;margin:16px 0;border-radius:4px}
code{background:rgba(27,31,35,.05);padding:.2em .4em;border-radius:3px;font-family:monospace;font-size:90%}
pre{background:#f6f8fa;padding:16px;border-radius:6px;overflow-x:auto}
pre code{background:0;padding:0}
a{color:#0366d6}
ul,ol{padding-left:2em}
hr{height:.25em;background:#e1e4e8;border:0;margin:24px 0}
p{margin:0 0 16px}
</style></head><body>
${html}
</body></html>`;

    res.json({ html: fullHtml, filename: sanitizeFilename(title) + '.html' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Save HTML file to server
app.post('/api/scraper/save-html', (req, res) => {
  const { html, title, saveDir } = req.body;
  if (!html || !title) return res.status(400).json({ error: '缺少 html 或 title' });
  const baseDir = (saveDir || '').replace(/^~/, process.env.HOME) || path.join(process.env.HOME, '.openclaw', 'docs');
  const filename = sanitizeFilename(title) + '.html';
  const filepath = path.join(baseDir, filename);
  try {
    fs.mkdirSync(baseDir, { recursive: true });
    fs.writeFileSync(filepath, html, 'utf-8');
    res.json({ success: true, filepath, filename });
  } catch (err) {
    res.status(500).json({ error: `保存失败: ${err.message}` });
  }
});

// ══════════════════════════════════════════════════════════════════════════════
// 后台任务管理 API
// ══════════════════════════════════════════════════════════════════════════════

// 列出所有后台任务
app.get('/api/tasks', (req, res) => res.json(taskMgr.listTasks()));

// 注册任务
app.post('/api/tasks', (req, res) => {
  try { res.json(taskMgr.registerTask(req.body)); }
  catch(e) { res.status(400).json({ error: e.message }); }
});

// 更新任务配置
app.put('/api/tasks/:id', (req, res) => {
  try {
    const existing = taskMgr.listTasks().find(t => t.id === req.params.id);
    if (!existing) return res.status(404).json({ error: 'not found' });
    res.json(taskMgr.registerTask({ ...existing, ...req.body, id: req.params.id }));
  } catch(e) { res.status(400).json({ error: e.message }); }
});

// 启动任务
app.post('/api/tasks/:id/start', (req, res) => {
  try { res.json(taskMgr.startTask(req.params.id)); }
  catch(e) { res.status(400).json({ error: e.message }); }
});

// 停止任务
app.post('/api/tasks/:id/stop', (req, res) => {
  taskMgr.stopTask(req.params.id);
  res.json({ ok: true });
});

// 删除任务
app.delete('/api/tasks/:id', (req, res) => {
  taskMgr.stopTask(req.params.id);
  db.prepare('DELETE FROM bg_tasks WHERE id=?').run(req.params.id);
  res.json({ ok: true });
});

// 获取任务日志
app.get('/api/tasks/:id/log', (req, res) => {
  const lines = parseInt(req.query.lines) || 100;
  res.json({ log: taskMgr.getTaskLog(req.params.id, lines) });
});

// ── Bitfinex 状态 & 配置 ──────────────────────────────────────────────────────
app.get('/api/bitfinex/status', (req, res) => {
  const f = '/tmp/bitfinex_status.json';
  if (!fs.existsSync(f)) return res.json({ error: 'no data yet' });
  try { res.json(JSON.parse(fs.readFileSync(f))); }
  catch { res.json({ error: 'parse error' }); }
});

app.get('/api/bitfinex/config', (req, res) => {
  const f = '/tmp/bitfinex_config.json';
  if (!fs.existsSync(f)) return res.json({});
  try { res.json(JSON.parse(fs.readFileSync(f))); }
  catch { res.json({}); }
});

app.post('/api/bitfinex/config', (req, res) => {
  const f = '/tmp/bitfinex_config.json';
  let cur = {};
  if (fs.existsSync(f)) { try { cur = JSON.parse(fs.readFileSync(f)); } catch {} }
  const updated = { ...cur, ...req.body };
  fs.writeFileSync(f, JSON.stringify(updated, null, 2));
  res.json(updated);
});

// ── 任务页面 ──────────────────────────────────────────────────────────────────
app.get('/tasks', (req, res) => res.sendFile('public/tasks.html', { root: __dirname }));

// ── 启动时注册 Bitfinex 守护任务并恢复 ────────────────────────────────────────
const BITFINEX_TASK_ID = 'bitfinex-monitor';
taskMgr.registerTask({
  id:           BITFINEX_TASK_ID,
  name:         'Bitfinex USDT 监控',
  description:  '每10分钟拉取 UST/USD 现货价格和借贷利率，超阈值推送 Telegram',
  command:      'python3',
  args:         ['/root/.openclaw/workspace/projects/bitfinex/bitfinex_daemon.py'],
  cwd:          '/root/.openclaw/workspace/projects/bitfinex',
  env_json:     null,
  interval_sec: 1,   // 守护进程自带循环，exit后1秒重拉起
  enabled:      1,
});
taskMgr.restoreEnabledTasks();


// ── Research: 一键采集 API ────────────────────────────────────────────────────
let collectRunning = false;
app.get('/api/research/list', (req, res) => {
  try {
    const files = require('fs').readdirSync('/root/.openclaw/workspace/dashboard-mvp/data/research')
      .filter(f => f.startsWith('raw_') && f.endsWith('.json'))
      .sort((a,b)=>require('fs').statSync('/root/.openclaw/workspace/dashboard-mvp/data/research/'+b).mtimeMs - require('fs').statSync('/root/.openclaw/workspace/dashboard-mvp/data/research/'+a).mtimeMs); // 按修改时间倒序
    res.json({ ok: true, files });
  } catch(e) { res.json({ ok: false, files: [], error: e.message }); }
});
app.get('/api/research/latest', (req, res) => {
  const fname = req.query.file;
  try {
    const dir = '/root/.openclaw/workspace/dashboard-mvp/data/research';
    const fs = require('fs');
    const files = fs.readdirSync(dir)
      .filter(f => f.startsWith('raw_') && f.endsWith('.json'))
      .sort((a,b)=>fs.statSync(dir+'/'+b).mtimeMs - fs.statSync(dir+'/'+a).mtimeMs); // 按修改时间倒序
    const target = fname && files.includes(fname) ? fname : files[0];
    if (!target) return res.json({ ok: false, error: 'no data' });
    const raw = JSON.parse(fs.readFileSync(dir + '/' + target, 'utf8'));
    // 兼容旧格式：补全缺失字段
    if (!raw.time) {
      const m = (raw.date||'').match(/(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})/);
      if (m) { raw.date = m[1]; raw.time = m[2] + ' BJT'; }
    }
    if (!raw.stats) raw.stats = { total: (raw.xhs||[]).length+(raw.reddit||[]).length+(raw.twitter||[]).length, xhs:(raw.xhs||[]).length, reddit:(raw.reddit||[]).length, twitter:(raw.twitter||[]).length };
    if (raw.twitterOnline === undefined) raw.twitterOnline = (raw.twitter||[]).length > 0;
    res.json({ ok: true, file: target, data: raw });
  } catch(e) { res.json({ ok: false, error: e.message }); }
});
app.post('/api/research/collect', (req, res) => {
  if (collectRunning) return res.json({ ok: false, error: '采集中，请稍候' });
  collectRunning = true;
  res.json({ ok: true, msg: '采集已启动，约3分钟后刷新（采集→AI分析→完成）' });
  const cp = require('child_process');
  cp.execFile('python3', ['/root/.openclaw/workspace/projects/daily-research/collect.py'],
    { timeout: 180000, env: Object.assign({}, process.env) },
    function(err, stdout, stderr) {
      console.log('[research-collect]', err ? err.message : 'OK');
      // 采集完后自动运行 AI 分析（enrich），生成 source_urls / signals / topics
      cp.execFile('python3', ['/root/.openclaw/workspace/dashboard-mvp/scripts/enrich-research.py'],
        { timeout: 120000, env: Object.assign({}, process.env) },
        function(err2) {
          collectRunning = false;
          console.log('[research-enrich]', err2 ? err2.message : 'OK');
        }
      );
    }
  );
});
app.get('/api/research/status', (req, res) => res.json({ running: collectRunning }));

// ── Research settings ──────────────────────────────────────────────────────────
const SETTINGS_FILE = '/root/.openclaw/workspace/dashboard-mvp/data/settings.json';
function readSettings() {
  try { return JSON.parse(require('fs').readFileSync(SETTINGS_FILE, 'utf8')); }
  catch { return { telegram_notify: true }; }
}
function writeSettings(s) {
  require('fs').writeFileSync(SETTINGS_FILE, JSON.stringify(s, null, 2));
}
app.get('/api/research/settings', (req, res) => {
  res.json({ ok: true, settings: readSettings() });
});
app.post('/api/research/settings', (req, res) => {
  try {
    const current = readSettings();
    const updated = Object.assign(current, req.body);
    writeSettings(updated);
    res.json({ ok: true, settings: updated });
  } catch(e) { res.json({ ok: false, error: e.message }); }
});

app.listen(PORT, () => console.log(`Dashboard running on http://localhost:${PORT}`));