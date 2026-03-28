[2026-03-12 UTC] 任务：按用户要求，将当前 Discord 服务器设置为“只有 @ Reese 才响应”。
状态：配置已在 /root/.openclaw/openclaw.json 就位，待重启网关使其生效。
当前配置：
1) channels.discord.markdown.tables = "bullets"
2) channels.discord.guilds.1472858437690855505.requireMention = true
下一步：重启网关。
重启后验证：当前服务器中未@消息不响应，被@消息正常响应。
