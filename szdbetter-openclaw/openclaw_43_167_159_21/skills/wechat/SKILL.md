---
name: wechat
description: Markdown→微信公众号草稿发布。Use /wechat to invoke.
disable-model-invocation: true
---

# wechat

将 Markdown 文章渲染为微信公众号草稿 payload，并可在凭证齐全时发布到微信公众号草稿箱。

## 适用场景
- 公众号文章排版预览
- 生成更清晰的微信公众号 HTML
- 将现有项目内容管线收口到统一入口
- 严格从 `.env` 读取公众号配置，禁止硬编码 token/secret

## 输入要求
- Markdown 文件路径
- 可选封面 media id、作者、摘要、文章内图片映射

## 环境变量
优先从 `/root/.openclaw/.env` 读取，其次从工作区 `.env` 或进程环境读取：
- `WECHAT_APP_ID`
- `WECHAT_APP_SECRET`
- `WECHAT_ACCESS_TOKEN`（可选；若提供则优先使用）
- `WECHAT_AUTHOR`（可选）
- `WECHAT_THUMB_MEDIA_ID`（可选）
- `WECHAT_DEFAULT_DIGEST`（可选）

## 常用命令
```bash
python3 skills/wechat/scripts/publish.py render \
  --input projects/digital-twin-advisor/content/kazike_boss_wechat_article_v1.md \
  --images-json skills/wechat/examples/body_images.json \
  --output-dir skills/wechat/out/demo
```

```bash
python3 skills/wechat/scripts/publish.py publish \
  --input projects/digital-twin-advisor/content/kazike_boss_wechat_article_v1.md \
  --thumb-media-id "$WECHAT_THUMB_MEDIA_ID" \
  --images-json skills/wechat/examples/body_images.json
```

## 输出
- `rendered.html`：排版后的微信 HTML
- `payload.json`：草稿接口 payload
- `summary.json`：渲染摘要

## 规则
- 所有公众号凭证与 token 一律从 `.env` 或环境变量读取
- 禁止在脚本中硬编码 access token / app secret / app id
- 优先使用本 skill 作为统一入口；项目目录保留文章与登记表等资产
