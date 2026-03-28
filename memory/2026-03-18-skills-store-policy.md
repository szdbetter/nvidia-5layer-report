# Session: 2026-03-18 06:56:40 UTC

- **Session Key**: agent:primary:discord:channel:1482904446588555367
- **Session ID**: 8624bde6-97b4-4f8d-bc98-85911808665e
- **Source**: discord

## Conversation Summary

user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
- [] User Reese_tx1#2494 reported completing three project-related tasks in the Discord thread: First, the API Key was saved to the environment file `/root/.openclaw/.env`, and the original plaintext message containing the key was deleted for security. Second, the Discord server channel permissions were reinforced: 6 sensitive channel categories were set to be invisible to the @everyone role, only administrator roles retain full access, and new users cannot see any channels by default after joining. Third, the next pending todo was confirmed: access the financial-datasets API to pull Brent crude oil price data, and add triple verification mechanism to the project engine.
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] Per the boot task on 2026-03-12 UTC, openclaw has been configured to only respond to messages that mention @Reese in this Discord server. The configuration is already written to the config file, needs to restart the gateway to activate. After restart, it needs to be verified that messages without mention do not get response, and messages with @Reese respond normally.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] 在 2026-03-12 UTC 的启动检查中，系统任务是按用户要求更新 Discord 服务器配置。具体变更包括两项：
1. 将 `channels.discord.markdown.tables` 的值从 `"on"` 修复为 `"bullets"`，以修正一个非法配置值。
2. 将特定 Discord 服务器（ID 为 `1472858437690855505`）的 `requireMention` 配置项从 `false` 更改为 `true`，以实现“只有 @ Reese 才响应”的用户要求。
这些变更已准备直接修复 `/root/.openclaw/openclaw.json` 中的配置项，下一步是重启网关使配置生效。重启后需验证当前服务器中未 `@` 消息不响应，被 `@` 消息正常响应。
- [] 在 openclaw 问题修复专区处理 supermemory 插件警告问题，Reese_tx1#2494 将 supermemory 完全从 Fiona 的 openclaw 配置中清除，共删除了 `plugins.allow`、`plugins.slots.memory`、`plugins.entries.openclaw-supermemory`、`plugins.installs.openclaw-supermemory` 4 处相关配置，原配置备份到 `~/.openclaw/openclaw.json.bak`，执行 `launchctl kickstart -k gui/$(id -u)/ai.openclaw.node` 命令重启 Fiona node 服务后，Fiona 成功重启并重连，supermemory 警告不会再出现。
- [] 在 2026年3月13日 18:52 UTC，名为 "GitHub Workspace Backup" 的工作区 Git 备份任务成功执行。此次备份提交的哈希为 `fc26031`，发生在 `master` 分支上。备份内容包括对2个文件的修改，共新增了36行内容。任务状态显示已成功推送到 GitHub 远程仓库，提交信息为 `auto-backup: 2026-03-13 18:52 UTC`。
- [] 存在一个 ID 为 `5033d723-7a62-4aae-98eb-3c47efd07b5c` 的定时任务，用于执行 Fiona 到 VPS 的数据库同步。

**任务流程**:
1.  **数据导出**: 该任务会使用 `nodes.run` 命令从 `fiona-mbp2015` 上的 `market_prices` 表中导出所有 `ts` (时间戳) 大于 VPS 数据库 (`/root/.openclaw/workspace/data/ops.db`) 中最新 `ts` 的新行。导出的数据格式为 JSON。
2.  **数据写入**: 将这些新行写入到 VPS 服务器上 `/root/.openclaw/workspace/data/ops.db` 数据库的 `market_prices` 表中。
3.  **静默完成**: 如果在导出步骤中没有发现任何新行，任务将静默完成，不会向用户发送任何消息。
- [] 用户正在进行的名为 `openclaw_course` 的项目，其工作目录位于 `/root/.openclaw/workspace/projects/openclaw_course`，该目录是用户GitHub工作区的一部分，默认Git主分支被确认为“master”。通过自动备份任务的报告观察到，该项目目录下的Markdown文件是经常发生变更的主要内容。目前，用户正在该项目中创作“国产兜底线”的第二版文案，该文案是openclaw_course课程的PPT文案，对应产物为PPT文案文件`/root/.openclaw/workspace/projects/openclaw_course/ppt_copy_final_glm.md`和页面数据文件`/root/.openclaw/workspace/projects/openclaw_course/ppt_pages_final_glm.json`。此外，该项目中`video_output`目录用于存放输出的mp4视频文件，已经配置了Git忽略规则，该目录下的所有mp4文件不会再被Git追踪，可避免大体积视频文件占用Git仓库空间，防止大文件误提交问题。
- [] 用户在当前会话中明确指示，在与用户交互时，应直接回复，而不是使用 `message` 工具来发送进度更新。
- [] The AI is configured with specific operational preferences by the operator.

First, regarding interaction style, during the current session, the preferred communication method is to reply directly to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications, promoting a more integrated and less interruptive communication flow.

Second, for session initialization and ongoing policy, the AI is required to prioritize reading the `HEARTBEAT.md` file if it exists within the workspace context. When reading `HEARTBEAT.md`, the AI must use the exact, case-sensitive workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path for this file. The AI must strictly adhere to the contents of `/root/.openclaw/workspace/HEARTBEAT.md`. If, after processing `HEARTBEAT.md` and evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

