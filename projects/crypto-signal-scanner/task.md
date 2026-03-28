# 📋 Task List - Crypto Signal Scanner

## Phase 1 任务（按优先级排序）

### P0: 基础设施
- [ ] **T1: 创建项目目录和配置**
  - 创建 `scripts/css/` 目录
  - 创建 `config.json`（监控币种列表、阈值参数、通知频道ID）
  - 所有配置从文件读取，禁止硬编码
  - 指派：subagent | 预估：15min

### P0: 新币狙击（ROI最高）
- [ ] **T2: 币安公告监控脚本**
  - 轮询 `bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=48`
  - 解析标题关键词：`Will Add`, `Will List`, `HODLer Airdrops`, `Launchpool`
  - 新公告写入SQLite `signals` 表（去重用article_id）
  - 输出JSON格式信号：`{type, symbol, title, timestamp}`
  - 指派：subagent | 预估：30min

- [ ] **T3: 新币上线cron任务**
  - 创建OpenClaw cron，每60秒执行T2脚本
  - 发现新信号 → Discord通知（指定频道）
  - 格式：`🚨 新币上线 | KAT (Katana) | 上线现货+合约+Earn | [公告链接]`
  - 指派：Reese | 预估：15min

### P1: 异常波动扫描
- [ ] **T4: 全市场24h行情扫描脚本**
  - 拉取 `api/v3/ticker/24hr` 全市场数据
  - 过滤规则：
    - 涨幅 >15% 且 成交量 >$500万 → 🟢 强势信号
    - 跌幅 >12% 且 成交量 >$500万 → 🔴 超跌信号
    - 成交量突增 >300%（vs 7日均量）→ 🟡 异动信号
  - 结果写入SQLite `signals` 表
  - 指派：subagent | 预估：45min

- [ ] **T5: 异常波动cron任务**
  - 创建OpenClaw cron，每5分钟执行T4脚本
  - 去重：同一币种同一类型信号，6小时内只通知一次
  - Discord通知格式：`📊 异动 | BONK -9.3% | 量$953万 | 类型：超跌`
  - 指派：Reese | 预估：15min

### P1: 通知与日志
- [ ] **T6: SQLite信号表schema**
  - 表名：`signals`
  - 字段：id, type(listing/surge/dump/volume), symbol, price, change_pct, volume_usd, source, raw_data(JSON), notified(bool), ts
  - 在现有 `ops.db` 中创建
  - 指派：subagent | 预估：10min

- [ ] **T7: Discord通知频道**
  - 确认/创建 `#crypto-signals` 频道
  - 需要老板确认用哪个频道
  - 指派：Reese | 预估：5min（需老板输入）

### P2: 验证
- [ ] **T8: 端到端测试**
  - 手动触发T2和T4脚本，验证信号输出
  - 验证Discord通知送达
  - 验证SQLite写入正确
  - 指派：Reese | 预估：20min

---

## 执行顺序
```
T1(基础) → T6(DB) → T2(公告脚本) → T4(波动脚本) → T7(频道) → T3(公告cron) → T5(波动cron) → T8(测试)
```

## 待老板确认
1. Discord通知发到哪个频道？新建 `#crypto-signals` 还是用现有频道？
2. 异常波动阈值（涨>15%/跌>12%）是否合理，还是要调？
3. Phase 1跑通后多久评估进Phase 2？
