# MiniMax 能力手册 (Agent Reference)

> 最后更新: 2026-03-20 | 全部能力已验证通过

## 📌 快速概览

MiniMax 通过两个 MCP Server 提供能力，均配置在 `config/mcporter.json` 中：

| Server | 包名 | 能力范围 |
|--------|------|---------|
| **MiniMax** | `minimax-coding-plan-mcp` | 🔍 网络搜索 + 👁️ 图片理解 |
| **MiniMax-Full** | `minimax-mcp` | 🗣️ TTS + 🎤 音色克隆 + 🎨 音色设计 + 🎵 音乐 + 🖼️ 图片 + 🎬 视频 |

**重要发现**: Coding Plan Key (`sk-cp-`开头) 可调用**全部**能力，无需额外购买标准API Key。

---

## 🔧 调用方式

所有工具通过 `mcporter call` 调用：

```bash
# 基础格式
mcporter call "<Server>.<tool>" key=value --output json

# 耗时任务（音乐/视频）需加大超时
MCPORTER_CALL_TIMEOUT=300000 mcporter call "<Server>.<tool>" key=value --output json
```

**超时建议**:
- 搜索/图片理解/TTS/图片生成: 默认60s够用
- 音色克隆/设计: 建议120s
- 音乐生成: 建议300s
- 视频生成: 建议300s

---

## 🔍 工具1: web_search (网络搜索)

```bash
mcporter call "MiniMax.web_search" query="搜索关键词" --output json
```

- **技巧**: 3-5个关键词效果最佳，时效性话题加日期
- **返回**: `organic[]` 数组，含 title/link/snippet/date

---

## 👁️ 工具2: understand_image (图片理解)

```bash
mcporter call "MiniMax.understand_image" \
  prompt="描述这张图片" \
  image_source="https://example.com/image.jpg" \
  --output json
```

- **支持格式**: JPEG, PNG, WebP（不支持PDF/GIF/SVG）
- **支持输入**: URL 或本地文件路径
- **注意**: 部分网站图片可能403，换源即可

---

## 🗣️ 工具3: text_to_audio (文字转语音)

```bash
mcporter call "MiniMax-Full.text_to_audio" \
  text="要朗读的文本" \
  voice_id="male-qn-qingse" \
  output_directory="/tmp/minimax-output" \
  --output json
```

**参数**:
- `voice_id`: 音色ID（默认 `female-shaonv`）
- `model`: 模型（默认 `speech-2.6-hd`）
- `speed`: 语速 0.5-2.0（默认1.0）
- `vol`: 音量 0-10（默认1）
- `pitch`: 音调 -12到12（默认0）
- `emotion`: 情绪 `happy|sad|angry|fearful|disgusted|surprised|neutral`
- `language_boost`: 语言增强 `Chinese|English|Japanese|auto` 等
- `format`: 输出格式 `mp3|pcm|flac`

**常用音色**: `male-qn-qingse`, `female-shaonv`, `audiobook_female_1`, `cute_boy`, `Charming_Lady`
> 完整音色列表用 `list_voices` 工具获取

---

## 🎤 工具4: voice_clone (音色克隆)

```bash
mcporter call "MiniMax-Full.voice_clone" \
  voice_id="my-custom-voice" \
  file="https://example.com/audio.mp3" \
  is_url=true \
  text="试听文本" \
  output_directory="/tmp/minimax-output" \
  --output json
```

- **支持格式**: mp3, m4a, wav
- **输入**: URL (`is_url=true`) 或本地文件路径
- 克隆后的 `voice_id` 可用于后续 `text_to_audio` 调用

---

## 🎨 工具5: voice_design (音色设计)

```bash
mcporter call "MiniMax-Full.voice_design" \
  prompt="磁性的成熟男声，低沉而温暖" \
  preview_text="试听这段文本" \
  output_directory="/tmp/minimax-output" \
  --output json
```

- 用自然语言描述想要的音色
- 返回试听音频，满意后可获取 voice_id

---

## 🎵 工具6: music_generation (音乐生成)

```bash
MCPORTER_CALL_TIMEOUT=300000 mcporter call "MiniMax-Full.music_generation" \
  prompt="轻快钢琴独奏，温暖治愈" \
  lyrics="[Intro]\n(piano)\n[Verse]\n歌词内容\n[Chorus]\n副歌内容" \
  output_directory="/tmp/minimax-output" \
  --output json
```

