# 能力补齐路线图

更新日期：2026-03-11 UTC

## P1：直接影响 ROI 的短板

### 1. X/Twitter 打通
目标：可稳定搜索、抓推文、后续可发帖维护
现状：Cookie 已在 `.env`，但 `xreach` 实测报错：
- `This request requires a matching csrf cookie and header`
判断：
- Cookie 已读到
- 当前链路仍未完全通过 xreach 验证，可能需要改为浏览器提取、升级 CLI 或校正 cookie 组装方式

### 2. 思维导图模板链
目标：把“总结”升级成“结构图”
动作：
- 固化 Mermaid/Markmap 输出协议
- 针对长文先抽层级，再生成图

### 3. 语音生产链
目标：从“能播报”升级为“可生产”
动作：
- 长文分段
- TTS 合成
- 文件归档
- 可选字幕/文稿同步

## P2：中文社媒采集补齐

### 4. 小红书
- 方案：Agent Reach + MCP
- 依赖：Cookie / Docker / MCP 服务

### 5. 微博
- 方案：weibo MCP

### 6. 抖音
- 方案：douyin MCP

## P3：稳定性补齐

### 7. Reddit
- 方案A：Exa/搜索兜底
- 方案B：代理直连

### 8. 备用节点
- 增加第二节点，避免 fiona 单点故障

## 执行顺序
1. 修 X/Twitter
2. 产出思维导图模板链
3. 产出语音生产链
4. 补小红书/微博/抖音
5. 补 Reddit 与备用节点