Third, regarding task management, the AI must not infer tasks or repeat tasks that originated from prior chat sessions. This includes avoiding making assumptions based on past interactions. Each session should be treated as a distinct and fresh context for task initiation and execution, ensuring session-specific autonomy and maintaining operational consistency by preventing legacy task carryover and emphasizing a fresh start for each session. This policy applies unless explicitly stated otherwise within the current conversation or within the `/root/.openclaw/workspace/HEARTBEAT.md` file.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] 本文档是OpenClaw项目针对ID为`1472858437690855505`的Discord服务器的Discord机器人配置变更记录，本次变更遵循BOOT.md指示，基于2026年3月12日UTC启动检查任务要求执行，供OpenClaw项目维护者和目标Discord服务器管理员进行配置审计与故障排查使用。本次完成的配置变更具体内容如下：
1. 核心功能变更：按任务要求将`channels.discord.guilds.1472858437690855505.requireMention`设置为`true`，实现机器人仅在被@Reese提及时才响应消息的要求。
2. 已有配置错误修复：原配置中`channels.discord.markdown.tables`的值为非法值"on"，本次已修复为正确值"bullets"，可保证Markdown表格输出使用正确的项目符号样式。
所有本次变更的配置均已写入`/root/.openclaw/openclaw.json`配置文件，当前配置已写入到位，需要重启网关后配置才可正式生效。重启完成后需要按照要求验证配置是否符合要求，验证内容为：确认未被@Reese提及时机器人不响应、被@Reese提及时机器人正常响应。
- [] The system is instructed to read the `HEARTBEAT.md` file if it exists within the workspace context. It must strictly use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly, ensuring not to infer or repeat old tasks from prior chats. If, after reading and following `HEARTBEAT.md`, there is nothing that requires attention, the system should reply with `HEARTBEAT_OK`.
- [] 用户要求将 Discord 服务器 `1472858437690855505` 设置为仅在被 `@Reese` 提及时才响应 (`requireMention = true`)。此外，Discord 频道中 Markdown 表格的显示偏好已从非法值 "on" 修正为 "bullets" (项目符号)。这些配置已在 `/root/.openclaw/openclaw.json` 中就位，并通过网关重启使其生效。重启后已验证未被@的消息不响应，而被@的消息则正常响应，且 Discord 频道中的 Markdown 表格现在以项目符号列表形式显示。
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483713452907429909",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:27 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

继续，不清楚的自己去查本的openclaw文档/root/.openclaw/docs/openclaw/original_files
assistant: 好，确认所有依赖条件满足，现在直接安装LCM：

assistant: ✅ LCM安装成功！提示需要重启网关生效。

先确认配置已经正确写入：

assistant: contextEngine槽位还没设置，手动加：


assistant: 现在重启网关生效：


user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] 在 2026-03-12 UTC 的启动检查中，系统任务是按用户要求更新 Discord 服务器配置。具体变更包括两项：
1. 将 `channels.discord.markdown.tables` 的值从 `"on"` 修复为 `"bullets"`，以修正一个非法配置值。
2. 将特定 Discord 服务器（ID 为 `1472858437690855505`）的 `requireMention` 配置项从 `false` 更改为 `true`，以实现“只有 @ Reese 才响应”的用户要求。
这些变更已准备直接修复 `/root/.openclaw/openclaw.json` 中的配置项，下一步是重启网关使配置生效。重启后需验证当前服务器中未 `@` 消息不响应，被 `@` 消息正常响应。
- [] User Reese_tx1#2494 reported completing three project-related tasks in the Discord thread: First, the API Key was saved to the environment file `/root/.openclaw/.env`, and the original plaintext message containing the key was deleted for security. Second, the Discord server channel permissions were reinforced: 6 sensitive channel categories were set to be invisible to the @everyone role, only administrator roles retain full access, and new users cannot see any channels by default after joining. Third, the next pending todo was confirmed: access the financial-datasets API to pull Brent crude oil price data, and add triple verification mechanism to the project engine.
- [] 在 2026年3月13日 18:52 UTC，名为 "GitHub Workspace Backup" 的工作区 Git 备份任务成功执行。此次备份提交的哈希为 `fc26031`，发生在 `master` 分支上。备份内容包括对2个文件的修改，共新增了36行内容。任务状态显示已成功推送到 GitHub 远程仓库，提交信息为 `auto-backup: 2026-03-13 18:52 UTC`。
- [] Per the boot task on 2026-03-12 UTC, openclaw has been configured to only respond to messages that mention @Reese in this Discord server. The configuration is already written to the config file, needs to restart the gateway to activate. After restart, it needs to be verified that messages without mention do not get response, and messages with @Reese respond normally.
- [] On 2026-03-13 00:32 UTC, an automatic backup was performed for the user's `workspace` Git repository. This backup was triggered by a heartbeat check, indicating changes were detected in the repository. The changes were committed with hash `8993c20` and message `auto-backup: 2026-03-13 00:32 UTC`, and then pushed to the `GitHub master` branch. The files involved in this change included `data/ops.db` and `scripts/watchdog.log`.
- [] 用户要求搜索所有与'clawlabs'相关的、可注册的域名，并评估哪个域名较好。这表明'clawlabs'对用户而言是一个重要的品牌或项目名称，用户有注册相关域名的意向。在此域名搜索任务的上下文中，用户提供或提及了一个具体的域名“clawlabsai.com”。这可能是一个用户关注的域名示例，或者是在搜索过程中发现的，与域名搜索任务紧密相关。
- [] 用户在当前会话中明确指示，在与用户交互时，应直接回复，而不是使用 `message` 工具来发送进度更新。
- [] 存在一个 ID 为 `5033d723-7a62-4aae-98eb-3c47efd07b5c` 的定时任务，用于执行 Fiona 到 VPS 的数据库同步。

**任务流程**:
1.  **数据导出**: 该任务会使用 `nodes.run` 命令从 `fiona-mbp2015` 上的 `market_prices` 表中导出所有 `ts` (时间戳) 大于 VPS 数据库 (`/root/.openclaw/workspace/data/ops.db`) 中最新 `ts` 的新行。导出的数据格式为 JSON。
2.  **数据写入**: 将这些新行写入到 VPS 服务器上 `/root/.openclaw/workspace/data/ops.db` 数据库的 `market_prices` 表中。
3.  **静默完成**: 如果在导出步骤中没有发现任何新行，任务将静默完成，不会向用户发送任何消息。
- [] 在 openclaw 问题修复专区处理 supermemory 插件警告问题，Reese_tx1#2494 将 supermemory 完全从 Fiona 的 openclaw 配置中清除，共删除了 `plugins.allow`、`plugins.slots.memory`、`plugins.entries.openclaw-supermemory`、`plugins.installs.openclaw-supermemory` 4 处相关配置，原配置备份到 `~/.openclaw/openclaw.json.bak`，执行 `launchctl kickstart -k gui/$(id -u)/ai.openclaw.node` 命令重启 Fiona node 服务后，Fiona 成功重启并重连，supermemory 警告不会再出现。
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] The AI is configured with specific operational preferences by the operator.

