/**
 * 后台任务管理器 (non-cron background scripts)
 * 
 * 职责：
 *  - 注册/列出/启停/删除 background script 任务
 *  - 用 child_process.spawn 在后台运行，PID 持久化到 SQLite
 *  - 提供 REST API 给 Dashboard 消费
 */

const { spawn } = require('child_process');
const path = require('path');
const fs   = require('fs');
const db   = require('./db');

// ── 建表 ──────────────────────────────────────────────────────────────────────
db.exec(`
  CREATE TABLE IF NOT EXISTS bg_tasks (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    command     TEXT NOT NULL,       -- e.g. "python3"
    args        TEXT NOT NULL,       -- JSON array
    cwd         TEXT,
    env_json    TEXT,
    interval_sec INTEGER DEFAULT 0,  -- 0 = run-once, >0 = auto-restart interval
    pid         INTEGER,
    status      TEXT DEFAULT 'stopped',  -- running | stopped | error
    last_started TEXT,
    last_error   TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    enabled      INTEGER DEFAULT 1
  )
`);

const processes = {}; // id -> { child, restartTimer }

// ── 工具 ──────────────────────────────────────────────────────────────────────
function row(id) {
  return db.prepare('SELECT * FROM bg_tasks WHERE id=?').get(id);
}

function setStatus(id, status, pid = null, err = null) {
  db.prepare(`UPDATE bg_tasks SET status=?, pid=?, last_error=? WHERE id=?`)
    .run(status, pid, err, id);
}

function isAlive(pid) {
  if (!pid) return false;
  try { process.kill(pid, 0); return true; } catch { return false; }
}

// ── 启动一个任务 ──────────────────────────────────────────────────────────────
function startTask(id) {
  const task = row(id);
  if (!task) throw new Error(`Task ${id} not found`);
  if (!task.enabled) throw new Error(`Task ${id} is disabled`);

  // 如果已经在跑就跳过
  if (processes[id]?.child && isAlive(processes[id].child.pid)) {
    return { already: true, pid: processes[id].child.pid };
  }

  const args   = JSON.parse(task.args || '[]');
  const envAdd = task.env_json ? JSON.parse(task.env_json) : {};
  const cwd    = task.cwd || process.cwd();

  const logFile = `/tmp/bgtask_${id}.log`;
  const out = fs.openSync(logFile, 'a');

  const child = spawn(task.command, args, {
    cwd,
    env:   { ...process.env, ...envAdd },
    stdio: ['ignore', out, out],
    detached: false,
  });

  processes[id] = { child };

  db.prepare(`UPDATE bg_tasks SET status='running', pid=?, last_started=datetime('now'), last_error=null WHERE id=?`)
    .run(child.pid, id);

  child.on('exit', (code) => {
    fs.closeSync(out);
    const task2 = row(id);
    const interval = task2?.interval_sec || 0;

    if (interval > 0 && task2?.enabled) {
      // 自动重启
      setStatus(id, 'restarting', null, code !== 0 ? `exit ${code}` : null);
      const timer = setTimeout(() => startTask(id), interval * 1000);
      processes[id] = { child: null, restartTimer: timer };
    } else {
      setStatus(id, code === 0 ? 'stopped' : 'error', null,
                code !== 0 ? `exit code ${code}` : null);
      delete processes[id];
    }
  });

  return { pid: child.pid };
}

// ── 停止一个任务 ──────────────────────────────────────────────────────────────
function stopTask(id) {
  const entry = processes[id];
  if (entry?.restartTimer) clearTimeout(entry.restartTimer);
  if (entry?.child?.pid && isAlive(entry.child.pid)) {
    try { process.kill(entry.child.pid, 'SIGTERM'); } catch {}
  }
  delete processes[id];
  setStatus(id, 'stopped');
}

// ── 注册任务 ──────────────────────────────────────────────────────────────────
function registerTask({ id, name, description, command, args, cwd, env_json, interval_sec, enabled }) {
  const existing = row(id);
  if (existing) {
    db.prepare(`UPDATE bg_tasks SET name=?,description=?,command=?,args=?,cwd=?,env_json=?,interval_sec=?,enabled=? WHERE id=?`)
      .run(name, description||'', command, JSON.stringify(args||[]), cwd||null, env_json||null, interval_sec||0, enabled!==false?1:0, id);
  } else {
    db.prepare(`INSERT INTO bg_tasks(id,name,description,command,args,cwd,env_json,interval_sec,enabled) VALUES(?,?,?,?,?,?,?,?,?)`)
      .run(id, name, description||'', command, JSON.stringify(args||[]), cwd||null, env_json||null, interval_sec||0, enabled!==false?1:0);
  }
  return row(id);
}

// ── 列出所有任务 ──────────────────────────────────────────────────────────────
function listTasks() {
  const tasks = db.prepare('SELECT * FROM bg_tasks ORDER BY created_at DESC').all();
  return tasks.map(t => {
    const alive = t.pid && isAlive(t.pid);
    const status = alive ? 'running' : (processes[t.id]?.restartTimer ? 'restarting' : t.status);
    return { ...t, status, args: JSON.parse(t.args||'[]'), log_file: `/tmp/bgtask_${t.id}.log` };
  });
}

// ── 读取任务日志 ──────────────────────────────────────────────────────────────
function getTaskLog(id, lines = 50) {
  const logFile = `/tmp/bgtask_${id}.log`;
  if (!fs.existsSync(logFile)) return '';
  try {
    const { execSync } = require('child_process');
    return execSync(`tail -n ${lines} "${logFile}" 2>/dev/null || true`).toString();
  } catch { return ''; }
}

// ── 恢复 enabled 任务（服务重启时调用） ──────────────────────────────────────
function restoreEnabledTasks() {
  const tasks = db.prepare("SELECT * FROM bg_tasks WHERE enabled=1 AND interval_sec>0").all();
  for (const t of tasks) {
    try { startTask(t.id); } catch(e) { console.error(`restore ${t.id}: ${e.message}`); }
  }
}

module.exports = { registerTask, startTask, stopTask, listTasks, getTaskLog, restoreEnabledTasks };
