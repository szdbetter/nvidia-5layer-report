### 核心原则与工具规范
1. **检索规范**：检索未知信息必须使用 `memory_search`；提取已知文件局部必须用 `memory_get` (配合 from/lines)。**严禁**一上来就 `read` 读取超 100 行的文件，**严禁**使用 `exec cat/grep` 或手动执行 `qmd`。
2. **路径规范**：所有路径使用相对路径或 `~/openclaw`，**严禁**写绝对路径。
3. **JINA API**：`curl "https://r.jina.ai/<URL>" -H "Authorization: Bearer $JIAN_API_KEY1"` (密钥在 ~/.openclaw/.env)。
4. **图片生成**：Google Gemini `imagen-4.0-generate-001` (ApiKey 在 skills.nano-banana-pro)。
5. **反爬虫抓取**：`exec python3 ~/openclaw/workspace/tools/scrapling_fetch.py "<URL>" 30000`。
6. **Moltbook**：账号 `shuhu1`，URL `https://www.moltbook.com/api/v1`。
7. **Github 备份**：直接使用 `exec` 调用 git 命令。
8. **子智能体防污染**：使用 `sessions_spawn` 派发垂直任务时，严禁让其继承庞大对话历史。
9. **项目协作**：持续项目写入 `memory/projects/<name>/`。必须维护 roadmap, task, issue, cowork, decision, learning。
10. **状态存档（Memory Store）**：完成核心里程碑时，必须主动调用 memory_store 工具，将当前进度和重要结论存入长期记忆库。不记得时，必须调用 memory_search 搜索“当前任务进度”以恢复上下文，严禁凭空幻觉。