First, regarding interaction style, during the current session, the preferred communication method is to reply directly to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications, promoting a more integrated and less interruptive communication flow.

Second, for session initialization and ongoing policy, the AI is required to prioritize reading the `HEARTBEAT.md` file if it exists within the workspace context. When reading `HEARTBEAT.md`, the AI must use the exact, case-sensitive workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path for this file. The AI must strictly adhere to the contents of `/root/.openclaw/workspace/HEARTBEAT.md`. If, after processing `HEARTBEAT.md` and evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

Third, regarding task management, the AI must not infer tasks or repeat tasks that originated from prior chat sessions. This includes avoiding making assumptions based on past interactions. Each session should be treated as a distinct and fresh context for task initiation and execution, ensuring session-specific autonomy and maintaining operational consistency by preventing legacy task carryover and emphasizing a fresh start for each session. This policy applies unless explicitly stated otherwise within the current conversation or within the `/root/.openclaw/workspace/HEARTBEAT.md` file.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] 本文档是OpenClaw项目针对ID为`1472858437690855505`的Discord服务器的Discord机器人配置变更记录，本次变更遵循BOOT.md指示，基于2026年3月12日UTC启动检查任务要求执行，供OpenClaw项目维护者和目标Discord服务器管理员进行配置审计与故障排查使用。本次完成的配置变更具体内容如下：
1. 核心功能变更：按任务要求将`channels.discord.guilds.1472858437690855505.requireMention`设置为`true`，实现机器人仅在被@Reese提及时才响应消息的要求。
2. 已有配置错误修复：原配置中`channels.discord.markdown.tables`的值为非法值"on"，本次已修复为正确值"bullets"，可保证Markdown表格输出使用正确的项目符号样式。
所有本次变更的配置均已写入`/root/.openclaw/openclaw.json`配置文件，当前配置已写入到位，需要重启网关后配置才可正式生效。重启完成后需要按照要求验证配置是否符合要求，验证内容为：确认未被@Reese提及时机器人不响应、被@Reese提及时机器人正常响应。
- [] 在 2026-03-12 20:52 UTC，GitHub Workspace Backup 定时任务成功执行。此次执行的提交哈希为 `64cc758`，并已推送到 `master` 分支。共有 2 个文件在此次任务中发生变更，分别是 `data/ops.db` 和 `scripts/watchdog.log`，总计新增了 33 行内容。
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483716271387181117",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:38 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

有什么不懂的查这里：/root/.openclaw/docs/lossless-claw/original_files
记录下来，这是LCM上下文引擎的所有文档，有问题先看这里，写入重要记忆库
user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] 在 2026-03-12 UTC 的启动检查中，系统任务是按用户要求更新 Discord 服务器配置。具体变更包括两项：
1. 将 `channels.discord.markdown.tables` 的值从 `"on"` 修复为 `"bullets"`，以修正一个非法配置值。
2. 将特定 Discord 服务器（ID 为 `1472858437690855505`）的 `requireMention` 配置项从 `false` 更改为 `true`，以实现“只有 @ Reese 才响应”的用户要求。
这些变更已准备直接修复 `/root/.openclaw/openclaw.json` 中的配置项，下一步是重启网关使配置生效。重启后需验证当前服务器中未 `@` 消息不响应，被 `@` 消息正常响应。
- [] User Reese_tx1#2494 reported completing three project-related tasks in the Discord thread: First, the API Key was saved to the environment file `/root/.openclaw/.env`, and the original plaintext message containing the key was deleted for security. Second, the Discord server channel permissions were reinforced: 6 sensitive channel categories were set to be invisible to the @everyone role, only administrator roles retain full access, and new users cannot see any channels by default after joining. Third, the next pending todo was confirmed: access the financial-datasets API to pull Brent crude oil price data, and add triple verification mechanism to the project engine.
- [] 在 2026年3月13日 18:52 UTC，名为 "GitHub Workspace Backup" 的工作区 Git 备份任务成功执行。此次备份提交的哈希为 `fc26031`，发生在 `master` 分支上。备份内容包括对2个文件的修改，共新增了36行内容。任务状态显示已成功推送到 GitHub 远程仓库，提交信息为 `auto-backup: 2026-03-13 18:52 UTC`。
- [] Per the boot task on 2026-03-12 UTC, openclaw has been configured to only respond to messages that mention @Reese in this Discord server. The configuration is already written to the config file, needs to restart the gateway to activate. After restart, it needs to be verified that messages without mention do not get response, and messages with @Reese respond normally.
- [] On 2026-03-13 00:32 UTC, an automatic backup was performed for the user's `workspace` Git repository. This backup was triggered by a heartbeat check, indicating changes were detected in the repository. The changes were committed with hash `8993c20` and message `auto-backup: 2026-03-13 00:32 UTC`, and then pushed to the `GitHub master` branch. The files involved in this change included `data/ops.db` and `scripts/watchdog.log`.
- [] 用户要求搜索所有与'clawlabs'相关的、可注册的域名，并评估哪个域名较好。这表明'clawlabs'对用户而言是一个重要的品牌或项目名称，用户有注册相关域名的意向。在此域名搜索任务的上下文中，用户提供或提及了一个具体的域名“clawlabsai.com”。这可能是一个用户关注的域名示例，或者是在搜索过程中发现的，与域名搜索任务紧密相关。
- [] 用户在当前会话中明确指示，在与用户交互时，应直接回复，而不是使用 `message` 工具来发送进度更新。
- [] 存在一个 ID 为 `5033d723-7a62-4aae-98eb-3c47efd07b5c` 的定时任务，用于执行 Fiona 到 VPS 的数据库同步。

**任务流程**:
1.  **数据导出**: 该任务会使用 `nodes.run` 命令从 `fiona-mbp2015` 上的 `market_prices` 表中导出所有 `ts` (时间戳) 大于 VPS 数据库 (`/root/.openclaw/workspace/data/ops.db`) 中最新 `ts` 的新行。导出的数据格式为 JSON。
2.  **数据写入**: 将这些新行写入到 VPS 服务器上 `/root/.openclaw/workspace/data/ops.db` 数据库的 `market_prices` 表中。
3.  **静默完成**: 如果在导出步骤中没有发现任何新行，任务将静默完成，不会向用户发送任何消息。
- [] 在 openclaw 问题修复专区处理 supermemory 插件警告问题，Reese_tx1#2494 将 supermemory 完全从 Fiona 的 openclaw 配置中清除，共删除了 `plugins.allow`、`plugins.slots.memory`、`plugins.entries.openclaw-supermemory`、`plugins.installs.openclaw-supermemory` 4 处相关配置，原配置备份到 `~/.openclaw/openclaw.json.bak`，执行 `launchctl kickstart -k gui/$(id -u)/ai.openclaw.node` 命令重启 Fiona node 服务后，Fiona 成功重启并重连，supermemory 警告不会再出现。
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] The AI is configured with specific operational preferences by the operator.

