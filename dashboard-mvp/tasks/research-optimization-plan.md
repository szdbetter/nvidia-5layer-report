# ClawLabs Research 情报站优化计划

> 日期：2026-03-25
> 项目：dashboard-mvp/public/research/
> 目标：将静态情报站升级为动态、可靠、自动化的 AI+Crypto 热点追踪平台

---

## 现状分析

### 架构
```
openclaw agent (定时采集)
  ↓ 生成完整 HTML（数据内嵌 JSON）
dashboard-mvp/public/research/index.html (775行单文件)
  ↓ Express 静态托管
nginx (:80) → proxy_pass :1980/research/
  ↓ auth-gate 密码保护
用户浏览器
```

### 数据 Schema（RESEARCH_DATA）
```json
{
  "date": "2026-03-25",
  "time": "07:03 BJ",
  "twitterOnline": true,
  "stats": { "total": 45, "xhs": 20, "reddit": 10, "twitter": 15 },
  "xhs": [{ "platform", "category", "title", "score", "likes", "collects", "comments", "url", "rank" }],
  "reddit": [{ "platform", "category", "title", "score", "likes", "comments", "url", "rank" }],
  "twitter": [{ "platform", "category", "title", "score", "likes", "retweets", "bookmarks", "views", "url", "rank" }],
  // 以下字段模板存在但数据缺失：
  "signals": [{ "icon", "tag", "color", "title", "desc" }],           // 三大共振信号
  "analysis": "markdown string",                                        // 深度分析报告
  "daily_review": [{ "signal", "score", "comment" }],                   // 信号评分
  "top_opportunity": { "title", "urgency", "subtitle", "actions": [] }  // 今日机会
}
```

### 已发现的 Bug（本次 QA 已修复）
1. **dashboard-mvp 未启动** → 502（无守护进程）
2. **JSON 中 `\n` 未转义** → RESEARCH_DATA 解析失败 → 全页空白
3. **5 个 build 函数缺空值检查** → buildSignals 崩溃阻断所有渲染

### 核心问题
- 数据是**死的**：内嵌在 HTML 里，每次更新要重新生成整个文件
- 没有数据 API：无法按日期查询、搜索、过滤
- 采集不自动：右侧面板"每日采集"和"MiniMax 分析"均为"待启用"
- 缺少守护进程：dashboard-mvp 挂了没人知道
- 4 个功能区（信号/分析/评分/机会）模板存在但数据缺失

---

## 优化任务（按优先级）

### Phase 1: 基础设施加固 [P1]

- [x] **1.1 dashboard-mvp 守护进程** ✅ 2026-03-25
  - ensure_dashboard.sh + cron 每分钟检活
  - 已验证：杀进程后自动恢复

- [x] **1.2 数据 API 化** ✅ 已存在（agent 已实现）
  - API: `/api/research/list`, `/api/research/latest`, `/api/research/collect`, `/api/research/status`
  - 数据路径从 `/tmp/daily-research` 迁移到 `data/research/`（持久化）
  - 8 个 raw JSON + 7 个 report MD

- [x] **1.3 前端数据加载改造** ✅ 已存在（agent 已实现）
  - fetch 动态加载 + 历史切换下拉框 + "一键抓取"按钮
  - 加载状态已处理

### Phase 2: 数据采集自动化 [P1]

- [x] **2.1 采集脚本** ✅ 已存在（agent 已实现）
  - `/root/.openclaw/workspace/projects/daily-research/collect.py` (15KB)
  - 采集小红书/Reddit/Twitter，输出到 `data/research/`

- [x] **2.2 AI 分析增强（用 qwen3:8b 补全缺失字段）** ✅ 2026-03-25
  - 新建 `scripts/enrich-research.py` — 调用 qwen3:8b 生成 signals、daily_review、top_opportunity
  - 已集成到 cron：采集完成后自动运行
  - 验证：3 个信号 + 3 个评分 + 1 个机会，数据质量好

- [x] **2.3 Cron 调度** ✅ 2026-03-25
  - `0 14 * * *`（每日 22:00 BJT）自动采集
  - 输出日志到 `data/research/collect.log`

### Phase 3: 功能完善 [P2]

- [x] **3.1 日期归档 API** ✅ 已存在（agent 已实现）
  - `GET /api/research/list` + switchHistory() + loadHistoryList()
  - 左侧归档栏 + 下拉切换

- [~] **3.2 搜索功能** — 跳过（每天 55 条数据，搜索价值低）

- [x] **3.3 通知推送** ✅ 2026-03-25
  - 集成到 enrich-research.py
  - 阈值：小红书 ≥5000 / Reddit ≥500 / Twitter ≥5000
  - 推送到 Telegram（复用 openclaw bot）
  - 已验证发送成功

### Phase 4: 体验优化 [P3]

- [ ] **4.1 Hacker News 数据源** — 待做
  - 面板显示 HN "已连接"，但 collect.py 未采集 HN
  - 需要加 HN API 采集 + 前端第 4 个 tab

- [x] **4.2 移动端** ✅ 已正常（用户确认 H5 显示正常）

- [ ] **4.3 趋势图表** — 待做（需积累多天数据）

- [x] **4.4 桌面端滚动修复** ✅ 2026-03-25
  - 根因：HTML 多余 `</div>` 闭合标签导致 main 提前关闭
  - 深度分析/信号评分区块溢出到 layout 外
  - 修复：删除多余闭合标签，验证所有标签平衡

---

## 实施顺序

```
Week 1: Phase 1（加固） → 1.1 守护进程 → 1.2 API → 1.3 前端改造
Week 2: Phase 2（采集） → 2.1 采集脚本 → 2.2 AI 分析 → 2.3 Cron
Week 3: Phase 3（功能） → 3.1 归档 → 3.2 搜索 → 3.3 通知
Later:  Phase 4（体验） → 按需推进
```

## 技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据存储 | JSON 文件（不用 DB） | 每天 1 个文件，数据量小，简单可靠 |
| AI 分析模型 | qwen3:8b via Ollama | 免费，53 t/s，中文质量好 |
| 前端框架 | 保持纯 JS | 单文件 775 行，不需要框架 |
| 图表库 | 暂不引入 | Phase 4 再考虑 |

## 文件变更清单

| 文件 | 操作 | Phase |
|------|------|-------|
| `ensure_dashboard.sh` | 新建 | 1.1 |
| `server.js` | 修改（+2 API 路由） | 1.2, 3.1 |
| `public/research/index.html` | 修改（JS 数据加载改造） | 1.3 |
| `data/research/` | 新建目录 | 1.2 |
| `scripts/collect-research.js` | 新建 | 2.1 |
| `scripts/analyze-research.js` | 新建 | 2.2 |
| crontab | 修改 | 2.3 |

总计：2 个现有文件修改 + 4 个新文件 + 1 个新目录
