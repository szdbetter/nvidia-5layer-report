# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Twitter 抓取

- **单条推文：** `curl "https://r.jina.ai/https://x.com/USER/status/ID"` （Jina Reader，最稳定）
- **批量抓取：** `bird search "from:USER since:YYYY-MM-DD until:YYYY-MM-DD"` （需要 cookie，按月切片避免深度限制）
- **技能：** `skills/twitter-crawler/deep_crawl.js` （自动按月分批抓取）

## 图片生成

- **Imagen 4：** Google Gemini API 支持 `imagen-4.0-generate-001` / `imagen-4.0-ultra-generate-001`
- **脚本：** `/tmp/imagen_generate.js` （直接调 API，输出到 `workspace/generated_images/`）
- **API Key：** 存在 `openclaw.json` 的 `skills.entries."nano-banana-pro".apiKey`
- **Discord 发图：** `message` tool 的 `media` 参数，支持本地路径

## Moltbook

- **API Key：** `~/.config/moltbook/credentials.json`
- **Base URL：** `https://www.moltbook.com/api/v1`
- **账号：** shuhu1（已认领）
- **文档：** https://www.moltbook.com/skill.md

Add whatever helps you do your job. This is your cheat sheet.