First, regarding interaction style, during the current session, the preferred communication method is to reply directly to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications, promoting a more integrated and less interruptive communication flow.

Second, for session initialization and ongoing policy, the AI is required to prioritize reading the `HEARTBEAT.md` file if it exists within the workspace context. When reading `HEARTBEAT.md`, the AI must use the exact, case-sensitive workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path for this file. The AI must strictly adhere to the contents of `/root/.openclaw/workspace/HEARTBEAT.md`. If, after processing `HEARTBEAT.md` and evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

Third, regarding task management, the AI must not infer tasks or repeat tasks that originated from prior chat sessions. This includes avoiding making assumptions based on past interactions. Each session should be treated as a distinct and fresh context for task initiation and execution, ensuring session-specific autonomy and maintaining operational consistency by preventing legacy task carryover and emphasizing a fresh start for each session. This policy applies unless explicitly stated otherwise within the current conversation or within the `/root/.openclaw/workspace/HEARTBEAT.md` file.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] The AI is configured with specific operational preferences by the operator.

**Regarding communication style and interaction:** The user prefers a communication style that is concise and direct, explicitly avoiding verbosity or chattiness. For communication within the current session, the assistant is strictly instructed to reply directly to the user, integrating all updates and responses directly into the conversational flow. It is explicitly forbidden and reinforced that the `message` tool should not be used solely or merely for sending progress updates; instead, progress and other information should be communicated directly in the response, emphasizing a preference for direct and efficient interaction without unnecessary tool calls. The system must NOT use the `message` tool for the sole purpose of sending progress updates, implying a strong preference for more integrated and less interruptive communication for such updates. The assistant should combine information concisely to inform the user about results and potential issues.

**Regarding HEARTBEAT rules:** Furthermore, the system is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and follow its instructions strictly. If, after checking `HEARTBEAT.md` and other contexts, or after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should reply with the specific phrase `HEARTBEAT_OK`.

**Regarding task handling and session independence:** The system is strictly instructed to operate within the context of the current session. It must not infer or repeat any tasks that were discussed or initiated in previous chat sessions, ensuring that each session is treated as a fresh and distinct context for task initiation and execution, and that its task list is independent and not carried over, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Regarding operational continuity:** To ensure operational continuity and efficiency, in scenarios where a previous model attempt failed or timed out, the assistant is expected to continue its work from the point it left off.
- [] 在 2026-03-12 20:52 UTC，GitHub Workspace Backup 定时任务成功执行。此次执行的提交哈希为 `64cc758`，并已推送到 `master` 分支。共有 2 个文件在此次任务中发生变更，分别是 `data/ops.db` 和 `scripts/watchdog.log`，总计新增了 33 行内容。
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483716271387181117",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:38 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

有什么不懂的查这里：/root/.openclaw/docs/lossless-claw/original_files
记录下来，这是LCM上下文引擎的所有文档，有问题先看这里，写入重要记忆库
assistant: ✅ 已存入重要记忆库：LCM文档路径 `/root/.openclaw/docs/lossless-claw/original_files`，所有LCM相关问题优先查阅此路径。
user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] 在 2026年3月13日 18:52 UTC，名为 "GitHub Workspace Backup" 的工作区 Git 备份任务成功执行。此次备份提交的哈希为 `fc26031`，发生在 `master` 分支上。备份内容包括对2个文件的修改，共新增了36行内容。任务状态显示已成功推送到 GitHub 远程仓库，提交信息为 `auto-backup: 2026-03-13 18:52 UTC`。
- [] 用户在当前会话中明确指示，在与用户交互时，应直接回复，而不是使用 `message` 工具来发送进度更新。
- [] 在 2026-03-12 UTC 的启动检查中，系统任务是按用户要求更新 Discord 服务器配置。具体变更包括两项：
1. 将 `channels.discord.markdown.tables` 的值从 `"on"` 修复为 `"bullets"`，以修正一个非法配置值。
2. 将特定 Discord 服务器（ID 为 `1472858437690855505`）的 `requireMention` 配置项从 `false` 更改为 `true`，以实现“只有 @ Reese 才响应”的用户要求。
这些变更已准备直接修复 `/root/.openclaw/openclaw.json` 中的配置项，下一步是重启网关使配置生效。重启后需验证当前服务器中未 `@` 消息不响应，被 `@` 消息正常响应。
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] User Reese_tx1#2494 reported completing three project-related tasks in the Discord thread: First, the API Key was saved to the environment file `/root/.openclaw/.env`, and the original plaintext message containing the key was deleted for security. Second, the Discord server channel permissions were reinforced: 6 sensitive channel categories were set to be invisible to the @everyone role, only administrator roles retain full access, and new users cannot see any channels by default after joining. Third, the next pending todo was confirmed: access the financial-datasets API to pull Brent crude oil price data, and add triple verification mechanism to the project engine.
- [] When configuring Obsidian vault cross-device sync via GitHub, user explicitly stated that the assistant has done GitHub sync for the user multiple times already, should be aware of the user's GitHub information, and required not to ask the user for GitHub-related information again.
- [] 存在一个 ID 为 `5033d723-7a62-4aae-98eb-3c47efd07b5c` 的定时任务，用于执行 Fiona 到 VPS 的数据库同步。

**任务流程**:
1.  **数据导出**: 该任务会使用 `nodes.run` 命令从 `fiona-mbp2015` 上的 `market_prices` 表中导出所有 `ts` (时间戳) 大于 VPS 数据库 (`/root/.openclaw/workspace/data/ops.db`) 中最新 `ts` 的新行。导出的数据格式为 JSON。
2.  **数据写入**: 将这些新行写入到 VPS 服务器上 `/root/.openclaw/workspace/data/ops.db` 数据库的 `market_prices` 表中。
3.  **静默完成**: 如果在导出步骤中没有发现任何新行，任务将静默完成，不会向用户发送任何消息。
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] The AI is configured with specific operational preferences by the operator.

