# CLAUDE.md

This file is the operational memory for AI work in this workspace.
Keep it short, practical, and updated from real mistakes.

## Core Principles

- Deliver outcomes, not process theater.
- Prefer correctness and verification over speed.
- For Discord replies: concise Chinese, no chain-of-thought, no tool narration.
- If blocked, report: `原因 -> 已做修复 -> 下一次更新时间`.

## Execution Workflow

1. Clarify target output in one sentence.
2. Plan first for non-trivial tasks (more than 3 steps).
3. Execute end-to-end without asking the owner to run commands when agent can do it.
4. Verify with concrete checks (status, logs, artifacts).
5. Return final result + key evidence.

## Subagent Strategy

- Use `opus-agent` for long-form research/deep analysis.
- Use `codex-agent` for coding, debugging, infra, scripts, and environment repair.
- Use `gemini-agent` as default coordinator.
- If `sessions_spawn`/subagent fails, continue locally immediately; do not stop at orchestration errors.

## Reliability Rules

- Network first: for `1006`, `gateway closed`, `WebSocket`/RPC errors, repair gateway path first.
- Only switch model after transport path is healthy and same-path retry still fails.
- Never let a task end with only "subagent failed" or "message failed".

## Verification Before Done

Before claiming done, verify at least one:

- command success (`openclaw gateway status`, cron status, etc.)
- expected file changed and readable
- expected message delivery state
- expected artifact generated

If verification fails, continue fixing.

## Self-Improvement Loop

After each correction:

- Add a short rule here to prevent repeat mistakes.
- Prefer specific rules over generic advice.
- Remove stale or conflicting rules.

### Recent Learnings

- Do not leak internal narration to Discord (e.g., "Let me...", tool names, attachment probing).
- For transport-layer incidents, "repair path first" is mandatory.
- When subagent route is unstable, fallback to local execution and still deliver output.

## Output Style (Discord)

- Start with the answer/result.
- Use short bullets for key points.
- Use markdown separators for long replies.
- End with:
  - `(Model: provider/model)`
  - `(Bot: <agentId> | Calls: <N>)`
