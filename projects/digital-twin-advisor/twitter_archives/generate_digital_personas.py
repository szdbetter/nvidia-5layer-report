#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter KOL 数字分身生成器

功能：
1) 遍历输入目录下所有 KOL 子目录，收集推文文本（.md/.txt，可配置）
2) 自动解析并去重推文（优先按 tweet URL 去重）
3) 读取指定 prompt，调用 OpenAI 兼容接口生成每个 KOL 的数字分身 Markdown
4) 生成总合并文件，包含来源、时间范围、数量、prompt 版本等元信息

示例：
python3 generate_digital_personas.py \
  --input-dir /Users/ai/.openclaw/workspace/twitter_archives \
  --prompt-file /Users/ai/.openclaw/workspace/skills/ai-avatar/twitter-crypto+trade-prompt.md \
  --output-dir /Users/ai/.openclaw/workspace/twitter_archives/digital_personas \
  --model gpt-4.1
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from urllib import error, request

try:
    from rich.console import Console

    RICH_AVAILABLE = True
    CONSOLE = Console()
except Exception:  # noqa: BLE001
    RICH_AVAILABLE = False
    CONSOLE = None


DEFAULT_INPUT_DIR = "/Users/ai/.openclaw/workspace/twitter_archives"
DEFAULT_PROMPT_FILE = (
    "/Users/ai/.openclaw/workspace/skills/ai-avatar/twitter-crypto+trade-prompt.md"
)
DEFAULT_OUTPUT_DIR = "/Users/ai/.openclaw/workspace/twitter_archives/digital_personas"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_PROVIDER = "codex-cli"
DEFAULT_CODEX_MODEL = "gpt-5.3-codex"
DEFAULT_HEARTBEAT_SEC = 15
DEFAULT_MIN_OUTPUT_CHARS = 7500
DEFAULT_MAX_RETRIES = 2

SEPARATOR_RE = re.compile(r"(?:\n|^)[\u2500\-]{20,}(?:\n|$)")
DATE_RE = re.compile(r"📅\s*(.+)")
URL_RE = re.compile(r"🔗\s*(https?://\S+)")
VERSION_RE = re.compile(r"^\s*#\s*版本\s*[:：]?\s*(.+?)\s*$", re.MULTILINE)
PROMPT_UPDATED_RE = re.compile(r"^\s*#\s*更新时间\s*[:：]?\s*(.+?)\s*$", re.MULTILINE)
MONTH_FILE_RE = re.compile(r"^\d{4}-\d{2}\.(txt|md)$", re.IGNORECASE)


@dataclass
class TweetItem:
    key: str
    text: str
    dt: Optional[datetime]
    source_file: str
    url: Optional[str]


@dataclass
class PersonaResult:
    kol: str
    output_file: Path
    total_tweets: int
    used_tweets: int
    source_files: List[str]
    data_start: Optional[datetime]
    data_end: Optional[datetime]


@dataclass
class ValidationResult:
    ok: bool
    length_ok: bool
    headings_ok: bool
    body_len: int
    missing_headings: List[str]


def log_line(text: str, level: str = "info") -> None:
    if RICH_AVAILABLE and CONSOLE:
        style = {
            "info": "cyan",
            "ok": "green",
            "warn": "yellow",
            "err": "bold red",
        }.get(level, "white")
        CONSOLE.print(text, style=style)
        return
    print(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Twitter KOL 数字分身批量生成工具")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="KOL 推文目录")
    parser.add_argument("--prompt-file", default=DEFAULT_PROMPT_FILE, help="分身生成 prompt 文件")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="输出目录")
    parser.add_argument(
        "--extensions",
        default=".md,.txt",
        help="可扫描扩展名，逗号分隔，例如 .md,.txt",
    )
    parser.add_argument(
        "--exclude-patterns",
        default="*digital_persona*.md,*SUMMARY*.md",
        help="文件排除模式，逗号分隔",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名")
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        choices=["openai", "codex-cli"],
        help="生成提供方：openai 或 codex-cli（默认 codex-cli）",
    )
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="OpenAI 兼容 API Base")
    parser.add_argument(
        "--codex-model",
        default=DEFAULT_CODEX_MODEL,
        help="provider=codex-cli 时使用的模型（默认 gpt-5.3-codex）",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="存放 API Key 的环境变量名",
    )
    parser.add_argument(
        "--max-input-chars",
        type=int,
        default=180000,
        help="每个 KOL 提供给模型的最大字符数",
    )
    parser.add_argument(
        "--combined-file",
        default="digital_personas_merged.md",
        help="合并文件名（位于 output-dir 下）",
    )
    parser.add_argument(
        "--kol-filter",
        default="",
        help="仅处理指定 KOL（逗号分隔目录名），空表示全部",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="不调用模型，只写占位内容用于流程验证",
    )
    parser.add_argument(
        "--min-tweets",
        type=int,
        default=1,
        help="每个 KOL 最少推文数，低于该值自动跳过",
    )
    parser.add_argument(
        "--codex-bin",
        default="codex",
        help="codex cli 可执行文件路径（provider=codex-cli 时使用）",
    )
    parser.add_argument(
        "--codex-timeout",
        type=int,
        default=600,
        help="单个 KOL 调用 codex-cli 的超时时间（秒）",
    )
    parser.add_argument(
        "--heartbeat-sec",
        type=int,
        default=DEFAULT_HEARTBEAT_SEC,
        help="模型调用过程进度心跳间隔（秒）",
    )
    parser.add_argument(
        "--min-output-chars",
        type=int,
        default=DEFAULT_MIN_OUTPUT_CHARS,
        help="每个数字分身正文最少字符数（默认 7500，偏旧版长度风格）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="输出不达标时的自动重试次数",
    )
    return parser.parse_args()