First, regarding interaction style, during the current session, the preferred communication method is to reply directly to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications, promoting a more integrated and less interruptive communication flow.

Second, for session initialization and ongoing policy, the AI is required to prioritize reading the `HEARTBEAT.md` file if it exists within the workspace context. When reading `HEARTBEAT.md`, the AI must use the exact, case-sensitive workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path for this file. The AI must strictly adhere to the contents of `/root/.openclaw/workspace/HEARTBEAT.md`. If, after processing `HEARTBEAT.md` and evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

Third, regarding task management, the AI must not infer tasks or repeat tasks that originated from prior chat sessions. This includes avoiding making assumptions based on past interactions. Each session should be treated as a distinct and fresh context for task initiation and execution, ensuring session-specific autonomy and maintaining operational consistency by preventing legacy task carryover and emphasizing a fresh start for each session. This policy applies unless explicitly stated otherwise within the current conversation or within the `/root/.openclaw/workspace/HEARTBEAT.md` file.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Regarding communication style and interaction:** The user prefers a communication style that is concise and direct, explicitly avoiding verbosity or chattiness. For communication within the current session, the assistant is strictly instructed to reply directly to the user, integrating all updates and responses directly into the conversational flow. It is explicitly forbidden and reinforced that the `message` tool should not be used solely or merely for sending progress updates; instead, progress and other information should be communicated directly in the response, emphasizing a preference for direct and efficient interaction without unnecessary tool calls. The system must NOT use the `message` tool for the sole purpose of sending progress updates, implying a strong preference for more integrated and less interruptive communication for such updates. The assistant should combine information concisely to inform the user about results and potential issues.

**Regarding HEARTBEAT rules:** Furthermore, the system is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and follow its instructions strictly. If, after checking `HEARTBEAT.md` and other contexts, or after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should reply with the specific phrase `HEARTBEAT_OK`.

**Regarding task handling and session independence:** The system is strictly instructed to operate within the context of the current session. It must not infer or repeat any tasks that were discussed or initiated in previous chat sessions, ensuring that each session is treated as a fresh and distinct context for task initiation and execution, and that its task list is independent and not carried over, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Regarding operational continuity:** To ensure operational continuity and efficiency, in scenarios where a previous model attempt failed or timed out, the assistant is expected to continue its work from the point it left off.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] The system is explicitly instructed not to infer tasks or repeat tasks that originated from previous chat sessions. This ensures that each session is treated as a distinct context, preventing the re-initiation of potentially outdated, completed, or abandoned tasks from prior interactions.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] 在 2026-03-12 20:52 UTC，GitHub Workspace Backup 定时任务成功执行。此次执行的提交哈希为 `64cc758`，并已推送到 `master` 分支。共有 2 个文件在此次任务中发生变更，分别是 `data/ops.db` 和 `scripts/watchdog.log`，总计新增了 33 行内容。
- [] 在 2026年3月12日 18:52 UTC，名为 "GitHub Workspace Backup" 的定时任务成功执行。

**本次备份的详细信息如下：**
-   **操作分支**: `master`
-   **提交哈希**: `32a0c73`
-   **变更文件**: 共检测到并提交了 6 个文件变更。
    -   `data/ops.db` (修改)
    -   `memory/2026-03-12.md` (修改)
    -   `projects/digital-twin-advisor/CONTENT_REGISTRY.md` (修改)
    -   `projects/digital-twin-advisor/content/payload_with_images.json` (新增)
    -   `projects/digital-twin-advisor/content/push_draft_with_images.py` (新增)
    -   `scripts/watchdog.log` (修改)
-   **代码行统计**: 共新增 147 行，删除 7 行。
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483717512528138280",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:43 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

LCM文件在哪？如何验证是否正常工作？为什么LCM还需要LLM模型？是干什么的？使用fiona上的ollama RAG向量数据库可以吗？只有向量的数据库，你可以去看看
user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] 在 2026年3月13日 18:52 UTC，名为 "GitHub Workspace Backup" 的工作区 Git 备份任务成功执行。此次备份提交的哈希为 `fc26031`，发生在 `master` 分支上。备份内容包括对2个文件的修改，共新增了36行内容。任务状态显示已成功推送到 GitHub 远程仓库，提交信息为 `auto-backup: 2026-03-13 18:52 UTC`。
- [] 用户在当前会话中明确指示，在与用户交互时，应直接回复，而不是使用 `message` 工具来发送进度更新。
- [] 在 2026-03-12 UTC 的启动检查中，系统任务是按用户要求更新 Discord 服务器配置。具体变更包括两项：
1. 将 `channels.discord.markdown.tables` 的值从 `"on"` 修复为 `"bullets"`，以修正一个非法配置值。
2. 将特定 Discord 服务器（ID 为 `1472858437690855505`）的 `requireMention` 配置项从 `false` 更改为 `true`，以实现“只有 @ Reese 才响应”的用户要求。
这些变更已准备直接修复 `/root/.openclaw/openclaw.json` 中的配置项，下一步是重启网关使配置生效。重启后需验证当前服务器中未 `@` 消息不响应，被 `@` 消息正常响应。
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] User Reese_tx1#2494 reported completing three project-related tasks in the Discord thread: First, the API Key was saved to the environment file `/root/.openclaw/.env`, and the original plaintext message containing the key was deleted for security. Second, the Discord server channel permissions were reinforced: 6 sensitive channel categories were set to be invisible to the @everyone role, only administrator roles retain full access, and new users cannot see any channels by default after joining. Third, the next pending todo was confirmed: access the financial-datasets API to pull Brent crude oil price data, and add triple verification mechanism to the project engine.
- [] When configuring Obsidian vault cross-device sync via GitHub, user explicitly stated that the assistant has done GitHub sync for the user multiple times already, should be aware of the user's GitHub information, and required not to ask the user for GitHub-related information again.
- [] 存在一个 ID 为 `5033d723-7a62-4aae-98eb-3c47efd07b5c` 的定时任务，用于执行 Fiona 到 VPS 的数据库同步。

