# OpenClaw Dashboard — 产品需求文档 (PRD)
> 版本: v0.1 | 作者: Reese | 日期: 2026-03-18

## 一、产品定位
**一句话**：把OpenClaw从黑盒变成一个可视化控制中心——看得见、管得了、省得住。

**目标用户**：OpenClaw运营者（非技术人员也能用）

**不是什么**：
- ❌ 不替代OpenClaw本体
- ❌ 不是通用Agent平台
- ❌ 不是SaaS托管服务（本地部署优先）

## 二、核心痛点（来自竞品调研）

| 痛点 | 来源 | 严重度 |
|---|---|---|
| 上下文token消耗不透明，睡一觉账单炸了 | HappyClaw文章 | 🔴 P0 |
| 不知道Agent在干什么、卡在哪 | Control Center | 🔴 P0 |
| 多Agent协作看不见流转链路 | 两者共有 | 🟡 P1 |
| 记忆系统状态不可见（是否健康/可检索） | Control Center | 🟡 P1 |
| 定时任务执行状态散落在日志里 | 自身痛点 | 🟡 P1 |
| 配置安全风险无感知 | Control Center | 🟢 P2 |

## 三、信息架构（6大面板）

### 📊 Panel 1: Overview（总览）
**一屏回答：OpenClaw现在还好吗？**
- 系统健康状态（Gateway连接/Node在线/内存/磁盘）
- 当前活跃session数 + 排队任务数
- 今日token消耗 vs 预算阈值（进度条）
- 需要关注的事项（阻塞任务/失败cron/异常告警）
- 最近10条操作时间线

### 💰 Panel 2: Usage（用量与成本）
**一屏回答：钱花哪了？还剩多少？**
- 今日/7日/30日 token消耗趋势折线图
- 按模型分布饼图（Opus/Sonnet/豆包/GLM各占多少）
- 按session分布TOP10（哪个任务最烧钱）
- **上下文压力卡片**：每个活跃session的上下文占用率，接近限制的标红
- Cron定时任务的token归因（哪个定时任务最费钱）

### 👥 Panel 3: Staff（Agent状态）
**一屏回答：谁在忙、谁在闲、谁卡住了？**
- 活跃Agent列表（主Agent + 子Agent）
- 每个Agent当前状态：🟢运行中 / 🟡排队中 / 🔴阻塞 / ⚪空闲
- 当前执行的任务摘要
- 最近完成的任务 + 耗时
- Node物理节点状态（Fiona在线？VPS负载？）

### 🔄 Panel 4: Collaboration（协作链路）
**一屏回答：任务在谁手上？流转到哪了？**
- 父子Agent会话关系图（树形/流程图）
- 跨session消息流转记录
- 当前等待中的handoff（谁在等谁）
- sessions_spawn历史记录 + 结果

### 📋 Panel 5: Tasks & Cron（任务与调度）
**一屏回答：计划了什么、执行了什么、卡在哪？**
- Cron任务列表 + 最近执行状态/耗时/结果
- 手动任务看板（Todo/进行中/阻塞/完成）
- 执行链路追踪（一个任务经历了哪些工具调用）
- 失败任务自动高亮 + 重试按钮

### 🧠 Panel 6: Memory & Docs（记忆与文档）
**一屏回答：Agent记住了什么？文档最新状态？**
- OpenViking记忆库统计（总条目/最近写入/检索命中率）
- 工作区核心文档列表（SOUL.md/AGENTS.md/TOOLS.md等）+ 最后修改时间
- 在线编辑器（直接编辑md文件，保存即生效）
- 记忆健康状态：每个Agent的记忆是否可用/可检索
- Obsidian知识库同步状态

## 四、技术方案

### 前端
- **React 19 + Vite 6 + TypeScript**
- **Tailwind CSS 4 + shadcn/ui**（与HappyClaw同栈，社区组件丰富）
- **Zustand** 状态管理
- **recharts** 图表
- **PWA** 移动端适配（手机随时看）

### 后端
- **Hono**（轻量HTTP框架，比Express快10x）
- 直接读取OpenClaw Gateway API获取实时数据
- 读取 `~/.openclaw/` 目录下的配置/日志/数据库
- SQLite（WAL模式）存储历史快照用于趋势图
- **默认只读模式**，写操作需要显式开启

### 安全约束
- `READONLY_MODE=true` 默认
- 本地Token认证
- 不修改 `openclaw.json`（只读取）
- 写操作（编辑文档/重试任务）需二次确认

### 部署
- `npm run dev` 一键启动，默认 `http://localhost:4310`
- 可选nginx反向代理公网访问

## 五、里程碑

| 阶段 | 交付物 | 工期 | 价值 |
|---|---|---|---|
| **M1: 骨架** | Overview + Usage两个面板可用 | 3天 | 解决"钱花哪了"的核心痛点 |
| **M2: 运维** | Staff + Tasks面板 | 3天 | 解决"Agent在干什么"的痛点 |
| **M3: 协作** | Collaboration + Memory面板 | 3天 | 多Agent可视化 |
| **M4: 移动端** | PWA适配 + 响应式布局 | 2天 | 手机随时看 |

**总工期预估：11天**

## 六、数据源映射

| 面板数据 | 数据来源 |
|---|---|
| 系统健康 | `openclaw status` / Gateway API `/healthz` |
| Session列表 | Gateway API `sessions_list` |
| Token消耗 | Gateway API `session_status` / 日志解析 |
| Cron任务 | Gateway API `cron list/runs` |
| Agent状态 | `sessions_list` + `subagents list` |
| 记忆统计 | OpenViking API `memory_recall` |
| 工作区文档 | 直接读取 `~/.openclaw/workspace/` 文件系统 |
| Node状态 | Gateway API `nodes status/describe` |

## 七、与竞品差异化

| 能力 | Control Center | HappyClaw | **我们** |
|---|---|---|---|
| 多模型成本归因 | ❌ 只看总量 | ❌ 只有Claude | ✅ 按模型/session拆分 |
| 向量记忆可视化 | ❌ 纯文件 | ❌ 纯文件 | ✅ OpenViking语义检索 |
| 物理节点监控 | ❌ | ❌ | ✅ Fiona等Node状态 |
| 代码质量 | 🔴 18K行单文件 | ✅ 模块化 | ✅ 模块化+组件库 |
| 中文优先 | 🟡 双语 | ✅ | ✅ |

## 八、开放问题（需老板确认）

1. **优先级**：先做M1（成本可视化）还是先做M2（Agent状态）？
2. **部署方式**：纯本地 or 需要公网访问？
3. **是否需要多用户**：目前只有你一个人用，先单用户？
4. **是否开源**：做完要开源到GitHub吗？
