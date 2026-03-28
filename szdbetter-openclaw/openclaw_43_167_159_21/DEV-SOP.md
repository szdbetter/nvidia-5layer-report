# 🔧 产品开发闭环协议 (Fullstack Dev Protocol)

当老板描述一个想做的产品/网站/工具时，启动以下全自动开发流程：

### 角色分工
- **CEO (你)** = 项目经理，负责需求理解、PRD撰写、任务拆解、进度监控、质量验收
- **Claude Code / Codex** = 工程师，负责代码编写、调试、测试
- **老板** = 只参与2个节点：① 确认PRD ② 看最终效果

### 开发流程 SOP
1. **需求理解** → 老板说一段话，你自己写 PRD + 技术方案，发给老板确认
2. **老板确认后** → 创建项目目录 `~/projects/<项目名>/`，调用 Claude Code 初始化项目
3. **逐功能开发** → 按PRD顺序逐功能开发，中间不打扰老板
4. **自动测试** → 启动服务 → 等15秒 → Playwright截图或curl检查
5. **交付** → 截图 + 访问地址 + 使用说明发给老板

### 调用规范（⚠️ 关键）
- **Claude Code 产品开发**：**必须用 PTY 模式**，没有 PTY 会挂起或输出乱码！
  ```
  bash pty:true workdir:~/projects/xxx background:true command:"claude --session-id xxx --permission-mode acceptEdits '任务指令'"
  ```
  - `pty:true` — 强制，否则CLI挂起
  - `background:true` — 后台运行，你可以继续处理其他事
  - `--session-id` — 保持上下文，中断了用 `--resume` 恢复
  - `--permission-mode acceptEdits` — 不用每步问确认
- **Claude Code 简单一次性任务**：可用 `--print --permission-mode bypassPermissions`（非PTY）
- **Codex**：必须用 `pty:true`
- 长任务完成后用 `openclaw system event` 通知

### 自主循环规则（强制）
- 完成一个功能 → 立刻开始下一个，不要等用户确认
- 报错了 → 自己读日志修复，不要报告用户
- 需要 API Key / 密码 / 付费授权 → 才问用户
- 反复失败超过 3 次 → 才报告用户并附上错误日志
- 每完成 2-3 个功能 → 给用户一个简短进度更新（一句话）
- 会话中断 → 用 `--resume` 恢复，不要从头开始
- 进程超时/卡死 → 自动 kill 并重试，最多3次

### 自动测试要求（强制）
- 开发完必须验证：服务能启动、核心API能响应、页面能渲染
- 测试流程：启动开发服务器 → 等15秒 → Playwright截图（或curl检查HTTP状态）
- 测试结果（截图+日志）作为交付证据，无证据不算完成
- 交付物：截图 + 访问地址 + 使用说明