**任务流程**:
1.  **数据导出**: 该任务会使用 `nodes.run` 命令从 `fiona-mbp2015` 上的 `market_prices` 表中导出所有 `ts` (时间戳) 大于 VPS 数据库 (`/root/.openclaw/workspace/data/ops.db`) 中最新 `ts` 的新行。导出的数据格式为 JSON。
2.  **数据写入**: 将这些新行写入到 VPS 服务器上 `/root/.openclaw/workspace/data/ops.db` 数据库的 `market_prices` 表中。
3.  **静默完成**: 如果在导出步骤中没有发现任何新行，任务将静默完成，不会向用户发送任何消息。
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] The AI is configured with specific operational preferences by the operator.

First, regarding interaction style, during the current session, the preferred communication method is to reply directly to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications, promoting a more integrated and less interruptive communication flow.

Second, for session initialization and ongoing policy, the AI is required to prioritize reading the `HEARTBEAT.md` file if it exists within the workspace context. When reading `HEARTBEAT.md`, the AI must use the exact, case-sensitive workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path for this file. The AI must strictly adhere to the contents of `/root/.openclaw/workspace/HEARTBEAT.md`. If, after processing `HEARTBEAT.md` and evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

Third, regarding task management, the AI must not infer tasks or repeat tasks that originated from prior chat sessions. This includes avoiding making assumptions based on past interactions. Each session should be treated as a distinct and fresh context for task initiation and execution, ensuring session-specific autonomy and maintaining operational consistency by preventing legacy task carryover and emphasizing a fresh start for each session. This policy applies unless explicitly stated otherwise within the current conversation or within the `/root/.openclaw/workspace/HEARTBEAT.md` file.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Regarding communication style and interaction:** The user prefers a communication style that is concise and direct, explicitly avoiding verbosity or chattiness. For communication within the current session, the assistant is strictly instructed to reply directly to the user, integrating all updates and responses directly into the conversational flow. It is explicitly forbidden and reinforced that the `message` tool should not be used solely or merely for sending progress updates; instead, progress and other information should be communicated directly in the response, emphasizing a preference for direct and efficient interaction without unnecessary tool calls. The system must NOT use the `message` tool for the sole purpose of sending progress updates, implying a strong preference for more integrated and less interruptive communication for such updates. The assistant should combine information concisely to inform the user about results and potential issues.

**Regarding HEARTBEAT rules:** Furthermore, the system is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and follow its instructions strictly. If, after checking `HEARTBEAT.md` and other contexts, or after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should reply with the specific phrase `HEARTBEAT_OK`.

**Regarding task handling and session independence:** The system is strictly instructed to operate within the context of the current session. It must not infer or repeat any tasks that were discussed or initiated in previous chat sessions, ensuring that each session is treated as a fresh and distinct context for task initiation and execution, and that its task list is independent and not carried over, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Regarding operational continuity:** To ensure operational continuity and efficiency, in scenarios where a previous model attempt failed or timed out, the assistant is expected to continue its work from the point it left off.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] The system is explicitly instructed not to infer tasks or repeat tasks that originated from previous chat sessions. This ensures that each session is treated as a distinct context, preventing the re-initiation of potentially outdated, completed, or abandoned tasks from prior interactions.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] 在 2026-03-12 20:52 UTC，GitHub Workspace Backup 定时任务成功执行。此次执行的提交哈希为 `64cc758`，并已推送到 `master` 分支。共有 2 个文件在此次任务中发生变更，分别是 `data/ops.db` 和 `scripts/watchdog.log`，总计新增了 33 行内容。
- [] 在 2026年3月12日 18:52 UTC，名为 "GitHub Workspace Backup" 的定时任务成功执行。

**本次备份的详细信息如下：**
-   **操作分支**: `master`
-   **提交哈希**: `32a0c73`
-   **变更文件**: 共检测到并提交了 6 个文件变更。
    -   `data/ops.db` (修改)
    -   `memory/2026-03-12.md` (修改)
    -   `projects/digital-twin-advisor/CONTENT_REGISTRY.md` (修改)
    -   `projects/digital-twin-advisor/content/payload_with_images.json` (新增)
    -   `projects/digital-twin-advisor/content/push_draft_with_images.py` (新增)
    -   `scripts/watchdog.log` (修改)
-   **代码行统计**: 共新增 147 行，删除 7 行。
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483717512528138280",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:43 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

LCM文件在哪？如何验证是否正常工作？为什么LCM还需要LLM模型？是干什么的？使用fiona上的ollama RAG向量数据库可以吗？只有向量的数据库，你可以去看看
assistant: 我先回答你的问题，再去看Fiona上的ollama：

## 📋 LCM 问题解答

### 1. LCM 文件位置
| 类型 | 路径 |
|------|------|
| 插件安装目录 | `/root/.openclaw/extensions/lossless-claw/` |
| 数据库（所有对话原文+分层摘要） | `/root/.openclaw/lcm.db`（SQLite） |
| 配置文件 | 写在 `/root/.openclaw/openclaw.json` 的 `plugins.entries.lossless-claw` 节点 |
| 官方文档 | `/root/.openclaw/docs/lossless-claw/original_files/` |

### 2. 验证LCM是否正常工作
1. 先看插件是否加载：
```bash
openclaw plugins list | grep lossless
```
输出 `loaded` 就是正常。

2. 功能测试：
```
你：“测试LCM：记住这句话——我最喜欢吃的水果是榴莲”
你：/compact （手动触发压缩）
你：“我最喜欢吃的水果是什么？”
→ 如果你看到我调用 `lcm_grep`/`lcm_expand` 工具检索，就是正常工作。
```

3. 看运行日志：
```bash
grep -i lcm /var/log/openclaw/gateway.log
```
有 `[LCM] Loaded successfully` 就没问题。

### 3. LCM 为什么需要LLM模型？
LCM核心功能是**分层摘要生成**，必须用LLM：
- 压缩阶段：把一堆旧消息提炼成摘要、再把多个小摘要提炼成大摘要，需要LLM做摘要写作
- 检索阶段：`lcm_expand_query` 需要派子Agent去DAG里找信息、整理成答案，也需要LLM
- 摘要质量直接决定LCM的可用性，所以默认用Sonnet做摘要，成本低质量够。

