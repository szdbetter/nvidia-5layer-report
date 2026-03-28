---
name: ppt-nano
description: 生成白板风格PPT，用户说「ppt-nano」「生成PPT」「做PPT」「白板风格PPT」等关键词时
allowed-tools: ["exec", "read", "write", "message", "web_search"]
metadata: {"openclaw": {"requires": {"bins": ["ov"]}, "user-invocable": true, "emoji": " ✅"}}
---


# PPT-Nano 技能 — 白板板书风格PPT生成

## 🚨 触发条件
用户说「ppt-nano」「生成PPT」「做PPT」「白板风格PPT」等关键词时，**必须严格按以下流程执行，不可跳步！**

---

## ✅ 标准执行流程（5步，必须按顺序）

### 第一步：告知风格

立即回复：

> 🖊️ **1. 白板板书风格**
> 真实白板照片 + shufa马克笔手写 + 手绘插图，黑/蓝/红三色马克笔


---

### 第二步：接收文案，整理确认表（必须输出表格）

收到文案后，**立即整理成确认表**发给用户，格式：

> 📋 梳理如下，请确认：
>
> | 页码 | 页面类型 | 参考图 | 内容摘要 |
> |------|---------|--------|---------|
> | 封面 | 首页 | cover.jpg | 主标题 / 副标题 |
> | P1 | 内容页 | content.jpg | 标题 / 要点摘要 |
> | P2 | 图表页 | chart.jpg | 标题 / 数据摘要 |
> | ... | ... | ... | ... |
>
> 共 X 页，请确认页面分配是否正确，确认后说"启动生成"！

**页面类型判断规则：**
- 有时间轴/流程/组织架构 → **导航页** navigation.jpg
- 有数据表格/数字对比 → **图表页** chart.jpg
- 有场景故事/对话泡泡 → **内容页** content.jpg
- 纯文字列表/要点 → **文字页** text.jpg（=content.jpg）
- 封面 → **首页** cover.jpg
- 结尾 → **尾页** closing.jpg（=content.jpg）

等用户确认后再进入第三步。

---



### 第三步：依赖检查（首次使用或不确定时执行）

```bash
python -c "import openai, PIL; print('ok')"
```

如果失败，先安装：
```bash
python -m pip install openai pillow
```

---

### 第四步：逐页生成并发预览

**每页命令模板（严格执行）：**
```bash
python {baseDir}/scripts/generate_image.py \
  --prompt "{固定前缀}{页面专属提示词}" \
  --filename "{输出文件名}.jpg" \
  --resolution 2K \
  --aspect-ratio 16:9 \
  -i "{参考图绝对路径}"
```

**关键参数说明：**
- `-i` 传入参考图（image-to-image 模式，必须带）
- `--resolution` 固定用 `2K`（Seedream 支持 `2K` / `3K`，不支持 1K）
- `--aspect-ratio` 固定用 `16:9`
- `--filename` 必须以 `.jpg` 结尾（Seedream 输出固定为 JPEG）
- 每次调用只生成一页

**固定前缀（一字不差，每页必须带）：**
```
按参考图出图，原图的白板和背景保留不变，内容文字配图按文案重新设计，中文必须是马克笔shufa笔触风格，配图手绘风格。Chinese text MUST use thick shufa-style ink brush marker calligraphy — bold chunky strokes, NOT printed font. 颜色规则：文字的颜色规则黑色：主标题、正文、蓝色：副标题、数据标注、补充信息、红色：强调词、结论句、圆圈高亮。配图的颜色规则按图片内容用红蓝马克笔适配。
```

**参考图路径（`{baseDir}/styles/whiteboard/pages/`）：**
```
├── cover.jpg       ← 首页专用
├── chart.jpg       ← 图表页专用
├── navigation.jpg  ← 导航页专用
├── content.jpg     ← 内容页/文字页/尾页共用
├── closing.jpg     ← 尾页（可替代 content.jpg）
└── text.jpg        ← 文字页（=content.jpg）
```

**规则：**
- 每页必须带参考图（`-i`），不同页型严禁混用参考图
- 以脚本输出的 `MEDIA:` 行为准获取生成图片路径，不依赖 stderr 解析
- 只输出保存路径，不读取图片内容

---

### 第五步：所有页确认后合成 .pptx

所有页面确认后：
```bash
pip install --break-system-packages python-pptx
python3 合成脚本
```

合成完成后将 .pptx 文件发给用户。

---

## 📁 文件位置
- 配置：`skills/ppt-nano/styles/styles.json`
- 参考图：`skills/ppt-nano/styles/whiteboard/pages/`
- 输出：`ppt_outputs/lobster_diary/`、`ppt_outputs/kickoff/`

## ⚠️ 常见错误（禁止）
- ❌ 不问风格直接问文案
- ❌ 收到文案不整理确认表直接生成
- ❌ 不传 @ref 或混用参考图
- ❌ 省略固定前缀
- ❌ 用错参考图（如内容页用了chart.jpg）
