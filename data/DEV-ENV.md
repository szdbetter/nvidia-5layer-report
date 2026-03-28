# 开发环境与工具参考

### 开发环境声明
- **Claude Code**：已安装。产品开发用 `pty:true --permission-mode acceptEdits --session-id`；简单任务用 `--print --permission-mode bypassPermissions`
- **Codex**：已安装，使用 `pty:true` 模式
- **项目目录**：`~/projects/`（所有新项目在此创建子目录）
- **Node.js**：v24.13.1
- **Python**：系统自带
- **FFmpeg**：已安装（视频/音频处理）
- **Git**：已安装（所有项目必须 git init）
- **Playwright**：用于端到端测试

---

### 语音识别 (STT)

**工具**: `skills/stt`（基于 faster-whisper，本地 CPU 运行，免费无需 API Key）

收到语音/音频文件时，使用以下命令转写：
```bash
python3 {workspace}/skills/stt/scripts/transcribe.py <音频文件路径> --model base --language zh
```

- 支持格式：ogg, mp3, wav, m4a, mp4 等（ffmpeg 支持的都行）
- `--language zh` 强制中文（不加则自动检测）
- `--model tiny` 更快但精度低，`--model base` 推荐
- 输出纯文本到 stdout，可直接处理

**注意：不要使用 `openai-whisper` skill**（VPS 未安装 PyTorch 依赖，无法运行）。统一使用 `stt` skill。

---

### 图片生成 (Image Generation)

**首选方案**: MIXIAN API (api.sydney-ai.com) + dall-e-3 模型
- **费用**: ¥0.04/张，最便宜
- **API Key**: 从环境变量 `MIXIAN_API_KEY` 读取

```bash
source /root/.openclaw/.env
curl -s -X POST "https://api.sydney-ai.com/v1/images/generations" \
  -H "Authorization: Bearer $MIXIAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"dall-e-3","prompt":"你的提示词","n":1,"size":"1024x1024","response_format":"url"}'
```

**备选模型**: `qwen-image-2.0`（¥0.1/张，同一API）
**优先级**: MIXIAN dall-e-3 > MIXIAN qwen-image-2.0 > nano-banana-pro (Gemini)
**注意**: 不要使用 OpenAI 官方 API 生图（贵），统一走 MIXIAN 中继。

---

### 工具补充
- **JINA API**：`curl "https://r.jina.ai/<URL>" -H "Authorization: Bearer $JIAN_API_KEY1"` (密钥在 ~/.openclaw/.env)
- **反爬虫抓取**：`exec python3 ~/openclaw/workspace/tools/scrapling_fetch.py "<URL>" 30000`
- **Moltbook**：账号 `shuhu1`，URL `https://www.moltbook.com/api/v1`