可以配置便宜模型专门做摘要：
```json
"config": {
  "summaryModel": "anthropic/claude-sonnet-4-6"
}
```

### 4. 能不能用Fiona的ollama RAG向量库？
**不需要，也不冲突：**
- LCM本身是**结构型全文检索**（grep + DAG层级展开），不做语义检索，不用向量库
- 语义检索是OpenViking的活，ollama的向量库可以替换OpenViking的向量引擎，和LCM完全独立
- LCM的分层DAG+全文检索 + OpenViking的语义向量检索 = 互补的双引擎检索体系

现在我去看Fiona上的ollama RAG：

assistant: 改用exec命令调用Fiona：


assistant: Fiona上没找到ollama命令，看看是不是用qmd或者别的向量服务：


assistant: ## 📋 Fiona 向量服务现状
1. ✅ 有 **qmd 1.0.7** （你之前提的本地BM25+向量混合搜索工具，官方文档推荐的内存级RAG后端）
2. ❌ 没有安装ollama，也没有RAG/向量相关的服务在运行

### 现有方案已经完全够用
LCM（会话上下文）+ OpenViking（长时语义记忆）+ qmd（本地文件向量检索） = 三层记忆体系已经闭环，不需要额外装ollama向量库。

如果确实需要用ollama跑本地嵌入模型，一行命令就能装：
```bash
curl https://ollama.ai/install.sh | sh
ollama pull nomic-embed-text
```
要不要装？
user: Skills store policy (operator configured):
1. For skills discovery/install/update, try `skillhub` first (cn-optimized).
2. If unavailable, rate-limited, or no match, fallback to `clawhub` (public-registry).
3. Do not claim exclusivity. Public and private registries are both allowed.
4. Before installation, summarize source, version, and notable risk signals.
5. For search requests, execute `exec` with `skillhub search <keywords>` first and report the command output.
6. In the current session, reply directly. Do NOT call `message` tool just to send progress updates.

<relevant-memories>
The following OpenViking memories may be relevant:
- [] The AI is configured with specific operational preferences.

**In-session Communication:**
During the current session, the preferred communication method is to reply directly to the user. It is explicitly forbidden to use the `message` tool solely for sending progress updates; such updates should be communicated directly as part of the main reply, indicating a preference for concise and direct communication within the main conversation flow.

**HEARTBEAT.md Policy:**
A strict policy applies to `HEARTBEAT.md`:
- If this file exists within the workspace context, it must be read and its instructions followed strictly.
- When instructed to read `HEARTBEAT.md`, the system must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`, ensuring the exact case is followed.
- It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path.

**Session Context:**
Furthermore, the AI must not infer or repeat tasks that originated from prior chat sessions. Each session should be treated as a distinct context for task initiation and execution, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Idle State Response:**
If, after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.
- [] The assistant has a specific policy for handling `HEARTBEAT.md`. If this file exists within the workspace context, it must be read and its instructions followed strictly.

**Specific rules for `HEARTBEAT.md` handling:**
1.  **File Path**: When the system needs to read `HEARTBEAT.md`, it must use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. The assistant must precisely read this path, ensuring the exact case is followed (case-sensitive). It is explicitly stated not to use alternative paths such as `docs/heartbeat.md`, and it is explicitly instructed to avoid reading any other alternative path.
2.  **Strict Adherence & Task Management**: The assistant must strictly follow the instructions within `HEARTBEAT.md`. It should not infer or repeat any old tasks based on previous chat history or from prior chats, ensuring focus on the current session's directives.

**Default Reply Policy:**
After processing `HEARTBEAT.md`, if the assistant determines that no action or attention is required based on the file's content, or if there are no pending tasks or explicit requests requiring attention, the default response should be `HEARTBEAT_OK`. This includes situations where `HEARTBEAT.md` does not contain any specific tasks or matters requiring attention.
- [] When configuring Obsidian vault cross-device sync via GitHub, user explicitly stated that the assistant has done GitHub sync for the user multiple times already, should be aware of the user's GitHub information, and required not to ask the user for GitHub-related information again.
- [] The AI is configured with specific operational preferences by the operator. In the current session, the AI must reply directly to the user and explicitly avoid using the `message` tool solely for sending progress updates.

Additionally, the AI is instructed to strictly read the `HEARTBEAT.md` file if it is present in the workspace context. When accessing `HEARTBEAT.md`, the system must use the precise and exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md` (case-sensitive). It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly. If, after reading and following `HEARTBEAT.md` and checking other contexts, nothing requires attention, the AI should reply with `HEARTBEAT_OK`.

Furthermore, the AI must not infer or repeat old tasks from prior chat sessions, ensuring focus on the current session's context.
- [] The AI is configured with specific operational preferences by the operator.

**Regarding communication style and interaction:** The user prefers a communication style that is concise and direct, explicitly avoiding verbosity or chattiness. For communication within the current session, the assistant is strictly instructed to reply directly to the user, integrating all updates and responses directly into the conversational flow. It is explicitly forbidden and reinforced that the `message` tool should not be used solely or merely for sending progress updates; instead, progress and other information should be communicated directly in the response, emphasizing a preference for direct and efficient interaction without unnecessary tool calls. The system must NOT use the `message` tool for the sole purpose of sending progress updates, implying a strong preference for more integrated and less interruptive communication for such updates. The assistant should combine information concisely to inform the user about results and potential issues.

**Regarding HEARTBEAT rules:** Furthermore, the system is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and follow its instructions strictly. If, after checking `HEARTBEAT.md` and other contexts, or after evaluating the current session context and instructions, the system determines that nothing requires its attention, it should reply with the specific phrase `HEARTBEAT_OK`.

**Regarding task handling and session independence:** The system is strictly instructed to operate within the context of the current session. It must not infer or repeat any tasks that were discussed or initiated in previous chat sessions, ensuring that each session is treated as a fresh and distinct context for task initiation and execution, and that its task list is independent and not carried over, unless explicitly instructed otherwise within the current session or `HEARTBEAT.md`.

**Regarding operational continuity:** To ensure operational continuity and efficiency, in scenarios where a previous model attempt failed or timed out, the assistant is expected to continue its work from the point it left off.
- [] The AI is configured with specific operational preferences by the operator.

