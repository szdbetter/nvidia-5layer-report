const fs = require('fs');
const path = require('path');

const PROJECTS_DIR = path.join(process.env.HOME || '/root', '.openclaw', 'projects');
const WORKSPACE_PROJECTS_DIR = path.join(__dirname, '..', 'memory', 'projects');
const IMAGE_EXTS = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']);

function safeRead(filePath) {
  try { return fs.readFileSync(filePath, 'utf8'); } catch { return ''; }
}

function safeStat(filePath) {
  try { return fs.statSync(filePath); } catch { return null; }
}

function listProjectDirs(baseDir) {
  try {
    return fs.readdirSync(baseDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => path.join(baseDir, d.name));
  } catch {
    return [];
  }
}

function parseTaskFile(content) {
  const lines = content.split('\n').map(l => l.trim()).filter(Boolean);
  const done = [];
  const todo = [];
  for (const line of lines) {
    if (line.includes('[Done]') || line.includes('[x]') || line.includes('✅')) done.push(line);
    else if (line.includes('[ ]') || line.includes('TODO')) todo.push(line);
  }
  return { done, todo };
}

function deriveStatus(taskStats) {
  if (taskStats.todo.length === 0 && taskStats.done.length > 0) return 'Done';
  if (taskStats.done.length > 0) return 'Active';
  return 'Draft';
}

function derivePhase(taskStats) {
  if (taskStats.todo.length === 0 && taskStats.done.length > 0) return 'Completed';
  if (taskStats.done.length > 0) return 'Execution';
  return 'Planning';
}

function listInterestingFiles(projectDir) {
  const targets = ['task.md', 'issue.md', 'learning.md', 'decision.md', 'cowork.md', 'roadmap.md', 'sop.md', 'sop-evolution.md'];
  const out = [];
  for (const name of targets) {
    const full = path.join(projectDir, name);
    const st = safeStat(full);
    if (st && st.isFile()) out.push({ name, path: full, type: 'text' });
  }
  try {
    for (const entry of fs.readdirSync(projectDir, { withFileTypes: true })) {
      if (!entry.isFile()) continue;
      const ext = path.extname(entry.name).toLowerCase();
      if (IMAGE_EXTS.has(ext)) out.push({ name: entry.name, path: path.join(projectDir, entry.name), type: 'image' });
    }
  } catch {}
  return out;
}

function summarizeWorkContent(roadmap, task) {
  const text = [roadmap, task].filter(Boolean).join('\n');
  return text.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 8).join('\n') || '暂无摘要';
}

function buildMissionFromProject(projectDir, sourceBase) {
  const projectName = path.basename(projectDir);
  const roadmap = safeRead(path.join(projectDir, 'roadmap.md'));
  const task = safeRead(path.join(projectDir, 'task.md'));
  const issue = safeRead(path.join(projectDir, 'issue.md'));
  const decision = safeRead(path.join(projectDir, 'decision.md'));
  const cowork = safeRead(path.join(projectDir, 'cowork.md'));
  const learning = safeRead(path.join(projectDir, 'learning.md'));
  const sop = safeRead(path.join(projectDir, 'sop.md')) || safeRead(path.join(projectDir, 'sop-evolution.md'));
  const taskStats = parseTaskFile(task);
  const files = listInterestingFiles(projectDir);

  return {
    id: projectName,
    name: projectName,
    owner: 'Reese',
    sponsor: '岁月',
    priority: 'P1',
    status: deriveStatus(taskStats),
    progress_done: taskStats.done.length,
    progress_total: taskStats.done.length + taskStats.todo.length,
    progress_pct: taskStats.done.length + taskStats.todo.length > 0 ? Math.round(taskStats.done.length * 100 / (taskStats.done.length + taskStats.todo.length)) : 0,
    roi_hypothesis: roadmap.split('\n').find(l => l.includes('目标') || l.includes('ROI')) || '来自项目文档自动提取。',
    mission_text: roadmap.split('\n').slice(0, 10).join('\n').trim() || '缺少 roadmap.md',
    work_content: summarizeWorkContent(roadmap, task),
    deliverables: taskStats.done.slice(0, 5).join('\n') || '见 task.md',
    non_goals: '自动发现项目；未显式定义。',
    deadline: '未声明',
    acceptance_criteria: '至少存在 roadmap/task，并可见 Proof。',
    evidence_requirements: 'task.md 中带 Proof 的已完成项、项目文档、后续 artifacts。',
    failure_conditions: issue ? '存在 issue.md 需复核' : '未显式声明',
    risk_level: issue ? 'medium' : 'low',
    current_phase: derivePhase(taskStats),
    next_action: taskStats.todo[0] || '无未完成项',
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    docs: {
      roadmap: !!roadmap,
      task: !!task,
      issue: !!issue,
      decision: !!decision,
      cowork: !!cowork,
      learning: !!learning,
      sop: !!sop
    },
    docFiles: files,
    sop_summary: sop.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 8).join('\n') || '暂无 SOP',
    assignment_summary: decision.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 6).join('\n') || cowork.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 6).join('\n') || '暂无明确分工文档',
    taskStats,
    sourceBase,
  };
}

function getProjectMissions() {
  const primary = listProjectDirs(PROJECTS_DIR).map(dir => buildMissionFromProject(dir, PROJECTS_DIR));
  if (primary.length > 0) return primary;
  return listProjectDirs(WORKSPACE_PROJECTS_DIR).map(dir => buildMissionFromProject(dir, WORKSPACE_PROJECTS_DIR));
}

module.exports = { getProjectMissions, parseTaskFile, PROJECTS_DIR };
