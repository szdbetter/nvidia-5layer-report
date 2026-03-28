# Supermemory OpenClaw Plugin

## 核心概念 (费曼学习法总结)

**1. 这是什么？**
OpenClaw 的一个云端长期记忆插件，由 [Supermemory.ai](https://supermemory.ai) 提供支持。它就像是给机器人装了一个“云盘大脑”。

**2. 解决了什么问题？**
原来的机器人只有短期记忆（当前对话）和本地文件记忆（MEMORY.md）。这个插件能让机器人：
- **自动记住**你聊过的事（Auto-Capture）。
- **自动回想**相关背景（Auto-Recall），在每次回答你之前，先去云端搜索一下有没有相关的记忆。
- 建立一个持续更新的**用户画像**（User Profile）。

**3. 怎么工作的？**
它是一个在云端运行的服务。
- **存（Capture）**：你每说一句话，插件就会把对话发给 Supermemory，云端会自动提取要点、去重，并存入数据库。
- **取（Recall）**：你提问时，插件会先拿着你的问题去云端进行“语义搜索”（找意思相近的记忆），把找到的记忆塞给机器人作为背景知识。
- **分类（Containers）**：你可以把记忆装进不同的“盒子”（比如工作盒子、私人盒子）。

**4. 怎么安装和配置？**
- 安装：`openclaw plugins install @supermemory/openclaw-supermemory`
- 配置 API Key：`openclaw supermemory setup` 或者设置环境变量 `SUPERMEMORY_OPENCLAW_API_KEY`
- 进阶配置：`openclaw supermemory setup-advanced` (可以设置多久拉取一次画像，最多拉取几条记忆等)
- 也可以直接在 `openclaw.json` 的 `plugins.entries` 里配置。

**5. 提供了哪些工具 (Tools) 供 AI 使用？**
即使开启了自动存取，AI 也可以主动调用以下工具：
- `supermemory_store`: 主动存入重要信息。
- `supermemory_search`: 主动搜索特定记忆。
- `supermemory_forget`: 删除不需要的记忆。
- `supermemory_profile`: 查看用户的画像。

**6. 提供了哪些命令给用户？**
- `/remember <text>`: 手动让 AI 记住某句话。
- `/recall <query>`: 手动搜索记忆。

## 注意事项
- 这个插件**需要 Supermemory Pro 或更高级别的付费订阅**才能使用。
- 所有的记忆都存在云端，而不是本地的 `MEMORY.md`。
