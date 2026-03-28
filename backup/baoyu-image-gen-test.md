# baoyu-image-gen 配置与测试记录

## 一、环境检查

### 已确认可用
- **bun**: 1.3.10 ✅
- **npx**: 可用 ✅
- **GOOGLE_API_KEY**: 已配置 ✅

### 配置文件位置
```
/root/.openclaw/workspace/.baoyu-skills/baoyu-image-gen/EXTEND.md
```

### 配置内容
```yaml
default_provider: google
default_model:
  google: gemini-3-pro-image-preview
default_quality: 2k
default_aspect_ratio: "16:9"
batch_worker_cap: 4
default_save_directory: ./generated_images
```

---

## 二、实测结果

### 测试命令
```bash
bun skills/baoyu-image-gen/scripts/main.ts \
  --prompt "Professional infographic showing a pyramid structure..." \
  --image generated_images/test-infographic.png \
  --ar 16:9 \
  --quality 2k \
  --provider google
```

### 输出
```
Using google / gemini-3-pro-image-preview for single
Generating image with Gemini... { imageSize: "2K" }
Generation completed.
/root/.openclaw/workspace/generated_images/test-infographic.png
```

### 图片信息
- **路径**: `/root/.openclaw/workspace/generated_images/test-infographic.png`
- **大小**: 2.7MB
- **质量**: 2K
- **比例**: 16:9

---

## 三、使用方式总结

### 1. 基础命令
```bash
cd /root/.openclaw/workspace
bun skills/baoyu-image-gen/scripts/main.ts \
  --prompt "你的 prompt" \
  --image generated_images/output.png
```

### 2. 指定参数
```bash
# 指定比例
bun ... --ar 16:9   # 或 4:3, 1:1, 9:16

# 指定质量
bun ... --quality 2k   # 或 normal

# 指定 provider
bun ... --provider google   # 或 openai, dashscope, replicate

# 指定模型
bun ... --model gemini-3-pro-image-preview

# 参考图片（支持 Google multimodal / OpenAI edits）
bun ... --ref reference.png
```

### 3. 批处理模式
```bash
# 创建 batch.json
{
  "jobs": 4,
  "tasks": [
    {
      "id": "img1",
      "promptFiles": ["prompts/img1.md"],
      "image": "out/img1.png",
      "ar": "16:9",
      "quality": "2k"
    }
  ]
}

# 运行批处理
bun skills/baoyu-image-gen/scripts/main.ts --batchfile batch.json
```

---

## 四、研报级 Prompt 模板

### 信息图（金字塔/层级结构）
```
Professional infographic showing a pyramid structure with 4 levels.
Level 1 (top): [标题]
Level 2: [第二大点]
Level 3: [第三大点]
Level 4 (bottom): [底部总结]
Style: blueprint technical schematic, clean lines, engineering diagram,
dark blue background with white text and grid lines,
professional research report quality.
```

### 对比图
```
Professional infographic showing a binary comparison.
Left side: [A方案]
Right side: [B方案]
Style: corporate memphis, flat vector figures, vibrant colors,
professional business presentation quality.
```

### 流程图
```
Professional infographic showing a linear progression.
Step 1: [第一步]
Step 2: [第二步]
Step 3: [第三步]
Style: ikea manual, minimal line art, assembly instruction style,
clean and professional.
```

---

## 五、可用 Provider 和模型

### Google
- `gemini-3-pro-image-preview`（当前使用）
- `gemini-3.1-flash-image-preview`

### OpenAI
- `gpt-image-1.5`
- `gpt-image-1`

### DashScope（阿里通义万象）
- 需配置 `DASHSCOPE_API_KEY`

### Replicate
- `google/nano-banana-pro`
- 需配置 `REPLICATE_API_TOKEN`

---

## 六、下一步建议

1. **固化你的研报级 Prompt 模板**
   - 记录效果好的 prompt 结构
   - 建立你自己的"研报图表模板库"

2. **测试不同布局×风格组合**
   - `pyramid + technical-schematic`：层级结构
   - `funnel + corporate-memphis`：漏斗转化
   - `comparison + aged-academia`：对比分析

3. **批量生成测试**
   - 创建 `batch.json`
   - 一次生成多张不同风格对比