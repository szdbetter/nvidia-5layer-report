const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

const dbPath = path.join(dataDir, 'dashboard.db');
const db = new Database(dbPath);

db.pragma('journal_mode = WAL');

db.exec(`
CREATE TABLE IF NOT EXISTS missions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  owner TEXT,
  sponsor TEXT,
  priority TEXT,
  status TEXT,
  roi_hypothesis TEXT,
  mission_text TEXT,
  deliverables TEXT,
  non_goals TEXT,
  deadline TEXT,
  acceptance_criteria TEXT,
  evidence_requirements TEXT,
  failure_conditions TEXT,
  risk_level TEXT,
  current_phase TEXT,
  next_action TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS mission_resources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  resource_type TEXT,
  resource_name TEXT,
  details TEXT
);

CREATE TABLE IF NOT EXISTS mission_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  actor_type TEXT,
  actor_name TEXT,
  responsibility TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS mission_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  event_type TEXT,
  event_text TEXT,
  source TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  artifact_type TEXT,
  title TEXT,
  path_or_ref TEXT,
  summary TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS runtime_entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  entity_type TEXT,
  entity_key TEXT,
  label TEXT,
  status TEXT,
  last_seen_at TEXT,
  last_summary TEXT
);

CREATE TABLE IF NOT EXISTS risks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  risk_type TEXT,
  severity TEXT,
  description TEXT,
  mitigation TEXT,
  escalated INTEGER,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id TEXT,
  memory_query TEXT,
  memory_summary TEXT,
  recall_score REAL,
  recall_status TEXT,
  stored_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT,
  target_type TEXT,
  target_id TEXT,
  actor TEXT,
  details TEXT,
  created_at TEXT
);
`);

