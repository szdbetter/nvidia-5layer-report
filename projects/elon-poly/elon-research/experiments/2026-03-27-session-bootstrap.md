# 2026-03-27 新会话启动模板

## 用途

当当前会话上下文不足时，在新会话中快速恢复开发状态并继续执行。

## 新会话第一条消息建议

将下面这段原样发送给新的 Codex 会话：

```text
继续开发 /root/.openclaw/workspace/projects/elon-poly/elon-research。
先完整读取以下文件并以它们为唯一权威上下文，不要重新做架构设计：
1) /root/.openclaw/workspace/projects/elon-poly/docs/superpowers/specs/2026-03-27-elon-research-system-design.md
2) /root/.openclaw/workspace/projects/elon-poly/docs/superpowers/plans/2026-03-27-elon-research-system-implementation-plan.md
3) /root/.openclaw/workspace/projects/elon-poly/elon-research/datasets/reports/2026-03-27-phase-progress-log.md
4) /root/.openclaw/workspace/projects/elon-poly/elon-research/datasets/reports/2026-03-27-artifacts-index.md
5) /root/.openclaw/workspace/projects/elon-poly/elon-research/experiments/2026-03-27-next-handoff.md

约束：
- 所有文档输出使用中文。
- 所有中间结果持续写入 datasets/reports/。
- 每完成一步都更新 phase-progress-log 与 artifacts-index。
- 不做 dashboard，不做自动交易，只做研究与验证链路。

当前优先任务：
1) 推进逐条历史推文时间线 A 级来源（X API 历史权限或等价来源）。
2) 寻找替代成交来源或抓取路径，绕过单 market `offset > 3000` 限制。
3) 只有在更强数据前提下，再进入下一轮策略验证。
```

## 新会话验证清单

新会话启动后，应先验证：

1. 能读取 `datasets/normalized/` 与 `datasets/reports/`。
2. `pytest -q` 通过。
3. 能执行：
   - `python -m elon_research.cli normalize --project-root .`
   - `python -m elon_research.cli backtest --project-root .`

## 进入新会话后的最小事实集

新会话应先接受以下事实，避免重复探索：

1. 跨周样本已扩展到 8 周。
2. 事件级成交抓取当前只能稳定拿到每周 `3500` 条，因为 `offset > 3000` 会返回 400。
3. 已确认公开 `data-api /trades` 中 `slug / market / conditionId / asset` 过滤不可依赖；高流动单 market 抽样 `8/8` 命中 `offset > 3000` 上限。
4. `proxy_tweet_windows` 已接入：
   - `tweet_delta_5m`
   - `tweet_delta_15m`
   - `tweet_delta_1h`
   - `tweet_delta_6h`
5. 修复后，跨周统一参数结果与 proxy window 结果都未观察到可执行弱信号。
6. 当前阶段性判断：
   - 尚未观察到可辩护的可交易 edge
   - 主阻塞仍是逐条推文时间线与单 market 成交完整性

## 失败恢复

如果新会话没有遵循上述文档上下文，立即中断并重发“新会话第一条消息建议”，不要让其自由发挥。
