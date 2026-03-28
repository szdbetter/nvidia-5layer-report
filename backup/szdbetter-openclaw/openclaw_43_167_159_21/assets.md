# Reese 资产清单

更新日期：2026-03-11 UTC

## 1. 员工 / 模型

### 可用模型别名
- `codex` → 代码、结构化产物、工程改造
- `gemini` → 超长上下文、多模态、超长文档吸收
- `glm` → 中文归纳、轻研究、翻译整合
- `kimi` → 长文速读、长资料初筛
- `opus` → 暂时跳过（provider 预算不足）
- `qwen` → 批量初筛、网页清洗、低成本并行
- `sonnet` → 暂时跳过（provider 预算不足）

### 当前建议路由
- 最终代码/脚本/格式转换：`codex`
- 中文总结与初版结构化输出：`glm`
- 海量长文预处理：`gemini` / `kimi`
- 高频初筛：`qwen`
- `sonnet/opus` 暂不纳入默认链路

## 2. 节点

### 本机主节点
能力：
- 文件读写
- shell/exec
- browser
- web search/fetch
- cron
- memory
- tts
- sessions/subagents

### `fiona-mbp2015`
- 平台：macOS
- 状态：在线
- 能力：`browser`, `system.run`, `system.which`
- 用途：浏览器态任务、macOS 专属执行、远端系统任务

## 3. 外部采集与检索能力

### 已可用
- GitHub（`gh` / github skill）
- 任意网页正文（Jina / web_fetch）
- RSS
- Exa 语义搜索
- YouTube 元数据/字幕
- B站元数据/字幕
- Agent Reach skill 已安装

### 半解锁 / 待补齐
- Twitter/X：Cookie 已写入 `.env`，但当前 xreach 实测仍报 csrf/header 匹配错误
- Reddit：需要代理或替代方案
- 小红书：未接 MCP
- 微博：未接 MCP
- 抖音：未接 MCP
- LinkedIn：未接 MCP
- 微信公众号：未装对应抓取链
- 小宇宙转写：缺 ffmpeg

## 4. 语音能力

### 已具备
- `tts`：文本转语音可用
- 可做短摘要播报、提醒、简短讲解

### 未完全解锁
- 长音频生产 SOP
- 音色策略与内容生产链
- 转写回流与字幕协同

## 5. 当前关键短板
1. X/Twitter 链路未完全打通
2. 小红书/抖音/微博等中文社媒仍缺专用 MCP
3. 生成链路缺模板化，导致思维导图和高质量总结不稳定
4. 语音只有基础 TTS，没有内容生产流水线
5. 单一远端节点，缺冗余
