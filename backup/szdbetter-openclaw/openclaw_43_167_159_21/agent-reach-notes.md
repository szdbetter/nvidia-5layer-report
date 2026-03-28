# Agent Reach 安装/测试记录（2026-03-11 UTC）

## 1. 安装来源
- 安装文档：`https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md`
- 安装命令（本次实际执行）：
  ```bash
  python3 -m pip install --user https://github.com/Panniantong/agent-reach/archive/main.zip
  ~/.local/bin/agent-reach install --env=auto --safe
  ```

> 说明：本次按“安全模式”执行，避免自动修改系统包。随后人工补了少量低风险配置。

## 2. 本机实际改动
- 安装 Python 包：`agent-reach==1.3.0`
- 注册 skill：
  - `~/.agents/skills/agent-reach/`
  - `~/.claude/skills/agent-reach/`
- 创建/修改：
  - `~/.config/yt-dlp/config` 添加 `--js-runtimes node`
  - `chmod 600 ~/.agent-reach/config.yaml`
- 安装：
  - `xreach-cli`（npm 全局）
- 配置：
  - `mcporter config add exa https://mcp.exa.ai/mcp`

## 3. doctor 结果（最终）
可用：6/14

### 已可用
1. GitHub 仓库和代码
2. YouTube 视频和字幕
3. RSS/Atom
4. 全网语义搜索（Exa via mcporter）
5. 任意网页（Jina Reader）
6. B站视频和字幕

### 仍未就绪 / 受限
1. Twitter/X：`xreach CLI` 被 doctor 判定版本过旧（当前显示 0.3.0，要求 >= 0.3.2）
2. Reddit：需要代理，否则服务器 IP 可能受限
3. 微博：未配置 weibo MCP
4. 小宇宙播客转写：缺 ffmpeg
5. 小红书：未配置 xiaohongshu MCP + 登录
6. 抖音：未配置 douyin MCP
7. LinkedIn：未配置 linkedin MCP
8. 微信公众号：未安装对应抓取工具

## 4. 实测记录

### 4.1 xreach
执行：
```bash
xreach --help
```
结果：CLI 可运行，但版本仍显示 `0.3.0`，未达到 doctor 要求。

### 4.2 YouTube
执行：
```bash
yt-dlp --dump-json --skip-download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
结果：成功拿到 JSON，字段示例：
```json
{"id":"dQw4w9WgXcQ","title":"Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)","channel":"Rick Astley","duration":213}
```
备注：仍有 warning：
- remote component challenge solver 未启用
- ffmpeg 未安装
但不影响基础元数据提取。

### 4.3 RSS
执行：
```python
import feedparser
feedparser.parse('https://hnrss.org/frontpage')
```
结果：可正常读取 RSS。

### 4.4 Web/Jina
执行：
```bash
curl -L -s https://r.jina.ai/http://example.com
```
结果：可正常读取网页内容。

## 5. 这个 skill 实际怎么用

## 核心判断
Agent Reach 本体更像“安装器 + 环境探测器 + 能力目录说明器”，不是统一抓取入口。
安装完成后，真正执行任务时，主要直接调用它背后的上游工具。

## 常用命令
```bash
agent-reach install --env=auto
agent-reach install --env=auto --safe
agent-reach install --env=auto --dry-run
agent-reach doctor
agent-reach watch
agent-reach check-update
agent-reach configure twitter-cookies "..."
agent-reach configure proxy http://user:pass@ip:port
agent-reach configure groq-key gsk_xxx
```

## 安装后实际工作流
### 1) 查环境是否能用
```bash
agent-reach doctor
```
用途：看哪些渠道已经打通、哪些缺依赖/凭证。

### 2) 定期巡检
```bash
agent-reach watch
```
用途：适合 cron，每天检查渠道健康和更新状态。

### 3) 真正干活时直接用上游工具
#### Twitter/X
```bash
xreach search "query" --json
```

#### YouTube / B站
```bash
yt-dlp --dump-json URL
```

#### GitHub
```bash
gh search repos "query"
```

#### 网页
```bash
curl -s "https://r.jina.ai/URL"
```

#### Exa 语义搜索
```bash
mcporter call 'exa.web_search_exa(...)'
```

#### RSS
```bash
python3 -c "import feedparser; ..."
```

## 6. 实际功能作用
### 它擅长什么
1. **把零散的信息抓取工具做成一张能力地图**：告诉你当前这台机器能抓哪些平台。
2. **快速补齐基础依赖**：统一安装/检查 `xreach`、`yt-dlp`、`mcporter`、`gh` 等。
3. **把“缺什么”说清楚**：是缺 CLI、缺代理、缺 Cookie、缺 Docker，还是缺 ffmpeg。
4. **适合作为多平台内容采集栈的 bootstrap 工具**。

### 它不擅长什么
1. **不是统一 API 层**：不会把所有平台操作抽象成一个稳定命令接口。
2. **不是全自动万能抓取器**：很多平台仍然需要你自己补 cookie、代理、Docker、MCP 服务。
3. **对版本/生态依赖较脆弱**：例如本次 `xreach` 已安装，但 doctor 仍判版本不够。
4. **对生产环境并不完全无脑**：自动模式可能触发系统级安装，服务器上最好先 safe mode。

## 7. 使用场景判断
### 适合
- 想在一台新机器上快速搭一个“多平台内容采集/检索工作台”
- 想知道当前环境到底缺哪块依赖
- 想给 AI agent 补齐 Twitter / YouTube / RSS / GitHub / Jina / MCP 相关能力
- 想做“安装 + 健康巡检 + 渠道清单”

### 不适合
- 只想抓单一平台；这时直接装对应工具更快
- 需要强一致、低波动、企业级稳定接口
- 不愿处理 cookie / proxy / Docker / MCP 这些外围依赖

## 8. 我的判断
### 结论
**Agent Reach 有价值，但它的价值主要在“编排安装与可用性盘点”，不在“统一执行能力”。**

### ROI 判断
- **中高 ROI 场景**：你要频繁折腾多平台抓取环境，或者要把一台机器快速变成内容采集节点。
- **低 ROI 场景**：你只需要 Twitter 或 YouTube 单一能力，直接安装对应工具更省事。

### 我对它的定位
它更像：
- 一个 **内容采集工具链 bootstrapper**
- 一个 **环境 doctor / checklist 工具**
- 一个 **给 agent 准备外部触角的能力总装层**

而不是：
- 一个成熟统一的“超级爬虫平台”
- 一个无需维护的稳定生产系统

## 9. 下一步建议
如果要把它变成真正可用的生产节点，优先顺序：
1. 修好 `xreach` 版本问题（>= 0.3.2）
2. 安装 `ffmpeg`
3. 按需要接入 `weibo` / `douyin` / `xiaohongshu` / `linkedin` MCP
4. 如果跑在大陆/海外受限网络，补代理配置
5. 给 `agent-reach watch` 挂 daily cron，异常才通知