function seed() {
  const exists = db.prepare('SELECT COUNT(*) AS c FROM missions').get().c;
  if (exists > 0) return;

  const now = new Date().toISOString();
  db.prepare(`INSERT INTO missions (
    id, name, owner, sponsor, priority, status, roi_hypothesis, mission_text, deliverables,
    non_goals, deadline, acceptance_criteria, evidence_requirements, failure_conditions,
    risk_level, current_phase, next_action, created_at, updated_at
  ) VALUES (
    @id, @name, @owner, @sponsor, @priority, @status, @roi_hypothesis, @mission_text, @deliverables,
    @non_goals, @deadline, @acceptance_criteria, @evidence_requirements, @failure_conditions,
    @risk_level, @current_phase, @next_action, @created_at, @updated_at
  )`).run({
    id: 'dashboard',
    name: 'OpenClaw 本地 Dashboard',
    owner: 'Reese',
    sponsor: '岁月',
    priority: 'P0',
    status: 'Active',
    roi_hypothesis: '统一任务中枢可降低目标偏差、证据散落和多 agent 管理损耗。',
    mission_text: '建立一个本地统一任务作战面板，统一展示 Mission Card、任务状态、Agent/节点执行流、证据、风险阻塞、OpenViking 记忆验证。',
    deliverables: '任务总览页、Mission Card详情页、运行态聚合页、Memory验证面板、SQLite状态层、README。',
    non_goals: '第一版不做深度权限系统、多租户和高风险自动执行按钮。',
    deadline: 'MVP ASAP',
    acceptance_criteria: '本地可启动；可查看任务、详情、运行态、记忆状态；有README和基础自测记录。',
    evidence_requirements: '代码、README、可运行页面、启动与接口测试结果。',
    failure_conditions: '无法启动、无法展示核心页面、无状态层、无文档。',
    risk_level: 'medium',
    current_phase: 'Implementation',
    next_action: '完成本地服务、自测、更新项目任务文档。',
    created_at: now,
    updated_at: now
  });

  const resources = db.prepare('INSERT INTO mission_resources (mission_id, resource_type, resource_name, details) VALUES (?, ?, ?, ?)');
  [
    ['dashboard', 'node', 'local-workspace', '本地 Node 服务 + SQLite'],
    ['dashboard', 'tool', 'OpenClaw APIs', '后续接 sessions/process/cron/nodes/memory'],
    ['dashboard', 'model', 'codex', '用于后续 ACP 开发']
  ].forEach(r => resources.run(...r));

  const assignments = db.prepare('INSERT INTO mission_assignments (mission_id, actor_type, actor_name, responsibility, status) VALUES (?, ?, ?, ?, ?)');
  [
    ['dashboard', 'reese', 'Reese', '治理定义、验收、补缺', 'active'],
    ['dashboard', 'fiona', 'Fiona', '后续接入高频扫描与监控流', 'planned'],
    ['dashboard', 'acp', 'Codex', 'MVP 开发实现', 'active']
  ].forEach(a => assignments.run(...a));

  const events = db.prepare('INSERT INTO mission_events (mission_id, event_type, event_text, source, created_at) VALUES (?, ?, ?, ?, ?)');
  [
    ['dashboard', 'created', 'Dashboard 项目立项', 'manual', now],
    ['dashboard', 'memory_write', '方法论与架构原则已写入 OpenViking', 'memory_store', now],
    ['dashboard', 'updated', 'MVP 开发启动', 'acp/codex', now]
  ].forEach(e => events.run(...e));

  const artifacts = db.prepare('INSERT INTO artifacts (mission_id, artifact_type, title, path_or_ref, summary, created_at) VALUES (?, ?, ?, ?, ?, ?)');
  [
    ['dashboard', 'file', 'CEO 立项三问协议', 'memory/projects/dashboard/ceo-intake-protocol.md', '复杂任务强制入口协议', now],
    ['dashboard', 'file', 'Mission Card 标准模板', 'memory/projects/dashboard/mission-card-template.md', '复杂任务统一模板', now],
    ['dashboard', 'file', 'Dashboard 系统设计草案', 'memory/projects/dashboard/dashboard-system-design.md', '本地 Dashboard MVP 架构与页面定义', now],
    ['dashboard', 'file', 'SQLite 最小数据模型', 'memory/projects/dashboard/sqlite-minimal-data-model.md', '任务状态层 schema', now],
    ['dashboard', 'file', 'Gateway 1979 集成方案', 'memory/projects/dashboard/gateway-1979-integration.md', '独立服务 + 单入口反代', now]
  ].forEach(a => artifacts.run(...a));

  const runtime = db.prepare('INSERT INTO runtime_entities (mission_id, entity_type, entity_key, label, status, last_seen_at, last_summary) VALUES (?, ?, ?, ?, ?, ?, ?)');
  [
    ['dashboard', 'session', 'dashboard-mvp', 'Dashboard MVP ACP 会话', 'active', now, '开发中'],
    ['dashboard', 'node', 'fiona-mbp2015', 'Fiona 节点', 'planned', now, '后续接入高频扫描'],
    ['dashboard', 'cron', 'gateway-1979-proxy', 'Gateway 1979 反代集成', 'planned', now, 'MVP 仅设计完成']
  ].forEach(r => runtime.run(...r));

  const risks = db.prepare('INSERT INTO risks (mission_id, risk_type, severity, description, mitigation, escalated, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)');
  [
    ['dashboard', 'architecture', 'medium', '若将 UI 深耦合进 Gateway，会提高迭代风险。', '保持独立服务 + 反代集成。', 0, now],
    ['dashboard', 'scope', 'medium', '若第一版追求过多控制能力，会拖慢落地。', '坚持只读优先，先做可视化与审计。', 0, now]
  ].forEach(r => risks.run(...r));

  const memories = db.prepare('INSERT INTO memories (mission_id, memory_query, memory_summary, recall_score, recall_status, stored_at) VALUES (?, ?, ?, ?, ?, ?)');
  [
    ['dashboard', 'CEO 立项三问 Mission Card Dashboard Gateway 1979', '已可召回 CEO 三问与 Dashboard 架构记忆。', 0.59, 'hit', now],
    ['dashboard', 'Fiona Polymarket 分层治理', '已可召回 Fiona 高频扫描下沉与主脑二次复核方法论。', 0.56, 'hit', now]
  ].forEach(m => memories.run(...m));

  const audit = db.prepare('INSERT INTO audit_logs (action, target_type, target_id, actor, details, created_at) VALUES (?, ?, ?, ?, ?, ?)');
  audit.run('seed', 'mission', 'dashboard', 'system', '初始化 Dashboard MVP 示例数据', now);
}

seed();

module.exports = db;