def parse_datetime(s: str) -> Optional[datetime]:
    s = s.strip()
    fmts = [
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def parse_prompt_meta(prompt_text: str, prompt_file: Path) -> dict:
    version_match = VERSION_RE.search(prompt_text)
    updated_match = PROMPT_UPDATED_RE.search(prompt_text)
    return {
        "path": str(prompt_file),
        "version": version_match.group(1).strip() if version_match else "unknown",
        "updated_at": updated_match.group(1).strip() if updated_match else "unknown",
        "sha256_12": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:12],
    }


def should_exclude(path: Path, exclude_patterns: Iterable[str]) -> bool:
    return any(path.match(pat.strip()) for pat in exclude_patterns if pat.strip())


def is_probably_tweet_file(path: Path, content: str) -> bool:
    if path.name == "all_tweets_raw.txt":
        return True
    if MONTH_FILE_RE.match(path.name):
        return True
    if "📅 " in content and "🔗 " in content:
        return True
    if "https://x.com/" in content and content.count("@") >= 1:
        return True
    if "────────────────" in content and "📅 " in content:
        return True
    return False


def split_tweet_blocks(content: str) -> List[str]:
    blocks = [b.strip() for b in SEPARATOR_RE.split(content) if b.strip()]
    return blocks if blocks else ([content.strip()] if content.strip() else [])


def extract_required_headings(prompt_text: str) -> List[str]:
    """提取模板里的核心章节标题，作为输出完整性约束。"""
    required: List[str] = []
    for line in prompt_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# 一、") or s.startswith("# 二、") or s.startswith("# 三、") or s.startswith("# 四、"):
            required.append(s.lstrip("#").strip())
        elif s.startswith("## （") and "提取方向" not in s and "核心" not in s[:6]:
            required.append(s.lstrip("#").strip())
        elif s.startswith("### "):
            # 旧版风格下三级标题很关键，保留模板中的主要三级标题
            required.append(s.lstrip("#").strip())
    # 去重并保持顺序
    seen = set()
    out: List[str] = []
    for h in required:
        if h in seen:
            continue
        seen.add(h)
        out.append(h)
    return out


def validate_persona_output(
    body: str,
    required_headings: List[str],
    min_output_chars: int,
) -> ValidationResult:
    body_len = len(body)
    missing = [h for h in required_headings if h not in body]
    length_ok = body_len >= min_output_chars
    headings_ok = len(missing) == 0
    return ValidationResult(
        ok=length_ok and headings_ok,
        length_ok=length_ok,
        headings_ok=headings_ok,
        body_len=body_len,
        missing_headings=missing,
    )


def extract_tweet_item(block: str, source_file: str) -> TweetItem:
    date_match = DATE_RE.search(block)
    url_match = URL_RE.search(block)
    dt = parse_datetime(date_match.group(1)) if date_match else None
    url = url_match.group(1).strip() if url_match else None
    key = url or hashlib.sha256(block.encode("utf-8")).hexdigest()
    return TweetItem(key=key, text=block, dt=dt, source_file=source_file, url=url)


