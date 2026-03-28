# OpenClaw 橙皮书分享课件 · 讲稿大纲

> 基于《OpenClaw 橙皮书》v1.1.0 提炼  
> 适合 20 分钟分享，共 16 页

---

## 第 1 页：封面
**标题**：OpenClaw：从聊天工具到数字员工的进化  
**副标题**：开源 AI Agent 系统架构与实战指南  
**要点**：
- GitHub 28万+ Stars，全球第一开源项目
- 吉祥物：龙虾（养虾文化）
- 从0到27.9万 Stars仅用不到4个月

---

## 第 2 页：OpenClaw 是什么
**标题**：OpenClaw 核心定位
**要点**：
- 开源、自托管的 AI Agent 系统
- 连接 20+ 消息渠道（WhatsApp/Telegram/飞书/钉钉/Discord等）
- 让 AI 从「顾问」变成「员工」——主动执行任务
- 与 ChatGPT 的核心区别：自主执行 vs 你问我答

---

## 第 3 页：为什么火
**标题**：现象级增长背后的原因
**要点**：
- GitHub Stars 28万+，超越 React 成为全球第一
- 72小时内获得6万 Stars，单日增长9000 Stars
- 「养虾」文化：中文社区将运行 OpenClaw 称为「养虾」
- 创始人 Peter Steinberger 加入 OpenAI，引发持续关注
- Moltbook：3万+ AI Agent 的社交网络实验场

---

## 第 4 页：核心架构
**标题**：Gateway-Node-Channel 三层架构
**要点**：
- Gateway：中央控制平面，WebSocket 总线，24/7 守护进程
- Node：设备端执行层（摄像头、录屏、系统命令）
- Channel：20+ 消息渠道接入层
- Loopback-First 设计：默认只绑定 localhost，天然安全

---

## 第 5 页：记忆系统
**标题**：四层记忆架构
**要点**：
- SOUL：不可变人格内核（Agent 是谁）
- TOOLS：动态工具列表（当前可用技能）
- USER：语义长期记忆（用户偏好、决策记录）
- Session：实时对话上下文
- 自动记忆保存（Pre-Compaction）+ 向量语义搜索

---

## 第 6 页：部署方案总览
**标题**：从本地到云端，总有一种适合你
**要点**：
- 本地安装：npm install -g openclaw（开发者首选）
- Docker 部署：docker-compose up -d（环境隔离）
- 国内云厂商一键部署：阿里云/腾讯云/火山引擎（9.9元/月起）
- 扣子编程：零门槛 SaaS 方案（¥49/月起）

---

## 第 7 页：渠道接入
**标题**：20+ 消息平台统一接入
**要点**：
- 国际平台：Telegram（5分钟入门）、Discord、WhatsApp、Slack
- 国内平台：QQ（官方支持）、飞书（内置）、钉钉（社区插件）、企业微信
- 统一三步：创建凭证 → 写入配置 → 启动 Gateway
- DM Pairing 机制：防止陌生人滥用

---

## 第 8 页：Skills 系统
**标题**：能力扩展的核心单元
**要点**：
- 三层优先级：工作区级 > 用户级 > 内置级
- ClawHub 技能市场：13,729 个 Skills（精选 5,494 个）
- 内置 55 个技能开箱即用
- 热门技能：Gmail、Agent Browser、GitHub、Summarize、Web Search

---

## 第 9 页：Skills 安全
**标题**：供应链攻击与防护
**要点**：
- ClawHavoc 事件：约 12% Skills 被确认为恶意
- 攻击手法：伪装专业工具 → 诱导安装 helper → 植入木马
- 篡改 SOUL.md 可「洗脑」Agent 长期行为
- 防护建议：审查源码、使用 SecureClaw 扫描、优先精选列表

---

## 第 10 页：模型配置
**标题**：多模型自由切换
**要点**：
- 国际模型：Claude（Agent 效果最佳）、GPT-5.4、Gemini
- 国产模型：DeepSeek-V3（性价比之王 $0.14/M）、GLM-5（代码最强）
- 本地模型：Ollama/LM Studio（完全免费、隐私安全）
- Fallback 机制：主模型不可用时自动降级

---

## 第 11 页：成本控制
**标题**：避免「一觉醒来 $1,100 账单」
**要点**：
- Token 消耗可能是传统聊天的几十到上百倍
- 省钱策略：三级 Fallback 链（Sonnet → Haiku → DeepSeek）
- 设置日预算上限：maxCostPerDay
- 推荐方案：复杂任务用 Claude，日常用 DeepSeek，心跳用 Gemini Flash 免费额度

---

## 第 12 页：安全模型
**标题**：默认不信任的安全哲学
**要点**：
- DM Pairing：未知用户需验证码批准
- 群组沙箱：会话隔离，群聊看不到私聊记忆
- 工具访问控制：allowlist/denylist 模式
- v2026.3.8 新增 ACP 身份验证
- 创始人坦诚：「prompt injection 没解决，有绝对风险」

---

## 第 13 页：已知安全事件
**标题**：5个月内的7起重大安全事件
**要点**：
- CVE-2026-25253：RCE 漏洞（CVSS 8.8），13.5万暴露实例受影响
- ClawHavoc：供应链攻击，800+ 恶意 Skills
- 谷歌封号：大规模封禁 OpenClaw 用户的 Google 账号
- 30,000+ 未认证暴露实例：公网开放 Gateway 的风险
- 工信部/CNCERT 发布安全风险预警

---

## 第 14 页：生态与社区
**标题**：养虾文化与国内生态
**要点**：
- 「养虾」：中文社区独特文化标签，降低传播门槛
- Moltbook：AI Agent 的社交网络，3万+ Agent 自主发帖互动
- 国内生态：10万+「云养虾」社区用户
- 深圳龙岗 AI 局发布支持政策征求意见稿
- 国产 Claw 产品：MaxClaw、AutoClaw、QClaw、ArkClaw 等

---

## 第 15 页：OpenClaw vs Claude Code
**标题**：互补而非替代
**要点**：
- OpenClaw：通用 AI 生活助手，多平台接入，长期在线
- Claude Code：专业编程 Agent，代码能力最强
- 最佳实践：OpenClaw 管生活（消息/邮件/日程），Claude Code 管代码
- 可通过 MCP 协议桥接两者能力

---

## 第 16 页：总结与建议
**标题**：给新手的三条建议
**要点**：
- 入门：阿里云一键部署 + QQ/飞书接入 + DeepSeek 模型（月均¥20-50）
- 安全：务必设置 Gateway 认证、审查 Skills 源码、定期备份
- 成本：配置 Fallback 链 + 日预算上限，避免账单失控
- 长期：关注社区精选列表，参与「养虾」生态共建

---

## 附录：3个可选主标题

1. **《养虾指南：OpenClaw 从入门到精通》**（轻松亲和风格）
2. **《28万 Stars 的 AI Agent 系统：OpenClaw 架构与实战》**（数据驱动风格）
3. **《从聊天工具到数字员工：OpenClaw 如何重塑人机协作》**（价值主张风格）

---

*文档版本：v1.0*  
*生成时间：2026-03-12*  
*来源：OpenClaw 橙皮书 v1.1.0*
