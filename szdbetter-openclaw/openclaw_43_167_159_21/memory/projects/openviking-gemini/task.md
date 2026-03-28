# Task: OpenViking → Gemini 迁移

## 状态: DONE ✅

## 根本原因
openclaw.json 插件配置多包了一层 `config: {}`，导致 `api.pluginConfig.mode` = undefined → 默认 local 模式 → waitForHealth 超时。

## 修复内容
1. ov.conf: embedder 改为 `models/gemini-embedding-001`（3072维）via OpenAI-compat endpoint
2. ov.conf: VLM 改为 `gemini-2.0-flash-lite`
3. openclaw.json: 插件配置 `mode: "remote"`, `baseUrl: "http://127.0.0.1:1933"` 移到 entry 顶层
4. systemd 服务 `/etc/systemd/system/openviking.service` 创建，GOOGLE_API_KEY 注入

## 验证证据
- memory_store: session 63dbf591-794d-43cd-b83a-8d50c397e303 ✅
- memory_recall: 正常响应 ✅
- curl /health: {"status":"ok"} ✅
- curl /api/v1/search/find: status ok ✅

## 完成时间: 2026-03-10