def collect_tweets_for_kol(
    kol_dir: Path,
    extensions: Iterable[str],
    exclude_patterns: Iterable[str],
) -> Tuple[List[TweetItem], List[str]]:
    ext_set = {e.strip().lower() for e in extensions if e.strip()}
    files: List[Path] = []
    file_and_content: List[Tuple[Path, str]] = []
    for path in sorted(kol_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ext_set:
            continue
        if should_exclude(path, exclude_patterns):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not is_probably_tweet_file(path, content):
            continue
        files.append(path)
        file_and_content.append((path, content))

    if not files:
        return [], []

    # 如果存在 all_tweets_raw.txt，优先只读它，避免月度文件重复。
    all_raw = [f for f in files if f.name == "all_tweets_raw.txt"]
    if all_raw:
        files = all_raw
        file_and_content = [x for x in file_and_content if x[0].name == "all_tweets_raw.txt"]

    dedup = {}
    used_files: List[str] = []
    for file_path, content in file_and_content:
        used_files.append(str(file_path))
        for block in split_tweet_blocks(content):
            item = extract_tweet_item(block, str(file_path))
            dedup[item.key] = item

    items = list(dedup.values())
    items.sort(key=lambda x: x.dt or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True)
    return items, used_files


def build_tweets_context(tweets: List[TweetItem], max_chars: int) -> Tuple[str, int]:
    chunks: List[str] = []
    used = 0
    total_len = 0
    for i, item in enumerate(tweets, start=1):
        block = f"\n[推文#{i}]\n{item.text}\n"
        if total_len + len(block) > max_chars:
            break
        chunks.append(block)
        total_len += len(block)
        used += 1
    return "\n".join(chunks).strip(), used


def iso_or_unknown(dt: Optional[datetime]) -> str:
    if not dt:
        return "unknown"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def date_only(dt: Optional[datetime]) -> str:
    if not dt:
        return "unknown"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def openai_chat_completion(
    api_base: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    url = api_base.rstrip("/") + "/chat/completions"
    req = request.Request(
        url=url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return data["choices"][0]["message"]["content"].strip()
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"API HTTPError {e.code}: {detail}") from e
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"API 调用失败: {e}") from e


def codex_cli_generate(
    codex_bin: str,
    model: Optional[str],
    prompt: str,
    timeout_sec: int,
    heartbeat_sec: int,
    progress_prefix: str = "",
) -> str:
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False) as tf:
        out_path = Path(tf.name)

    cmd = [
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "--output-last-message",
        str(out_path),
        "-",
    ]
    if model:
        cmd = cmd[:-1] + ["-m", model, "-"]

    started_at = time.time()
    heartbeat_sec = max(5, heartbeat_sec)
    next_heartbeat = heartbeat_sec
    stdout = ""
    stderr = ""
    input_sent = False

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"未找到 codex 命令: {codex_bin}") from e

    status_text = f"{progress_prefix} 调用模型中..."
    status_ctx = (
        CONSOLE.status(status_text, spinner="dots")
        if (RICH_AVAILABLE and CONSOLE)
        else contextlib.nullcontext()
    )

    with status_ctx as status:
        while True:
            elapsed = int(time.time() - started_at)
            if elapsed >= timeout_sec:
                proc.kill()
                try:
                    stdout, stderr = proc.communicate(timeout=3)
                except Exception:  # noqa: BLE001
                    stdout, stderr = "", ""
                raise RuntimeError(
                    f"codex-cli 超时（>{timeout_sec}s），已运行 {elapsed}s"
                )

            try:
                feed = None
                if not input_sent:
                    feed = prompt
                    input_sent = True
                stdout, stderr = proc.communicate(input=feed, timeout=1)
                break
            except subprocess.TimeoutExpired:
                if elapsed >= next_heartbeat:
                    msg = f"{progress_prefix} 模型处理中... {elapsed}s"
                    if RICH_AVAILABLE and CONSOLE and status is not None:
                        status.update(msg)
                    else:
                        log_line(msg, "info")
                    next_heartbeat += heartbeat_sec
                continue

    if proc.returncode != 0:
        stderr = (stderr or "").strip()
        stdout = (stdout or "").strip()
        stderr_tail = stderr[-1200:] if len(stderr) > 1200 else stderr
        stdout_tail = stdout[-1200:] if len(stdout) > 1200 else stdout
        raise RuntimeError(
            f"codex-cli 执行失败，exit={proc.returncode}\n"
            f"stdout(tail):\n{stdout_tail}\n"
            f"stderr(tail):\n{stderr_tail}"
        )

    total_elapsed = int(time.time() - started_at)
    log_line(f"{progress_prefix} 模型完成，用时 {total_elapsed}s", "ok")

    try:
        content = out_path.read_text(encoding="utf-8", errors="ignore").strip()
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass
    if not content:
        raise RuntimeError("codex-cli 返回空内容")
    return content


