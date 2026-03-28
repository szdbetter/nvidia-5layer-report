# Roadmap

## 项目
- 名称：Polymarket 美伊战争单市场统一作战引擎
- 目录：`memory/projects/polymarket/`
- 当前线程：`# › Polymarket-🇺🇸🇮🇷美伊战争`

## 核心目标
1. 建立单市场 MVP：`US x Iran ceasefire by March 31? -> NO`
2. 建立统一引擎：同一流程内同时评估盘面与 OSINT
3. 建立可审计战报：价格、地址、成本、盈亏、OSINT 来源齐全
4. 建立可复盘证据链：订单号、tx hash、日志、输出样本

## 阶段
### Phase 1 基础设施与认知校准
- [done] 建立六文档
- [done] 核验 `.env`
- [done] 跑通 auth / quote / address
- [done] 回溯本频道策略历史

### Phase 2 统一作战引擎定型
- [done] 确定“盘口 + OSINT 合并”的统一策略
- [todo] 固定市场标识与 yes/no 映射
- [todo] 固定统一战报模板

### Phase 3 证据链补齐
- [todo] 核对持仓、成本、盈亏
- [todo] 补齐历史订单 / tx hash / 日志样本
- [todo] 修复监控脚本读取链路差异

### Phase 4 实盘闭环
- [todo] 在授权前提下执行最小实盘验证
- [todo] 输出完整复盘
