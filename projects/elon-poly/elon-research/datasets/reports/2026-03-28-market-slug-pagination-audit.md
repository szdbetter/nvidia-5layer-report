# 公开成交接口过滤行为核验

## 目标

验证 `https://data-api.polymarket.com/trades` 是否支持通过 market 级过滤器绕过单事件 `offset > 3000` 限制。

## 核验结果

### 1) `eventId` 过滤有效

- 当请求参数包含 `eventId=278377` 时，返回结果中的 `eventSlug` 保持单一：
  - `elon-musk-of-tweets-march-20-march-27`

### 2) `slug / market / conditionId / asset` 过滤不可依赖

- 仅传 `slug=elon-musk-of-tweets-march-20-march-27-260-279` 时，返回结果会混入多个无关市场。
- `market`、`conditionId`、`asset` 在公开接口上的行为同样不可作为可辩护过滤条件。
- `side=BUY/SELL` 会改变买卖方向，但不能限制到目标 market。

## 结论

- 当前公开 `data-api /trades` 中，只有 `eventId` 过滤可以作为可信研究输入使用。
- 这意味着研究链路当前只能获得“事件级有效但截断”的成交样本。
- 想要绕过单 event `offset > 3000` 限制，必须依赖替代成交来源，而不是继续尝试当前公开过滤器。
