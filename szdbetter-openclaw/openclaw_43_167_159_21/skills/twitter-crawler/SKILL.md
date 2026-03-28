---
name: twitter-crawler
description: 按月分片抓取Twitter用户历史推文。Use /twitter-crawler to invoke.
disable-model-invocation: true
---

# Twitter Crawler Skill

## 核心能力
抓取 Twitter/X 指定用户的历史推文（支持长周期回溯）。

## 核心策略：时间切片 (Time Slicing)
由于 Twitter 搜索接口限制深度，直接抓取 "过去1年" 会被截断。本 Skill 采用 **按月切片** 策略：
1.  自动生成过去 12 个月的时间范围（例如 `since:2025-01-01 until:2025-02-01`）。
2.  对每个月单独执行 `bird search` 抓取。
3.  最后合并去重。

## 依赖
- **Bird CLI:** 必须安装 (`npm install -g openclaw-bird` 或本地已存在)。
- **Cookie:** 需要有效的 `auth_token` 和 `ct0` (配置在脚本中或环境变量)。

## 文件结构
- `deep_crawl.js`: 执行按月分片抓取。
- `merge_monthly.js`: 合并 JSON 并生成 Markdown。

## 使用方法
```bash
# 1. 抓取 (默认抓取 0xsunNFT 过去 12 个月)
node skills/twitter-crawler/deep_crawl.js

# 2. 合并
node skills/twitter-crawler/merge_monthly.js
```

## 数据位置
- 原始分片数据: `data/tweets/<username>/monthly/*.json`
- 最终 Markdown: `data/tweets/<username>/history_full_year.md`
