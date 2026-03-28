---
name: stt
description: Speech-to-text via faster-whisper (local CPU). Use /stt to invoke.
version: 1.0.0
disable-model-invocation: true
metadata:
  openclaw:
    emoji: "🎤"
    requires:
      bins: ["python3", "ffmpeg"]
      pip: ["faster-whisper"]
---

# STT (Speech-to-Text)

Local speech-to-text using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2 backend). Runs on CPU with int8 quantization — no GPU or API key required.

## Usage

Transcribe an audio file:

```bash
python3 {baseDir}/scripts/transcribe.py <audio_file> [--model base] [--language zh]
```

### Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `audio_file` | (required) | Path to audio/video file (mp3, wav, ogg, m4a, mp4, etc.) |
| `--model` | `base` | Whisper model size: `tiny`, `base`, `small` |
| `--language` | auto-detect | Force language code (e.g., `zh`, `en`, `ja`) |
| `--output` | stdout | Output file path (optional) |

### Models

| Model | Size | RAM | Quality |
|-------|------|-----|---------|
| tiny | ~75MB | ~500MB | Fast, lower accuracy |
| base | ~150MB | ~700MB | **Recommended** — good balance |
| small | ~500MB | ~1.5GB | Best quality for low-RAM machines |

> ⚠️ `medium` and `large` require >4GB RAM — not suitable for current VPS (3.5GB).

### Examples

```bash
# Auto-detect language
python3 {baseDir}/scripts/transcribe.py voice_message.ogg

# Force Chinese
python3 {baseDir}/scripts/transcribe.py meeting.mp3 --language zh

# Use tiny model for speed
python3 {baseDir}/scripts/transcribe.py audio.wav --model tiny
```

## Integration with OpenClaw

When a voice message arrives via Discord/Telegram, use this skill to transcribe it before processing the text content.
