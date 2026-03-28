### 工具使用规范

#### 1. 检索优先级
当前上下文 → `lcm_grep`/`lcm_expand_query` → `memory_recall` → `Read`(带offset/limit)
**严禁**一上来就全量读取超100行的文件。

#### 2. 子智能体防污染
`sessions_spawn` task以 `[ROLE:EXECUTOR]` 开头，仅含目标+必要参数。

#### 3. 项目文件结构
持续项目写入 `projects/<name>/`：roadmap.md, task.md, findings.md, progress.md, issue.md, LEARNING.md, SOP.md, RESEARCH.md

#### 4. 状态存档
核心里程碑 → `memory_store`。不记得先 `memory_recall`，严禁幻觉。

### 参考数据文件（按需加载，禁止预加载）
- `data/LLM-DISPATCH.md` — LLM分工表
- `data/DEV-ENV.md` — 开发环境/图片生成/STT参数
- `data/EXA-KEYS.md` — EXA API Key轮换
- `data/MiniMax.md` — MiniMax全能力调用手册

### 本地文档库
`docs/`（`openclaw/` 和 `OpenViking/`），优先读 `original_files/`
