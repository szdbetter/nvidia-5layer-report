# Twitter Cookie 使用与测试记录

## 读取来源
- 文件：`~/.openclaw/.env`
- 字段：`ACCOUNT` / `AUTH_TOKEN` / `CT0` / `TOKEN_EXPIRE_DATE`

## 当前状态
- ACCOUNT: 0x_kraken
- AUTH_TOKEN 长度: 40
- CT0 长度: 52

## 测试结果
- 已成功读取 Cookie
- 使用 `xreach` 实测搜索/读用户失败
- 核心报错：`This request requires a matching csrf cookie and header`

## 判断
- Cookie 已更新到位
- 当前 xreach 链路未打通，不能确认可稳定抓取
- 当前更不能确认可安全发帖

## 后续建议
1. 升级或替换 xreach 链路
2. 在浏览器态验证 Cookie 是否仍有效
3. 分开验证读链路与发帖链路
