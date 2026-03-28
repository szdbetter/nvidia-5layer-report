#!/usr/bin/env python3
"""Speech-to-text transcription using faster-whisper (CPU, int8)."""

import argparse
import sys
import os
import json


def transcribe(audio_path: str, model_size: str = "base", language: str | None = None) -> dict:
    """Transcribe audio file and return result dict."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    kwargs = {}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(audio_path, **kwargs)

    texts = []
    segment_list = []
    for seg in segments:
        texts.append(seg.text.strip())
        segment_list.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })

    return {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 2) if hasattr(info, "duration") else None,
        "text": " ".join(texts),
        "segments": segment_list,
    }


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper")
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--language", default=None, help="Force language (e.g., zh, en, ja)")
    parser.add_argument("--output", default=None, help="Output file path (JSON)")
    parser.add_argument("--json", action="store_true", help="Output full JSON (with segments)")
    args = parser.parse_args()

    try:
        result = transcribe(args.audio, model_size=args.model, language=args.language)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved to {args.output}")
    elif args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Plain text output
        lang = result["language"]
        prob = result["language_probability"]
        print(f"[{lang} ({prob})]")
        print(result["text"])


if __name__ == "__main__":
    main()
