# Polymarket Runtime Package

目标：将 Polymarket 长期运行脚本迁移至 Fiona 节点执行。

## 包含文件
- `poly_runtime.py`
- `poly_unified_engine.py`
- `poly_monitor_job.py`
- `sync_to_fiona.sh`

## Fiona 侧目标目录
- `~/.openclaw/workspace/polymarket-runtime`

## 建议调度
- 分钟级：`python3 ~/.openclaw/workspace/polymarket-runtime/poly_unified_engine.py`
- 小时级心跳：检查节点 `connected` 状态 + 脚本目录/解释器可用性

## 依赖
- Python 3
- `requests`
- `web3`
- `py_clob_client`
- Fiona 本地需存在 `PRIVATE_KEY` 与 `BRAVE_API_KEY` 可被脚本读取
