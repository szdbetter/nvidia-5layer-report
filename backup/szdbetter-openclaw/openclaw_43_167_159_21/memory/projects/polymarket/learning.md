# Learning

## 2026-03-09 用户约束沉淀
- Polymarket 项目相关内容只允许发当前线程，不得再外发到其他 Discord 群或频道；除非用户明确要求。
- Discord 超过 100 字必须使用 markdown。
- 除非缺资源/权限，否则直接执行并给结果，不抛过程问题。

## 2026-03-09 从本频道学到的项目历史
- 09:41-09:42：用户要求建立持续监控机制，证明后台可自主运行；随后建立价格监控与 Cron 哨兵。
- 09:47-09:49：用户要求解释靖安文章的数据源；由此建立六维 OSINT 模型与 `scripts/poly_osint_report.py`。
- 10:11-10:12：用户要求将盘口与 OSINT 合并为一个 30 分钟统一引擎；随后形成 `scripts/poly_unified_engine.py` 的设计方向。
- 10:28 起：用户要求提高主动汇报频率到 5 分钟，测试自主汇报机制。
- 12:44：用户要求战报增加 Polygon 地址、成本价、盈亏、OSINT 来源解释。
- 22:33：用户要求 decision 不只是边界，而应记录“策略、原因、优势”。

## 2026-03-09 已知策略事实
- 当前单市场目标：`US x Iran ceasefire by March 31? -> NO`
- 已知持仓历史记录：5 shares NO，后续记录出现 6.52 shares NO
- 已知成本记录：`0.77` 与后续 `0.56` 粗算浮盈口径并存，后续需统一以链上/订单记录校准
- 已知地址：`0x9b8dEbcABAa772105Af586e278380B4E31bb4Bb8`

## 2026-03-09 当前缺口
- 历史订单号、tx hash、精确持仓、精确成本还未统一固化到 task/issue 证据链
- 需要在下一轮核验中补齐链上或订单级证明

## 2026-03-10 新协作规则
- Reese 定位固定为“大脑”：负责策略制定、开发组织、任务分发、日常执行监控与节点调度。
- Fiona 节点定位为 Polymarket 主执行面：承接分钟级巡检与策略运行。
- 发生异常时，不做静默吞错，必须回流给 Reese 统一判断与汇报。

## 2026-03-10 Fiona 迁移落地经验
- Fiona 使用 macOS 的 externally-managed Python，直接 `pip install --user` 会被 PEP 668 拦截；正确路径是项目内 `.venv` 隔离安装。
- Fiona 原 `.env` 中已有 `BRAVE_API_KEY`，但没有 `PRIVATE_KEY`；迁移时需显式落到 `~/.openclaw/workspace/config/.secrets`。
- 远程节点超长安装容易触发 gateway timeout；应拆成“执行 + 日志校验”两步，避免误判为失败。
