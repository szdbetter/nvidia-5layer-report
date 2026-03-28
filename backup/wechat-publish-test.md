# 公众号测试与踩坑记录

更新日期：2026-03-11 UTC

## 1. 文章学习结果
目标文章：`https://mp.weixin.qq.com/s/wsDcVNaDfcKRtqOJlXJ8-w`

实际抓取结果：
- 直接用 `web_fetch` 只能拿到标题和极少量页面壳内容
- 正文与图片细节未被可靠提取

结论：
- 微信文章页面对通用抓取极不友好
- 后续应优先使用专用公众号抓取链，而不是直接指望通用网页抽取

## 2. 当前 .env 检查结果
已发现：
- `WX_GZH_APPID`：已配置
- `WX_GZH_APPSECRET`：已配置，但格式可疑
- `ZILIU_API_KEY`：已配置

关键问题：
- `WX_GZH_APPSECRET` 当前值为：`WX_GZH_APPSecret＝3762b69455e128c4ccaa94890b8597b7`
- 这里包含了错误前缀和全角等号，不是纯 secret

## 3. 公众号官方 API 实测
测试：`cgi-bin/token`
结果：
- 返回 `errcode: 40125`
- 含义：`invalid appsecret`

结论：
- 当前公众号官方 API 还不能用
- 必须先修正 `.env` 中的 `WX_GZH_APPSECRET`

## 4. 字流 API 实测
已发现：
- `ZILIU_API_KEY` 已配置

结果：
- 未找到可解析的公开 API 域名
- 直接探测常见域名全部 DNS 失败

结论：
- 仅有 API key 还不够
- 还缺明确的 API base / 接口文档 / SDK 使用方式

## 5. 关于文章配图风格判断
虽然正文未完整抓下，但从描述目标看，常见是这种路径：
- 扁平科技风
- 大留白
- 深浅对比背景
- 卡片式信息块
- 渐变高光
- 简洁几何元素
- 无过多写实细节

适合固化的默认 prompt 方向：
- `tech editorial cover`
- `clean minimal layout`
- `gradient lighting`
- `modern UI card composition`
- `high-end technology article illustration`
- `square or 16:9 social cover`

## 6. 现在能否发公众号？
不能确认。

阻塞点：
1. 官方公众号 appsecret 当前无效
2. 字流 API 缺 base / 文档 / 调用方式
3. 未完成草稿箱 API 打通

## 7. 下一步建议
1. 修正 `.env`：把 `WX_GZH_APPSECRET` 改成纯 secret 值
2. 提供字流 API 文档或 base URL
3. 先做最小闭环：获取 access_token → 新建草稿 → 上传封面/内容
4. 文章抓取改走专用公众号链路