def generate_persona_markdown(
    *,
    kol: str,
    prompt_meta: dict,
    prompt_text: str,
    tweets: List[TweetItem],
    source_files: List[str],
    args: argparse.Namespace,
    api_key: Optional[str],
    progress_prefix: str = "",
    required_headings: Optional[List[str]] = None,
) -> Tuple[str, int]:
    context, used_tweets = build_tweets_context(tweets, args.max_input_chars)
    dates = [t.dt for t in tweets if t.dt is not None]
    data_start = min(dates) if dates else None
    data_end = max(dates) if dates else None

    meta_block = (
        f"- KOL: @{kol}\n"
        f"- Prompt 文件: {prompt_meta['path']}\n"
        f"- Prompt 版本: {prompt_meta['version']}\n"
        f"- Prompt 更新时间: {prompt_meta['updated_at']}\n"
        f"- Prompt 指纹: {prompt_meta['sha256_12']}\n"
        f"- 数据来源文件数: {len(source_files)}\n"
        f"- 数据来源文件: {', '.join(source_files)}\n"
        f"- 推文总量(去重后): {len(tweets)}\n"
        f"- 本次输入模型推文数: {used_tweets}\n"
        f"- 数据时间范围: {date_only(data_start)} ~ {date_only(data_end)}\n"
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    if args.dry_run:
        body = (
            "## Dry Run\n\n"
            "已完成数据汇总，未调用模型。去掉 `--dry-run` 后即可实际生成分身内容。"
        )
    else:
        system_prompt = (
            "你是资深加密投研与交易风格建模助手。"
            "严格根据提供的 prompt 模板和历史推文，输出可复用数字分身。"
            "不编造事实；对无法确认的点需明确标注。输出语言为中文 Markdown。"
        )
        user_prompt = (
            "请基于以下模板和推文，生成一个可复用的 KOL 数字分身。\n\n"
            "【模板 prompt】\n"
            f"{prompt_text}\n\n"
            "【KOL】\n"
            f"@{kol}\n\n"
            "【数据元信息】\n"
            f"{meta_block}\n"
            "【历史推文样本】\n"
            f"{context}\n\n"
            "要求：\n"
            "1) 必须完整覆盖模板中的全部章节与小节标题，不得省略。\n"
            "2) 输出必须可直接用于知识库问答（投研、是否可买、如何交易）。\n"
            "3) 结论必须贴合推文证据，避免空泛。\n"
            "4) 输出风格按“旧版长文档”执行：展开充分、条目完整。\n"
            "5) 在文末增加“证据摘要”：列出你主要依据的5-15条关键观点。\n"
        )
        if required_headings:
            user_prompt += (
                "\n【必须包含的章节标题（逐条覆盖）】\n"
                + "\n".join([f"- {h}" for h in required_headings])
                + "\n"
            )
        user_prompt += f"\n【最少正文长度】\n- 至少 {args.min_output_chars} 字符。\n"

        def run_generation(prompt_for_model: str) -> str:
            if args.provider == "codex-cli":
                merged_prompt = (
                    f"System:\n{system_prompt}\n\n"
                    f"User:\n{prompt_for_model}\n\n"
                    "仅输出最终 Markdown，不要输出额外说明。"
                )
                return codex_cli_generate(
                    codex_bin=args.codex_bin,
                    model=args.codex_model if args.codex_model else None,
                    prompt=merged_prompt,
                    timeout_sec=args.codex_timeout,
                    heartbeat_sec=args.heartbeat_sec,
                    progress_prefix=progress_prefix,
                )

            if not api_key:
                raise RuntimeError(
                    f"环境变量 {args.api_key_env} 未设置，无法调用 OpenAI API。"
                    "可切换 --provider codex-cli 或先使用 --dry-run 验证流程。"
                )
            return openai_chat_completion(
                api_base=args.api_base,
                api_key=api_key,
                model=args.model,
                system_prompt=system_prompt,
                user_prompt=prompt_for_model,
            )

        body = run_generation(user_prompt)
        req = required_headings or []
        validation = validate_persona_output(body, req, args.min_output_chars)
        attempts = 0
        while not validation.ok and attempts < max(0, args.max_retries):
            attempts += 1
            problems = []
            if not validation.length_ok:
                problems.append(f"长度不足: {validation.body_len} < {args.min_output_chars}")
            if not validation.headings_ok:
                missing_preview = ", ".join(validation.missing_headings[:20])
                problems.append(f"缺失标题: {missing_preview}")
            log_line(
                f"{progress_prefix} 输出校验未通过，开始补写重试 {attempts}/{args.max_retries} | "
                + " | ".join(problems),
                "warn",
            )
            revise_prompt = (
                "你上一版输出未满足格式要求，请在保留已有有效内容基础上重写完整版本。\n"
                "严格要求：\n"
                f"1) 正文至少 {args.min_output_chars} 字符。\n"
                "2) 必须包含下列所有章节标题，且每节都要有实质内容：\n"
                + "\n".join([f"- {h}" for h in req])
                + "\n3) 对证据不足的项可标注“证据不足”，但不能删节章节。\n"
                "4) 文末保留“证据摘要”。\n\n"
                "【上一版输出】\n"
                f"{body}"
            )
            body = run_generation(revise_prompt)
            validation = validate_persona_output(body, req, args.min_output_chars)
        if not validation.ok:
            log_line(
                f"{progress_prefix} 输出仍未完全达标（长度 {validation.body_len}，缺失标题 {len(validation.missing_headings)}），已保留当前最优版本。",
                "warn",
            )

    final_md = (
        f"# @{kol} 数字分身\n\n"
        "## 生成元信息\n"
        f"{meta_block}\n"
        "## 数字分身内容\n\n"
        f"{body.strip()}\n"
    )
    return final_md, used_tweets


def write_combined_file(
    combined_path: Path,
    prompt_meta: dict,
    results: List[PersonaResult],
    contents: List[str],
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    persona_names = ", ".join([f"@{r.kol}" for r in results]) if results else "none"
    total_tweets = sum(r.total_tweets for r in results)
    total_used = sum(r.used_tweets for r in results)
    earliest = min((r.data_start for r in results if r.data_start), default=None)
    latest = max((r.data_end for r in results if r.data_end), default=None)

    summary = [
        "# Twitter KOL 数字分身合并文件",
        "",
        "## 总元信息",
        f"- 合并时间: {now}",
        f"- 数字人数量: {len(results)}",
        f"- 包含数字人: {persona_names}",
        f"- Prompt 文件: {prompt_meta['path']}",
        f"- Prompt 版本: {prompt_meta['version']}",
        f"- Prompt 更新时间: {prompt_meta['updated_at']}",
        f"- Prompt 指纹: {prompt_meta['sha256_12']}",
        f"- 全量推文总数(去重后): {total_tweets}",
        f"- 输入模型推文总数: {total_used}",
        f"- 全局数据时间范围: {date_only(earliest)} ~ {date_only(latest)}",
        "",
        "## 明细",
        "",
        "| KOL | 推文数(去重) | 入模推文数 | 数据时间范围 | 输出文件 |",
        "|---|---:|---:|---|---|",
    ]
    for r in results:
        summary.append(
            f"| @{r.kol} | {r.total_tweets} | {r.used_tweets} | "
            f"{date_only(r.data_start)} ~ {date_only(r.data_end)} | {r.output_file} |"
        )
    summary.append("")
    summary.append("## 分身正文")
    summary.append("")
    for i, c in enumerate(contents, start=1):
        summary.append(f"---\n\n### 数字人 {i}\n\n{c.strip()}\n")

    combined_path.parent.mkdir(parents=True, exist_ok=True)
    combined_path.write_text("\n".join(summary), encoding="utf-8")


def main() -> None:
    args = parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    combined_path = output_dir / args.combined_file

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"输入目录不存在: {input_dir}")
    if not prompt_file.exists() or not prompt_file.is_file():
        raise SystemExit(f"Prompt 文件不存在: {prompt_file}")

    prompt_text = prompt_file.read_text(encoding="utf-8", errors="ignore")
    prompt_meta = parse_prompt_meta(prompt_text, prompt_file)
    required_headings = extract_required_headings(prompt_text)
    api_key = os.getenv(args.api_key_env)

    extensions = [x.strip() for x in args.extensions.split(",") if x.strip()]
    exclude_patterns = [x.strip() for x in args.exclude_patterns.split(",") if x.strip()]
    kol_filter = {x.strip() for x in args.kol_filter.split(",") if x.strip()}

    kol_dirs = []
    for p in sorted(input_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith(".") or p.name.startswith("__"):
            continue
        if p.name.startswith("digital_personas"):
            continue
        if p.resolve() == output_dir:
            continue
        kol_dirs.append(p)
    if kol_filter:
        kol_dirs = [p for p in kol_dirs if p.name in kol_filter]

    if not kol_dirs:
        raise SystemExit("未发现可处理的 KOL 子目录")

    output_dir.mkdir(parents=True, exist_ok=True)
    results: List[PersonaResult] = []
    contents: List[str] = []

    log_line("=== Twitter KOL 数字分身生成 ===", "info")
    log_line(f"输入目录: {input_dir}", "info")
    log_line(f"Prompt: {prompt_file}", "info")
    log_line(f"Prompt 版本: {prompt_meta['version']}", "info")
    log_line(f"模板章节约束数: {len(required_headings)}", "info")
    log_line(f"输出目录: {output_dir}", "info")
    log_line(f"Provider: {args.provider}", "info")
    if args.provider == "codex-cli":
        log_line(f"Codex 模型: {args.codex_model or '(默认)'}", "info")
    else:
        log_line(f"模型: {args.model}", "info")
    log_line(f"Dry Run: {args.dry_run}", "info")
    if not RICH_AVAILABLE:
        log_line("提示: 未安装 rich，当前使用纯文本输出。", "warn")
    log_line("", "info")

    total_dirs = len(kol_dirs)
    scanned = 0
    success = 0
    skipped = 0
    failed = 0

    for kol_dir in kol_dirs:
        scanned += 1
        kol = kol_dir.name
        log_line(f"[{scanned}/{total_dirs}] 扫描 {kol} ...", "info")
        tweets, source_files = collect_tweets_for_kol(kol_dir, extensions, exclude_patterns)
        if not tweets:
            skipped += 1
            log_line(f"[{scanned}/{total_dirs}] [跳过] {kol}: 未发现可用推文文件", "warn")
            continue
        if len(tweets) < args.min_tweets:
            skipped += 1
            log_line(
                f"[{scanned}/{total_dirs}] [跳过] {kol}: 推文数 {len(tweets)} < min_tweets({args.min_tweets})",
                "warn",
            )
            continue

        dates = [t.dt for t in tweets if t.dt]
        data_start = min(dates) if dates else None
        data_end = max(dates) if dates else None

        log_line(
            f"[{scanned}/{total_dirs}] [处理] {kol}: 推文{len(tweets)}条, 文件{len(source_files)}个, "
            f"时间范围 {date_only(data_start)} ~ {date_only(data_end)}",
            "info",
        )
        kol_started = time.time()
        prefix = f"[{scanned}/{total_dirs}] @{kol}"

        try:
            persona_md, used_tweets = generate_persona_markdown(
                kol=kol,
                prompt_meta=prompt_meta,
                prompt_text=prompt_text,
                tweets=tweets,
                source_files=source_files,
                args=args,
                api_key=api_key,
                progress_prefix=prefix,
                required_headings=required_headings,
            )
        except Exception as e:  # noqa: BLE001
            failed += 1
            elapsed = int(time.time() - kol_started)
            log_line(f"[{scanned}/{total_dirs}] [失败] {kol}: 用时 {elapsed}s | {e}", "err")
            continue

        output_file = output_dir / f"{kol}_digital_persona.md"
        output_file.write_text(persona_md, encoding="utf-8")
        results.append(
            PersonaResult(
                kol=kol,
                output_file=output_file,
                total_tweets=len(tweets),
                used_tweets=used_tweets,
                source_files=source_files,
                data_start=data_start,
                data_end=data_end,
            )
        )
        contents.append(persona_md)
        success += 1
        elapsed = int(time.time() - kol_started)
        log_line(f"[{scanned}/{total_dirs}] [完成] {kol}: 用时 {elapsed}s | {output_file}", "ok")

    write_combined_file(combined_path, prompt_meta, results, contents)
    log_line("", "info")
    log_line("=== 任务完成 ===", "ok")
    log_line(f"总目录数: {total_dirs}", "info")
    log_line(f"成功: {success} | 跳过: {skipped} | 失败: {failed}", "info")
    log_line(f"已生成数字分身: {len(results)}", "ok")
    log_line(f"合并文件: {combined_path}", "ok")


if __name__ == "__main__":
    main()
