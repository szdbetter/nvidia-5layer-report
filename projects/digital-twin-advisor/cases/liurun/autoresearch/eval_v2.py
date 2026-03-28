#!/usr/bin/env python3
"""
Eval runner for Liurun digital twin system prompt optimization.
Usage: python3 eval_v2.py <version>
"""
import subprocess
import json
import sys
import os
import re

VERSION = int(sys.argv[1]) if len(sys.argv) > 1 else 1
BASE_DIR = "/root/.openclaw/workspace/projects/digital-twin-advisor/cases/liurun/autoresearch"
PROMPT_FILE = f"{BASE_DIR}/system_prompt_v{VERSION}.md"
OUTPUT_FILE = f"{BASE_DIR}/eval_results_v{VERSION}.json"

QUESTIONS = [
    "我的餐饮生意越来越难做，要不要关店转行做电商？",
    "员工总是执行不到位，是员工问题还是管理问题？",
    "现在AI这么热，我一个传统制造业老板，要怎么用AI？",
    "怎么判断一个新赛道值不值得进入？",
    "公司现金流很紧，但老板说要扩张，怎么办？",
    "为什么很多努力工作的人，收入反而不高？",
    "我想给团队做激励，发奖金还是涨工资哪个更有效？",
    "平台电商流量越来越贵，品牌还有出路吗？",
    "古巴的经济实验给中小企业主什么启示？",
    "一个人公司（独立顾问/自由职业）有没有天花板？",
]

BAD_WORDS = ["显而易见", "值得注意", "毋庸置疑", "首先其次最后", "综上所述", "不言而喻"]

def run_claude(system_prompt, user_msg, model="claude-sonnet-4-5"):
    result = subprocess.run(
        ["claude", "-p", system_prompt, "--model", model],
        input=user_msg,
        capture_output=True, text=True, timeout=120,
        cwd="/root/.openclaw/workspace"
    )
    return result.stdout.strip()

def score_answer(answer: str) -> dict:
    """Score answer locally without another claude call to avoid confusion."""
    scores = []
    fails = []
    
    # Rule 1: Case/story intro - check if first 200 chars contain story-like content
    first_200 = answer[:200] if len(answer) > 200 else answer
    # Look for indicators of a story: year, someone's name, specific number, "有一家", "有一位", etc.
    story_markers = ["有一家", "有一位", "有一个", "年，", "年前", "曾经", "那一年", "故事", 
                     "记得", "家公司", "位老板", "有家", "这家", "那家", "一家"]
    # Also check: starts with a narrative sentence (not with "如果", "当", "面对", etc.)
    direct_answer_starters = ["如果你", "面对这", "这个问题", "要回答", "答案是", "我认为", "关于"]
    has_story = any(m in first_200 for m in story_markers)
    is_direct = any(first_200.startswith(s) or first_200.startswith("**") for s in direct_answer_starters)
    scores.append(1 if has_story else 0)
    if not has_story:
        fails.append("规则1失败：开头未用真实案例/故事切入")
    
    # Rule 2: Principle extraction - look for framework keywords
    principle_markers = ["底层逻辑", "规律", "框架", "原理", "本质", "换句话说", "大白话说", 
                        "模型", "公式", "等式", "定律", "法则", "结论是", "答案是"]
    has_principle = any(m in answer for m in principle_markers)
    scores.append(1 if has_principle else 0)
    if not has_principle:
        fails.append("规则2失败：未明确提炼底层规律或框架")
    
    # Rule 3: Golden closing - check last 200 chars for punchy sentence
    last_200 = answer[-200:] if len(answer) > 200 else answer
    # A good closing is usually a short, standalone sentence at the end
    lines = [l.strip() for l in answer.split('\n') if l.strip()]
    last_line = lines[-1] if lines else ""
    # Check if last line is short (< 60 chars) and impactful
    has_golden = len(last_line) < 80 and len(last_line) > 5 and ('。' in last_line or '！' in last_line)
    scores.append(1 if has_golden else 0)
    if not has_golden:
        fails.append(f"规则3失败：结尾无传播性金句，末行='{last_line[:50]}'")
    
    # Rule 4: No AI-ish words
    has_ai_words = any(bw in answer for bw in BAD_WORDS)
    scores.append(0 if has_ai_words else 1)
    if has_ai_words:
        found = [bw for bw in BAD_WORDS if bw in answer]
        fails.append(f"规则4失败：出现AI味词汇 {found}")
    
    # Rule 5: Word count 600-1800
    # Chinese char count approximation
    char_count = len(answer)
    in_range = 600 <= char_count <= 1800
    scores.append(1 if in_range else 0)
    if not in_range:
        fails.append(f"规则5失败：字数={char_count}，不在600-1800范围内")
    
    return {"scores": scores, "total": sum(scores), "fails": fails}

def main():
    with open(PROMPT_FILE, 'r') as f:
        system_prompt = f.read()
    
    results = []
    total_score = 0
    
    for i, q in enumerate(QUESTIONS):
        print(f"  Q{i+1}: {q[:30]}...", flush=True)
        
        answer = run_claude(system_prompt, q)
        eval_result = score_answer(answer)
        
        total_score += eval_result["total"]
        print(f"    Score: {eval_result['total']}/5 | Fails: {eval_result['fails']}", flush=True)
        
        results.append({
            "question": q,
            "answer": answer,
            "eval": eval_result
        })
    
    output = {
        "version": VERSION,
        "total_score": total_score,
        "max_score": 50,
        "questions": results
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nv{VERSION} TOTAL: {total_score}/50")
    return total_score

if __name__ == "__main__":
    main()
