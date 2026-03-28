/* ── ClawLabs 指挥中心 · app.js ── */

// ── Clock ──────────────────────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('header-time');
  if (!el) return;
  const bj = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  const p = n => String(n).padStart(2, '0');
  el.textContent = `🕐 ${bj.getFullYear()}-${p(bj.getMonth()+1)}-${p(bj.getDate())} ${p(bj.getHours())}:${p(bj.getMinutes())}:${p(bj.getSeconds())} BJT`;
}
setInterval(updateClock, 1000); updateClock();

// ── Helpers ────────────────────────────────────────────────────────────────────
async function api(url, opts = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  return r.json();
}
function fmt(iso) {
  if (!iso) return '—';
  try {
    const bj = new Date(new Date(iso).toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
    const p = n => String(n).padStart(2, '0');
    return `${p(bj.getMonth()+1)}-${p(bj.getDate())} ${p(bj.getHours())}:${p(bj.getMinutes())}`;
  } catch { return iso; }
}
const badge = (txt, type) => `<span class="badge badge-${type}">${txt}</span>`;

// ── Navigation ────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item[data-page]').forEach(item =>
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + item.dataset.page)?.classList.add('active');
  })
);
document.querySelectorAll('.nav-item[data-href]').forEach(item =>
  item.addEventListener('click', () => window.open(item.dataset.href, '_blank'))
);
// Section anchor scroll (sidebar links to #bg-tasks)
document.querySelectorAll('.nav-item[data-section]').forEach(item =>
  item.addEventListener('click', () => {
    document.getElementById(item.dataset.section)?.scrollIntoView({ behavior: 'smooth' });
  })
);

// Submenu toggles
[['nav-polymarket','poly-submenu','poly-arrow'],
 ['nav-ticket','ticket-submenu','ticket-arrow'],
 ['nav-bot','bot-submenu','bot-arrow']].forEach(([navId, menuId, arrowId]) => {
  document.getElementById(navId)?.addEventListener('click', () => {
    const m = document.getElementById(menuId);
    const a = document.getElementById(arrowId);
    const open = m.style.display !== 'none';
    m.style.display = open ? 'none' : 'block';
    a?.classList.toggle('open', !open);
  });
});

// ── Projects ───────────────────────────────────────────────────────────────────
const PROJECT_DESCRIPTIONS = {
  'poly-macro-engine': '🌊 霍尔木兹宏观引擎 — 美伊战争险 + JMIC 通行量',
  'dashboard': '🏢 ClawLabs 指挥中心',
};

async function loadProjects() {
  try {
    const projects = await api('/api/projects');
    const list = Array.isArray(projects) ? projects : (projects.projects || []);
    document.getElementById('stat-projects').textContent = list.length;
    const totalTodo = list.reduce((s, p) => s + (p.taskTodo || 0), 0);
    const openIssues = list.reduce((s, p) => s + (p.openIssues || 0), 0);
    document.getElementById('stat-tasks').textContent = totalTodo;
    document.getElementById('stat-issues').textContent = openIssues;

    const grid = document.getElementById('project-grid');
    if (!list.length) { grid.innerHTML = '<div class="loading-placeholder">暂无项目数据</div>'; return; }
    grid.innerHTML = list.map(p => {
      const pct = p.pct || 0;
      const colorCls = pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger';
      const desc = PROJECT_DESCRIPTIONS[p.id] || PROJECT_DESCRIPTIONS[p.name] || p.description || '—';
      const statusBadge = !p.taskTodo && !p.taskDone
        ? badge('无任务','default')
        : p.taskTodo === 0
        ? badge('✅ 已完成','success')
        : badge(`🔄 进行中 ${p.taskTodo}项`,'blue');
      const enterBtn = (p.id === 'poly-macro-engine' || p.name === 'poly-macro-engine')
        ? '<button class="btn-enter" onclick="window.open(\'/macro\',\'_blank\')">进入 →</button>' : '';
      return `<div class="project-card">
        <div class="project-card-header"><div class="project-name">${p.name || p.id}</div></div>
        <div class="project-desc">${desc}</div>
        <div class="project-progress-row">
          <div class="progress-bar-wrap"><div class="progress-bar-fill ${colorCls}" style="width:${pct}%"></div></div>
          <div class="progress-text">${pct}% (${p.taskDone||0}/${(p.taskDone||0)+(p.taskTodo||0)})</div>
        </div>
        <div class="project-card-footer">${statusBadge}${enterBtn}</div>
      </div>`;
    }).join('');
  } catch (e) {
    console.error('[loadProjects]', e);
    document.getElementById('project-grid').innerHTML = '<div class="error-state">❌ 数据加载失败</div>';
  }
}

