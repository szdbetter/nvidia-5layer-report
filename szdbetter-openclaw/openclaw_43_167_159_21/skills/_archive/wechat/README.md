# wechat skill

本地微信公众号发布技能，目标是把 `digital-twin-advisor` 已跑通的内容生产链路，与更清晰的 Markdown 排版能力合并到统一入口。

## 设计原则
1. 项目资产继续放在 `projects/...`
2. 发布入口统一放在 `skills/wechat`
3. 凭证只从 `.env` 读取
4. 默认先 `render` / `dry-run`，确认排版后再 `publish`

## 安装依赖
当前实现仅依赖 Python 标准库 + `python-dotenv`（环境中已存在）。

## .env 示例
优先读取 `/root/.openclaw/.env`，其次读取工作区根目录 `.env`，也支持直接导出为环境变量。

## 支持能力
- Markdown → 微信 HTML
- 标题、摘要、作者、封面配置
- 正文图片 media_id 映射插入
- 生成草稿 API payload
- 使用 `draft/add` 发布到草稿箱
- 安全 dry-run

## 推荐流程
1. 在 `projects/...` 下写文章 Markdown
2. 准备 `body_images.json`
3. 执行 `render`
4. 打开 `rendered.html` 预览
5. 确认无误后执行 `publish`
6. 将 Draft ID 回写到 `CONTENT_REGISTRY.md`

## body_images.json 格式
```json
[
  {"before_heading": "一、我为什么不再满足于“问 AI 一个问题”", "media_id": "MEDIA_ID_1"},
  {"before_heading": "二、我们不是在做功能，我们是在制造顾问", "media_id": "MEDIA_ID_2"}
]
```

## 命令示例
```bash
python3 skills/wechat/scripts/publish.py render \
  --input projects/digital-twin-advisor/content/kazike_boss_wechat_article_v1.md \
  --images-json skills/wechat/examples/body_images.json \
  --output-dir skills/wechat/out/demo
```

```bash
python3 skills/wechat/scripts/publish.py publish \
  --input projects/digital-twin-advisor/content/kazike_boss_wechat_article_v1.md \
  --images-json skills/wechat/examples/body_images.json \
  --thumb-media-id "$WECHAT_THUMB_MEDIA_ID"
```
