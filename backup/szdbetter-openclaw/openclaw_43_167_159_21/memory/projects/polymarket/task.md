# Task

## 已完成
- [done] 建立 Polymarket 六文档目录
  - proof: `memory/projects/polymarket/{roadmap,task,issue,cowork,decision,learning}.md`

- [done] 从当前频道回溯项目关键历史并沉淀策略
  - proof: Discord 频道 `1480446033531240469` 历史消息自 `1480500827104743434` 至 `1480574159506378874`

- [done] 核验真实环境变量结构
  - proof: `/root/.openclaw/.env` 中存在 `POLYMARKET_API_KEY` / `POLYMARKET_API_SECRET` / `POLYMARKET_API_PASSPHRASE` / `PRIVATE_KEY`

- [done] 跑通认证链路
  - proof: `python3 scripts/polymarket_auth.py`
  - output: `API Credentials successfully derived/created.`

- [done] 跑通市场报价链路
  - proof: `python3 scripts/check_market_price.py`
  - output: `Last trade price for 'No': 0.43 | Best Ask: 0.99 | Best Bid: 0.01`

- [done] 跑通地址推导链路
  - proof: `python3 scripts/get_address.py`
  - output: `0x9b8dEbcABAa772105Af586e278380B4E31bb4Bb8`

- [done] 明确输出边界：项目相关信息只发当前线程
  - proof: 用户消息 `1480574159506378874`


- [done] 修复统一引擎私钥读取链路
  - proof: `scripts/poly_unified_engine.py`
  - output: 已支持 `os.environ -> config/.secrets -> /root/.openclaw/.env`

- [done] 重跑统一引擎并恢复盘口链路
  - proof: `python3 scripts/poly_unified_engine.py`
  - output: `当前标的 'NO' 中间价: $0.775 (持仓成本: $0.77)`

- [done] 2026-03-09 23:15 CST 定时战报执行并主动群发
  - proof: `python3 scripts/poly_unified_engine.py`
  - output: `NO中间价: $0.775 | OSINT: 40% | 继续蛰伏观察`

## 待办
- [done] 将 Polymarket 分钟级巡检与统一引擎迁移到 Fiona 节点执行
  - 目标：全部运行面切到 Fiona，异常回流 Reese
  - 范围：统一引擎、分钟级巡检、异常告警链路
  - 结果：Fiona 已创建 `~/.openclaw/workspace/polymarket-runtime`，已写入运行脚本、建立 `.venv`、补齐 `config/.secrets`、完成统一引擎与监控脚本实跑测试
  - proof:
    - Fiona 实跑：`~/.openclaw/workspace/polymarket-runtime/.venv/bin/python poly_unified_engine.py`
    - 输出：`NO Last $0.680 | Mid $0.670 | 持仓 6.52 NO | TEST_PULSE_OK`
    - Fiona 实跑：`~/.openclaw/workspace/polymarket-runtime/.venv/bin/python poly_monitor_job.py`
    - 输出：`Price stable. No risk thresholds breached.`
    - 旧 5min cron 已禁用：`1da9b722-5471-4c8a-a36a-e0f6561e1b73`

- [done] 校准历史持仓、成本、盈亏口径
  - 结论：当前 NO 持仓为 `6.52`；由两笔已确认成交构成：`1.52 @ 0.56` + `5 @ 0.77`
  - 加权平均成本：约 `0.7216`
  - 当前价格：`0.79`
  - 当前未实现盈亏：约 `+0.4464 USDC`（按 6.52 shares 与加权成本估算）
  - 关键证据：
    - trade id `1f0fc73a-1fbc-49fd-a9a4-7f6055c51a92` | tx `0x6e8adb794080df2e64a4ca1c211c9a9f1dc951859146937dda62054f6355f4e8` | `1.52 @ 0.56`
    - trade id `61639982-c6f7-4866-bf3d-a23a39f243d1` | tx `0x2a19d2838cd466c8336635c47df87b2e4bc9cb133e71366c4077e1110ac5031a` | `5 @ 0.77`
    - 余额输出：`NO Token Balance: 6.52`
  - proof: `python3` 调用 `client.get_trades()` + `python3 scripts/check_earnings.py`

- [done] 固定当前交易市场元数据
  - market slug: `us-x-iran-ceasefire-by`
  - target market: `US x Iran ceasefire by March 31?`
  - condition id: `0x3c6bcb7da14ea576e5af25547dbd96f2bb24ac34e748e76aecff2ee9195dd1ac`
  - token ids / CLOB ids: `5708561660601459805512817131601230493971589760294984590237789749933853841330` (Yes), `51938013536033607392847872760095315790110510345353215258271180769721415981927` (No)
  - yes/no 映射: `Outcomes: ["Yes", "No"]`，当前作战方向为 `NO`
  - proof: `python3 scripts/get_ceasefire_market.py`

- [done] 固定统一战报模板
  - 模板字段：时间 / 市场 / 价格(Last/BestBid/BestAsk/Mid) / Polygon 地址 / 持仓 / 成本 / 浮盈亏 / OSINT 概率 / OSINT 来源方法 / 执行动作
  - 当前已落地字段：时间、市场、地址、NO Last/Bid/Ask/Mid、持仓、加权成本、未实现盈亏、OSINT 概率、OSINT 来源、统一动作
  - proof: `python3 scripts/poly_unified_engine.py` 当前输出已完整覆盖模板字段

- [done] 监控阶段接管原“最小闭环验证”任务
  - 原任务：approve -> quote -> tiny order -> result capture
  - 当前判断：用户已明确说明“已经下单了，现在在监控阶段”，因此不再重复执行最小测试单闭环
  - 替代结果：已进入实盘后监控，现以真实持仓、真实成交、真实 tx hash、实时盘口与 OSINT 联合监控作为主流程
  - proof：持仓 `6.52 NO`、tx `0x6e8adb794080df2e64a4ca1c211c9a9f1dc951859146937dda62054f6355f4e8`、tx `0x2a19d2838cd466c8336635c47df87b2e4bc9cb133e71366c4077e1110ac5031a`、`python3 scripts/poly_unified_engine.py`