// ── Background Tasks ───────────────────────────────────────────────────────────
async function loadBgTasks() {
  try {
    const tasks = await api('/api/tasks');
    const running = tasks.filter(t => t.status === 'running').length;
    document.getElementById('stat-bg-running').textContent = `${running}/${tasks.length}`;
    document.getElementById('nav-task-badge').textContent = running;
    document.getElementById('nav-task-badge').style.display = running ? '' : 'none';

    const tbody = document.getElementById('bg-task-tbody');
    if (!tasks.length) { tbody.innerHTML = '<tr><td colspan="7" class="table-empty">暂无后台任务</td></tr>'; return; }

    tbody.innerHTML = tasks.map(t => {
      const dotCls = { running: 'dot-running', stopped: 'dot-stopped', error: 'dot-error', restarting: 'dot-restarting' }[t.status] || 'dot-stopped';
      const cmd = [t.command, ...(t.args || [])].join(' ');
      const shortCmd = cmd.length > 36 ? cmd.slice(0, 36) + '…' : cmd;
      const interval = t.interval_sec > 0 ? `${t.interval_sec}s` : '不重启';
      const started = t.last_started ? fmt(t.last_started) : '—';
      const actionBtn = t.status === 'running'
        ? `<button class="btn-danger-sm" onclick="stopBgTask('${t.id}')">停止</button>`
        : `<button class="btn-success-sm" onclick="startBgTask('${t.id}')">启动</button>`;
      return `<tr>
        <td><span class="status-dot ${dotCls}"></span>${t.status}</td>
        <td><strong>${t.name}</strong>${t.description ? `<br><span style="font-size:11px;color:#475569">${t.description}</span>` : ''}</td>
        <td><code style="font-size:11px;color:#94a3b8">${shortCmd}</code></td>
        <td><span class="tag">${interval}</span></td>
        <td style="color:#475569">${t.pid || '—'}</td>
        <td style="color:#475569;font-size:12px">${started}</td>
        <td><div style="display:flex;gap:4px">${actionBtn}
          <button class="btn-ghost-sm" onclick="viewBgTaskLog('${t.id}','${t.name}')">日志</button>
          <button class="btn-ghost-sm" style="color:#ef4444" onclick="deleteBgTask('${t.id}')">删除</button>
        </div></td>
      </tr>`;
    }).join('');
  } catch (e) {
    console.error('[loadBgTasks]', e);
    document.getElementById('bg-task-tbody').innerHTML = '<tr><td colspan="7" class="table-empty error-state">❌ 加载失败</td></tr>';
  }
}

async function startBgTask(id) { await api(`/api/tasks/${id}/start`, { method: 'POST' }); loadBgTasks(); }
async function stopBgTask(id)  { await api(`/api/tasks/${id}/stop`,  { method: 'POST' }); loadBgTasks(); }
async function deleteBgTask(id) {
  if (!confirm(`确认删除任务 ${id}？`)) return;
  await api(`/api/tasks/${id}`, { method: 'DELETE' });
  loadBgTasks();
}
async function viewBgTaskLog(id, name) {
  const d = await api(`/api/tasks/${id}/log?lines=200`);
  const win = window.open('', '_blank', 'width=800,height=600');
  win.document.write(`<pre style="background:#0f1117;color:#94a3b8;padding:20px;font-size:12px;white-space:pre-wrap">${d.log || '（暂无日志）'}</pre>`);
}

// Add Task Modal
function openAddTaskModal() { document.getElementById('add-task-modal').classList.add('open'); }
function closeAddTaskModal() { document.getElementById('add-task-modal').classList.remove('open'); }
async function submitAddTask() {
  const body = {
    id:          document.getElementById('at-id').value.trim(),
    name:        document.getElementById('at-name').value.trim(),
    description: document.getElementById('at-desc').value.trim(),
    command:     document.getElementById('at-cmd').value.trim(),
    args:        document.getElementById('at-args').value.trim().split(/\s+/).filter(Boolean),
    cwd:         document.getElementById('at-cwd').value.trim() || null,
    interval_sec: parseInt(document.getElementById('at-interval').value) || 0,
  };
  if (!body.id || !body.name || !body.command) { alert('ID、名称、命令必填'); return; }
  await api('/api/tasks', { method: 'POST', body: JSON.stringify(body) });
  await api(`/api/tasks/${body.id}/start`, { method: 'POST' });
  closeAddTaskModal();
  loadBgTasks();
}

