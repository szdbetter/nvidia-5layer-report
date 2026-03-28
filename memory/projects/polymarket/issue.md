# Issue

## 2026-03-10 Fiona 迁移阻塞
- 状态：open
- 阻塞 1：Fiona 节点本地不存在 Polymarket 运行脚本副本。
- 阻塞 2：Fiona 可读配置中缺少 `PRIVATE_KEY`；当前仅检测到 `BRAVE_API_KEY`。
- 阻塞 3：Fiona Python 环境缺少 `web3` 与 `py_clob_client` 依赖，脚本无法直接运行。
- 已验证：Fiona 在线，Python 3.14.3 可用，OpenClaw workspace 存在，适合作为执行面。
- 建议动作：同步 `polymarket-runtime/` 运行包、补齐节点密钥读取路径、安装 Python 依赖后再切换分钟级任务。

## Open
### ISSUE-001 历史证据链不完整
- 状态：resolved
- 问题：频道里出现了 `5 shares`、`6.52 shares`、成本 `0.77`、成本 `0.56` 等多个口径，但未统一到订单级证据。
- 影响：当前盈亏与仓位结论不可完全审计。
- 修复：已补抓两笔成交、tx hash 与余额输出，确认当前 NO 持仓 `6.52 = 1.52 @ 0.56 + 5 @ 0.77`，加权成本约 `0.7216`。
- 证据：频道消息 `1480514203725987872`、`1480554126986317965`；trade `1f0fc73a-1fbc-49fd-a9a4-7f6055c51a92` / tx `0x6e8adb794080df2e64a4ca1c211c9a9f1dc951859146937dda62054f6355f4e8`；trade `61639982-c6f7-4866-bf3d-a23a39f243d1` / tx `0x2a19d2838cd466c8336635c47df87b2e4bc9cb133e71366c4077e1110ac5031a`；余额输出 `NO Token Balance: 6.52`。

### ISSUE-002 监控脚本配置读取链路曾不一致
- 状态：resolved
- 问题：统一引擎多次报“找不到私钥”，说明脚本内部读取链路存在偏差。
- 影响：虽然 `poly_unified_engine.py` 已恢复，但同项目内脚本配置口径仍不统一，影响证据链一致性。
- 修复：已抽出 `scripts/poly_runtime.py` 作为统一运行时，统一 `PRIVATE_KEY` 读取、盘口快照、钱包余额、盈亏计算；并已修复 `get_address.py`、`check_market_price.py`、`check_earnings.py`、`polymarket_monitor.py`、`poly_monitor_job.py`、`poly_unified_engine.py` 的旧路径/旧成本口径。
- 结果：所有监控脚本现已可直接通过 `python3` 正常执行，并输出一致口径的数据。
- 证据：本轮连续执行 `python3 scripts/check_market_price.py`、`python3 scripts/check_earnings.py`、`python3 scripts/poly_monitor_job.py`、`python3 scripts/poly_unified_engine.py` 均成功。

### ISSUE-003 历史外发污染
- 状态：resolved
- 问题：项目相关结果曾发到其他 Discord 频道，违背当前集中归档原则。
- 影响：证据分散，检索困难。
- 修复：从现在起只在当前线程输出，并将该要求写入 decision/learning。
- 证据：用户消息 `1480574159506378874`。
