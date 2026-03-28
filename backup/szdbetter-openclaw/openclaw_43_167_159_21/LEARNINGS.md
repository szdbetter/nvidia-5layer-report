- 2026-03-10: `scripts/poly_unified_engine.py` 的 cron 调用若使用 `python` 会因环境缺失失败；预防机制：统一改用 `python3 scripts/poly_unified_engine.py` 执行，避免重复报错。
- 2026-03-10 00:10 UTC: 再次验证 `python` 在 cron 环境下不存在，已按自愈机制切换并确认 `python3 scripts/poly_unified_engine.py` 稳定输出 `TEST_PULSE_OK`；后续同类任务默认禁用 `python` 调用。

## 2026-03-10 Gateway 持续崩溃根因
- **症状**: `openclaw gateway status` 连接失败，watchdog 自愈无效，heartbeat 持续报警
- **根因**: `openclaw.json` 中 `plugins.entries.memory-openviking` 包含废弃非法字段（mode/targetUri/autoRecall/autoCapture/configPath/port/baseUrl），导致配置验证失败
- **修复**: `openclaw doctor --fix` 自动清理非法字段
- **预防**: 修改 openclaw.json 时必须先用 `openclaw doctor` 验证，禁止手动添加未知字段
- **附加**: cron 环境缺少 nvm PATH，已创建 `/usr/local/bin/node` symlink 指向 nvm node

## 2026-03-10: Fiona→VPS DB 同步架构缺失
**错误**: 假设 Fiona daemon 写本地 SQLite 后 VPS Datasette 能自动看到数据。实际上是两个独立 SQLite 文件，无任何同步机制。上报"150行已写入"时未验证 VPS 侧数据。
**根因**: 两台机器的 `~/.openclaw/workspace/data/ops.db` 是完全独立的文件。SQLite 无网络访问能力。
**修复**: SSH 密钥 Fiona→VPS + launchd 定时任务每 2 分钟 `sqlite3 .backup` + `scp` 同步。
**预防**: 任何跨机器数据流必须显式验证端到端连通性。声称"数据已写入"时必须从最终消费端（Datasette/VPS DB）验证，不能只看生产端。