// ── Cron Tasks ─────────────────────────────────────────────────────────────────
async function loadCrons() {
  try {
    const data = await api('/api/runtime');
    const crons = data.cron || data.crons || data.cronJobs || [];
    const list = Array.isArray(crons) ? crons : Object.values(crons);
    document.getElementById('stat-crons').textContent = list.length;
    const tbody = document.getElementById('cron-tbody');
    if (!list.length) { tbody.innerHTML = '<tr><td colspan="5" class="table-empty">暂无 Cron 任务</td></tr>'; return; }
    tbody.innerHTML = list.map(j => {
      const s = j.lastStatus;
      const sb = s === 'success' ? badge('✅ 成功','success')
               : s === 'error' || s === 'failed' ? badge('❌ 失败','danger')
               : j.enabled === false ? badge('⏸ 已禁用','default')
               : badge('🔄 待运行','blue');
      return `<tr>
        <td>${j.name || j.id || '—'}</td>
        <td>${sb}</td>
        <td>${fmt(j.lastRunAt || j.last_run)}</td>
        <td>${fmt(j.nextRunAt || j.next_run)}</td>
        <td><code style="font-size:11px;color:#475569">${j.schedule || j.cron || '—'}</code></td>
      </tr>`;
    }).join('');

    // System node statuses
    const ov = data.openviking || {};
    document.getElementById('sys-ov').innerHTML = ov.ok ? badge('✅ 在线','success') : badge('— 无数据','default');
    const fiona = data.fiona_daemon || {};
    const fok = fiona.ok || fiona.running || fiona.status === 'ok';
    document.getElementById('sys-fiona').innerHTML = fok ? badge('✅ 在线','success')
      : Object.keys(fiona).length ? badge('❌ 离线','danger') : badge('— 无数据','default');
    const bm = data.bot_monitor;
    document.getElementById('sys-bot').innerHTML = !bm ? badge('— 未运行','default')
      : bm.health === 'ok' ? badge('✅ 正常','success')
      : bm.health === 'warning' ? badge('⚠️ 告警','warning')
      : badge('❌ 降级','danger');
  } catch (e) {
    console.error('[loadCrons]', e);
    document.getElementById('cron-tbody').innerHTML = '<tr><td colspan="5" class="table-empty error-state">❌ 加载失败</td></tr>';
  }
}

// ── Bitfinex Widget ────────────────────────────────────────────────────────────
async function loadBfx() {
  try {
    const [d, cfg] = await Promise.all([api('/api/bitfinex/status'), api('/api/bitfinex/config')]);
    const bfxBadge = document.getElementById('bfx-badge');
    if (d.error) {
      // 判断是否 503 维护
      const is503 = d.error.includes('503') || d.error.includes('521') || d.error.includes('temporarily_unavailable') || d.error.includes('Server Error');
      const errMsg = is503 ? '🔧 官方维护中' : '⚠️ API 异常';
      bfxBadge.innerHTML = `<span style="background:#7c3aed;color:#fff;padding:2px 8px;border-radius:9px;font-size:11px">${errMsg}</span>`;
      document.getElementById('bfx-price').textContent = is503 ? '维护中' : '错误';
      document.getElementById('bfx-price').style.color = '#f59e0b';
      document.getElementById('bfx-rate').textContent = '--';
      document.getElementById('bfx-frr').textContent = '--';
      document.getElementById('bfx-updated').textContent = (d.updated_at || '--') + (is503 ? ' · Bitfinex 官方 503' : '');
      return;
    }
    const { spot = {}, funding = {} } = d;
    const priceEl = document.getElementById('bfx-price');
    priceEl.textContent = spot.last ? spot.last.toFixed(5) : '--';
    priceEl.style.color = spot.last > (cfg.price_alert_above || 1.0002) ? '#ef4444' : '#22c55e';
    const rateEl = document.getElementById('bfx-rate');
    rateEl.textContent = funding.ask_daily ? funding.ask_daily.toFixed(8) : '--';
    rateEl.style.color = funding.ask_daily > (cfg.rate_alert_above || 0.00045) ? '#ef4444' : '#e2e8f0';
    document.getElementById('bfx-frr').textContent = funding.frr_annual_pct ? `${funding.frr_annual_pct}%` : '--';
    document.getElementById('bfx-updated').textContent = d.updated_at || '--';
    bfxBadge.innerHTML = d.alerts?.length ? badge(`🚨 ${d.alerts.length}条告警`,'danger') : badge('✓ 正常','success');
    // Bitfinex daemon status
    const tasks = await api('/api/tasks');
    const bfxTask = tasks.find(t => t.id === 'bitfinex-monitor');
    document.getElementById('sys-bfx-daemon').innerHTML = bfxTask?.status === 'running'
      ? badge(`✅ 运行中 PID ${bfxTask.pid}`,'success') : badge('❌ 未运行','danger');
  } catch (e) { console.error('[loadBfx]', e); }
}

// ── Init ───────────────────────────────────────────────────────────────────────
async function refreshAll() {
  await Promise.all([loadProjects(), loadBgTasks(), loadCrons(), loadBfx()]);
}
refreshAll();
setInterval(refreshAll, 30000);
