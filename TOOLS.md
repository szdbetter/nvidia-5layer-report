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

### 已归档skill（说一声即可恢复，mv _archive/xxx skills/）
- `gstack-design-consultation` — 设计系统咨询
- `gstack-plan-design-review` — 设计师视角审方案
- `gstack-qa-design-review` — 设计QA视觉问题
- `gstack-document-release` — 发版后自动更新README/CHANGELOG
- `gstack-setup-browser-cookies` — 导入浏览器cookie到无头浏览器
- `polymarket-fast-loop` / `polymarket-weather-trader` — Polymarket自动交易
- `stt` / `wechat` / `twitter-browser-harvest` — 语音转写/微信/推特采集
- `obsidian-sync` / `sp-using-superpowers` / `sp-subagent-driven-development` — 开发辅助
