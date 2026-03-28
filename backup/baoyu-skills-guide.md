# baoyu-skills 安装与使用指南

## 一、这是什么？

宝玉（JimLiu）分享的一套 **Claude Code / OpenClaw 专用技能集**，核心解决 **研报级图表生成** 问题。

### 核心能力矩阵

| 插件包 | 核心技能 | 解决什么问题 |
|--------|----------|--------------|
| **content-skills** | `baoyu-infographic`<br>`baoyu-xhs-images`<br>`baoyu-cover-image`<br>`baoyu-slide-deck`<br>`baoyu-comic` | 专业信息图、小红书配图、封面、PPT、漫画 |
| **ai-generation-skills** | `baoyu-image-gen` | 统一的图片生成后端（OpenAI/Google/阿里/Replicate） |
| **utility-skills** | `baoyu-markdown-to-html`<br>`baoyu-translate` | 排版、翻译等工具 |

---

## 二、你之前生图为什么达不到研报级？

**核心差距不在模型，在"布局+风格"的体系化Prompt设计。**

### baoyu-skills 的杀手锏：二维风格系统

#### 1. `baoyu-infographic`：20 种布局 × 17 种风格

**布局（信息结构）**：
- `bridge`：问题→解决方案、跨越鸿沟
- `pyramid`：层级金字塔、马斯洛需求
- `funnel`：转化漏斗、筛选过程
- `timeline-horizontal`：历史、时间线事件
- `venn`：重叠概念、韦恩图
- `mind-map`：头脑风暴、思维导图
- `comparison-table`：多因素对比
- `fishbone`：根因分析、鱼骨图
- `priority-quadrants`：四象限矩阵、优先级
- ...共 20 种

**风格（视觉美学）**：
- `craft-handmade`（默认）：手绘插画、纸艺风格
- `technical-schematic`：蓝图、等距 3D、工程图 ← **研报级**
- `corporate-memphis`：扁平矢量人物、鲜艳填充
- `claymation`：3D 黏土人物、定格动画感
- `cyberpunk-neon`：霓虹灯光、暗色未来感
- `bold-graphic`：漫画风格、网点、高对比
- `aged-academia`：复古科学、泛黄素描
- `origami`：折纸形态、几何感
- `subway-map`：地铁图、彩色线路
- `ikea-manual`：极简线条、组装说明风
- ...共 17 种

**研报级组合推荐**：
```bash
/baoyu-infographic article.md --layout pyramid --style technical-schematic
/baoyu-infographic article.md --layout funnel --style corporate-memphis
/baoyu-infographic article.md --layout comparison-table --style aged-academia
```

#### 2. `baoyu-xhs-images`：9 种风格 × 6 种布局

**风格**：
`cute`（默认）、`fresh`、`warm`、`bold`、`minimal`、`retro`、`pop`、`notion`、`chalkboard`

**布局**：
- `sparse`（1-2点）：封面、金句
- `balanced`（3-4点）：常规内容
- `dense`（5-8点）：知识卡片、干货总结
- `list`（4-7项）：清单、排行
- `comparison`（双栏）：对比、优劣
- `flow`（3-6步）：流程、时间线

#### 3. `baoyu-cover-image`：五维定制系统

**类型 × 配色 × 渲染 × 文字 × 氛围 = 54 种独特效果**

- **类型**：hero、conceptual、typography、metaphor、scene、minimal
- **配色**：warm、elegant、cool、dark、earth、vivid、pastel、mono、retro
- **渲染**：flat-vector、hand-drawn、painterly、digital、pixel、chalk
- **文字**：none、title-only、title-subtitle、text-rich
- **氛围**：subtle、balanced、bold

---

## 三、安装方式

### 已安装（本地复制）
```bash
/root/.openclaw/workspace/skills/baoyu-image-gen/
/root/.openclaw/workspace/skills/baoyu-infographic/
/root/.openclaw/workspace/skills/baoyu-cover-image/
```

### ClawHub 安装（推荐）
```bash
clawhub install baoyu-image-gen
clawhub install baoyu-infographic
clawhub install baoyu-cover-image
```

---

## 四、使用示例（研报级）

### 1. 专业信息图
```bash
# 自动推荐布局+风格
/baoyu-infographic path/to/content.md

# 研报级：金字塔+蓝图风
/baoyu-infographic path/to/content.md --layout pyramid --style technical-schematic

# 研报级：漏斗+企业扁平风
/baoyu-infographic path/to/content.md --layout funnel --style corporate-memphis
```

### 2. 小红书知识卡片
```bash
# 干货总结（dense布局）
/baoyu-xhs-images article.md --layout dense --style minimal

# 流程图
/baoyu-xhs-images article.md --layout flow --style tech
```

### 3. 文章封面
```bash
# 五维定制
/baoyu-cover-image article.md --type conceptual --palette cool --rendering digital --text title-subtitle --mood bold
```

---

## 五、底层图像生成：`baoyu-image-gen`

### 支持的 Provider
| Provider | 模型 |
|----------|------|
| **OpenAI** | `gpt-image-1.5`, `gpt-image-1` |
| **Google** | `gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview` |
| **DashScope** | 阿里通义万象 |
| **Replicate** | `google/nano-banana-pro` |

### 关键特性
1. **必须先配置 EXTEND.md**（首选项）
2. 支持批处理模式
3. 支持参考图片（Google multimodal / OpenAI edits）
4. 支持多种质量和尺寸

### 使用示例
```bash
# 基础
bun /root/.openclaw/workspace/skills/baoyu-image-gen/scripts/main.ts --prompt "A cat" --image cat.png

# 高质量
bun ... --prompt "..." --image out.png --quality 2k

# 指定比例
bun ... --prompt "..." --image out.png --ar 16:9

# 批处理
bun ... --batchfile batch.json
```

---

## 六、与微信文章对比

那篇微信文章讲的是傅盛直播、OpenClaw实战案例，**不是生图教程**。

核心信息：
- 养一个顶配 Agent 日均 $100-200
- 国产模型一天几块到几十块
- Token 两年降 90%+
- 最重要的事：学会提问

---

## 七、我的判断

### 为什么你之前生图达不到研报级？

**三个核心原因**：

1. **没有布局系统**：直接让模型"画一个图"，没有明确信息结构
   - baoyu 解决：20 种预设布局（pyramid、funnel、venn...）

2. **没有风格系统**：每次随机生成，不稳定
   - baoyu 解决：17 种预设风格（technical-schematic、corporate-memphis...）

3. **没有体系化 Prompt 模板**：每次手写，不可复用
   - baoyu 解决：布局×风格二维组合，自动生成结构化 prompt

### 研报级输出公式

```
研报级图表 = 明确布局（信息结构） + 专业风格（视觉语言） + 结构化 Prompt 模板
```

### 你现在应该怎么做？

1. **先配置 `baoyu-image-gen`**
   - 选一个 provider（建议 Replicate/Google）
   - 配置 EXTEND.md

2. **用 `baoyu-infographic` 生成第一张研报级图表**
   ```bash
   /baoyu-infographic article.md --layout pyramid --style technical-schematic
   ```

3. **固化你的风格组合**
   - 记录效果好的布局×风格组合
   - 建立你自己的"研报图表模板库"

---

## 八、下一步建议

我建议现在立刻做两件事：

1. **配置 baoyu-image-gen 的 EXTEND.md**
   - 选 provider
   - 选默认模型
   - 选默认质量

2. **实测一张研报级信息图**
   - 用我们之前的 Polymarket/公众号文章内容
   - 用 `pyramid + technical-schematic` 组合
   - 看实际效果

你要我现在开始配置和测试吗？