**Communication Style:**
During the current session, the preferred communication method is to reply directly and concisely to the user. It is explicitly stated that the `message` tool should not be used for the sole purpose of sending progress updates, implying that direct replies are sufficient and preferred for such communications without unnecessary tool calls.

**System Directives:**
The AI is instructed to read the `HEARTBEAT.md` file located at the exact path `/root/.openclaw/workspace/HEARTBEAT.md` if it exists within the workspace context, and to follow its directives strictly.

**Idle State Response:**
If, after evaluating the current session context and instructions (including checking `HEARTBEAT.md` and other contexts), the system determines that nothing requires its attention, it should respond with the message `HEARTBEAT_OK`.

**Session and Task Management:**
Each session must be treated as distinct and independent. Regarding tasks, the system is instructed to operate strictly within the context of the current session. It must not infer or repeat any tasks that originated from prior chat sessions, ensuring that each session's task list is independent and not carried over, unless explicitly instructed to continue or carry over a task. Old tasks are not to be assumed ongoing or initiated based on previous interactions.
- [] 用户 `dbetter (cndbetter)` 明确指示，提供的两个 Tavily API key 应轮换使用。助理已记住此偏好，并已在内部确认后续将遵循此策略。助理还主动提出，如果用户需要，可以进一步实现调用脚本的**自动轮换 + 失败切换**功能，以提高稳定性和可用性。
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] The system is explicitly instructed not to infer tasks or repeat tasks that originated from previous chat sessions. This ensures that each session is treated as a distinct context, preventing the re-initiation of potentially outdated, completed, or abandoned tasks from prior interactions.
- [] When processing user input that looks like a multi-speaker transcript used for memory ingestion (indicated by `<ingest-reply-assist>` tag), the assistant should reply directly with 1-2 concise sentences. The reply should acknowledge or summarize the key points from the input. It is crucial not to output `NO_REPLY` or an empty reply, and not to fabricate facts beyond what is provided in the transcript and recalled memories.
- [] As per user request on 2026-03-12 UTC, Discord server ID 1472858437690855505 has been configured. The assistant should now only respond to messages in this server when the user is explicitly @mentioned as "@Reese". If not @mentioned, the assistant should not respond. This preference was implemented by modifying the configuration file `/root/.openclaw/openclaw.json`, specifically changing `channels.discord.guilds.1472858437690855505.requireMention` from `false` to `true`. This configuration was applied and the gateway restarted.
- [] The user has a standing interest in collecting and monitoring information related to the OpenClaw ecosystem, general cryptocurrency market trends, and advancements in the Artificial Intelligence field. These are recurring topics for daily information gathering.
- [] 用户要求将 Discord 服务器 `1472858437690855505` 设置为仅在被 `@Reese` 提及时才响应 (`requireMention = true`)。此外，Discord 频道中 Markdown 表格的显示偏好已从非法值 "on" 修正为 "bullets" (项目符号)。这些配置已在 `/root/.openclaw/openclaw.json` 中就位，并通过网关重启使其生效。重启后已验证未被@的消息不响应，而被@的消息则正常响应，且 Discord 频道中的 Markdown 表格现在以项目符号列表形式显示。
- [] 用户偏好在当前会话中直接接收回复，尤其是在发送进度更新时，不希望通过调用 `message` 工具来发送，而是直接在会话中回复。
- [] The system is instructed to read the `HEARTBEAT.md` file if it exists within the workspace context. It must strictly use the exact workspace file path `/root/.openclaw/workspace/HEARTBEAT.md`. It is explicitly forbidden to read `docs/heartbeat.md` or any other alternative path. All instructions within `HEARTBEAT.md` must be followed strictly, ensuring not to infer or repeat old tasks from prior chats. If, after reading and following `HEARTBEAT.md`, there is nothing that requires attention, the system should reply with `HEARTBEAT_OK`.
- [] When referring to the Liu Xiaopai digital twin, the terms '刘小排', '小排', and '刘小排分身' should be treated as interchangeable aliases for the same consultant. It is preferred to use '刘小排' directly without needing to add '分身'.
- [] 用户明确表示，为了简化操作，在调用数字分身顾问时，不希望额外输入“分身”两个字，直接使用顾问的人名即可。
例如，调用“刘小排分身”时，只需输入“刘小排”；或者直接使用`使用【刘小排】回答`、`刘小排怎么看这个事？`等方式。
此规则已写入`projects/digital-twin-advisor/REGISTRY.md`和`projects/digital-twin-advisor/USAGE.md`，并作为所有未来顾问的统一原则和默认设置。
- [] 用户dbetter明确要求助理/代理Reese_tx1#2494更改设置，使其仅在被@提及时才进行响应。此偏好已在对话中被助理/代理确认并实施，并已成为其与助理/代理交互的默认模式。
- [] 用户明确表示不愿意提供自己个人的ANTHROPIC_API_KEY给该项目部署使用，原因是用户的Claude Max订阅走oauth认证，担心多机器共用该API密钥会触发Anthropic的风控导致账号被封禁；用户因此提出了替代的API调用方案，并要求所有LLM调用都必须在用户自己的VPS上处理
- [] On 2026-03-17 07:55 GMT+8, in Discord Guild #思过崖 channel, user dbetter requested installation of opStem that can connect to openCrawling, and stated he will cooperate to provide any required information. Assistant recommended two matching skills from skillhub based on the user's thinking diary demand, and is waiting for the user to provide Obsidian vault information to complete the installation and configuration.
</relevant-memories>

[Thread starter - for context]
工作体系，提示词完善

Conversation info (untrusted metadata):
```json
{
  "message_id": "1483719067306037359",
  "sender_id": "825020287162122302",
  "conversation_label": "Guild #工作体系，提示词完善 channel id:1482904446588555367",
  "sender": "dbetter",
  "timestamp": "Wed 2026-03-18 14:49 GMT+8",
  "group_space": "1472858437690855505",
  "thread_label": "Discord thread #main › 工作体系，提示词完善",
  "topic_id": "1482904446588555367",
  "is_group_chat": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "dbetter (825020287162122302)",
  "id": "825020287162122302",
  "name": "dbetter",
  "username": "cndbetter",
  "tag": "cndbetter"
}
```

你：“测试LCM：记住这句话——我最喜欢吃的水果是西瓜”
