# Elon Poly Trading System - Lessons Learned

## 自动交易系统铁律

### L1: 链上真相 > 本地状态
永远从链上读持仓余额，本地文件只作缓存。每次决策前先query CTF合约balanceOf。

### L2: 止损必须是独立进程
止损逻辑不能嵌在策略引擎里。独立watchdog进程，只做一件事：检查持仓P&L，超阈值立即market sell。

### L3: 摩擦成本会杀死你
低价bracket（$0.01-0.02）的spread比例极高（50-100%），反复进出=纯粹烧钱。最小持仓时间 > 1小时。

### L4: 熔断机制
- 单笔止损: -40%
- 单日熔断: -30%总资金
- 触发后: 全部平仓 + 停止daemon + 发告警

### L5: 权限隔离
- 分析cron: 只读
- 交易daemon: 只执行预定义规则
- 策略修改: 需要人工审批

### L6: negRisk CLOB机制
- 裸SELL YES = 不支持（需要持仓）
- BUY NO = 等效做空YES（有效）
- collateral = size × (1 - price)