**歌词结构标签**: `[Intro]` `[Verse]` `[Chorus]` `[Bridge]` `[Outro]`

**底层模型**: `music-2.0`（MCP默认，不是music-01）

**参数**:
- `prompt`: 风格描述（必填，10-300字符）
- `lyrics`: 歌词（必填，10-600字符，支持结构标签）
- `vocal_gender`: 人声性别
- `make_instrumental`: 是否纯器乐
- `tags`: 风格标签

---

## 🖼️ 工具7: text_to_image (图片生成)

```bash
mcporter call "MiniMax-Full.text_to_image" \
  prompt="赛博朋克城市日落，霓虹灯倒映在雨后街道" \
  output_directory="/tmp/minimax-output" \
  --output json
```

- **模型**: image-01 / image-01-live
- **宽高比**: 支持8种（1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9）
- 返回图片URL

---

## 🎬 工具8: generate_video (文生视频)

```bash
MCPORTER_CALL_TIMEOUT=300000 mcporter call "MiniMax-Full.generate_video" \
  prompt="一只橘猫跳入游泳池" \
  model="T2V-01" \
  output_directory="/tmp/minimax-output" \
  --output json
```

**模型选择**:
- `T2V-01`: 文生视频（标准）
- `MiniMax-Hailuo-02`: 文生视频（支持1080P）
- `I2V-01`: 图生视频（需 `first_frame_image` 参数）

---

## 📹 工具9: image_to_video (图生视频)

```bash
MCPORTER_CALL_TIMEOUT=300000 mcporter call "MiniMax-Full.generate_video" \
  prompt="镜头缓缓推进，灯光闪烁" \
  first_frame_image="https://example.com/image.jpg" \
  model="I2V-01" \
  output_directory="/tmp/minimax-output" \
  --output json
```

- 用已有图片作为首帧，生成动态视频
- `first_frame_image` 支持URL

---

## 🔊 工具10: list_voices (查询音色)

```bash
mcporter call "MiniMax-Full.list_voices" --output json
```

- 返回所有可用音色（系统/克隆/设计生成的）

---

## ⚠️ 注意事项

1. **输出目录**: 所有生成类工具需指定 `output_directory`，建议用 `/tmp/minimax-output`
2. **超时处理**: 视频和音乐生成耗时较长，务必设置 `MCPORTER_CALL_TIMEOUT=300000`
3. **URL有效期**: 生成的OSS链接有过期时间（通常24h），需及时下载或分享
4. **Brave 429**: web_search 底层用Brave API，高频调用可能触发限流
5. **图片403**: understand_image 从服务端下载图片，部分网站会拦截，换源即可

---

## 📚 本地文档库

更多技术细节请参考本地文档：

- **M2.7使用技巧**: `docs/minimax/M2.7使用技巧`
- **MiniMax MCP文档**: `docs/minimax/MiniMax MCP`
- **Token Plan MCP文档**: `docs/minimax/TokenPlan MCP`
- **Mini-Agent框架**: `docs/minimax/Mini-Agent`

文档根目录: `/root/.openclaw/docs/minimax/`

---

## 🔑 API Key体系

| Key类型 | 前缀 | 来源 | 能力 |
|---------|------|------|------|
| Coding Plan Key | `sk-cp-` | Token Plan订阅页 | **全部能力**（已验证） |
| 标准API Key | 无特殊前缀 | 开放平台接口密钥 | 全部能力 |

**当前配置**: 使用 Coding Plan Key，已验证可调用全部10个工具。
Key存储位置: `config/mcporter.json` 的 env.MINIMAX_API_KEY

---

## 🔄 VPS额度耗尽时的降级方案

VPS（1500次/5h）额度用完时，可SSH到Fiona（6000次/5h）直接curl调API：

```bash
ssh fiona 'curl -s "https://api.minimaxi.com/v1/music_generation" \
  -H "Authorization: Bearer $FIONA_MINIMAX_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"music-2.0\",\"prompt\":\"...\",\"lyrics\":\"...\",\"audio_setting\":{\"sample_rate\":32000,\"bitrate\":128000,\"format\":\"mp3\"},\"output_format\":\"url\"}"'
```

Fiona的Key存储在: `/Users/ai/.openclaw/.env` → `MINIMAX_API_KEY`
