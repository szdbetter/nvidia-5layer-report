# LLM 分工体系（2026-03-15 更新 · 基于实际可用资源）

> ⚠️ 下列模型可能不稳定：GPT 系列（Plus 账号易限流）、Kimi、Qwen、MiniMax 未在环境中稳定注册，遇到限流/不可用时直接使用Primary模型，无需等待。

---

## 【派发冲突优先法则】

1. **超长文档（>100页）** → 优先 `doubao-seed-2.0-pro`（128K上下文），不可用降级 `glm-4.7`
2. **脏数据清洗/批量初筛** → `doubao-seed-2.0-lite`（最快最省钱）
3. **强结构化输出（JSON/固定模板）** → `doubao-seed-2.0-pro` 最后一步组装
4. **数学/算法** → `deepseek-v3.2` 原型，`doubao-seed-code` 工程落地

---

## 【⚠️ LLM 调用兜底法则 · 强制生效】

**任何模型调用前，必须预判额度风险：**
1. 调用火山引擎/OpenAI 系模型遇到 `429 / quota exceeded / insufficient_quota` → **立即停止重试，降级至 Claude Sonnet（Max订阅，无额度上限）**
2. Claude Max 订阅是**最终兜底**，永远保持可用，绝不因额度问题断链
3. 派发子 agent 时，task 指令中必须注明：「若模型不可用，降级至 claude-sonnet-4-6」

---

## 一、当前主力决策层

| 模型 | 标识 | 定位 | 额度风险 |
|------|------|------|----------|
| **Claude Sonnet 4.6** | `anthropic/claude-sonnet-4-6` | 🧠 CEO 主脑 · **最终兜底** | ✅ Max订阅，无限额 |
| **Claude Opus 4.6** | `anthropic/claude-opus-4-6` | 🏛️ 顶级决策（按需） | ✅ Max订阅，有速率限制 |
| **Doubao-Seed-2.0-Pro** | `volcengine/doubao-seed-2.0-pro` | 📊 国产战略替代 | ⚠️ 按token计费，监控余额 |

---

## 二、代码执行团队

### OpenAI（外援·高质量·有限流风险）
| 模型 | 调用方式 | 定位 | 额度风险 |
|------|----------|------|----------|
| **Codex / GPT-5.3+** | `sessions_spawn` runtime=acp 或 exec acpx | 🏆 顶级代码架构师 | ⚠️ Plus订阅易限流；**🚨 sessions_spawn 禁用 runtime:"acp"，必须用 subagent 模式或 exec acpx** |

> Codex 用法：适合极复杂重构、大型分布式系统搭建。限流时立即降级至 Doubao-Seed-2.0-Code，无需等待。

### 火山引擎（主力·稳定·按量付费）
| 模型 | 标识 | 定位 | 额度风险 |
|------|------|------|----------|
| **Doubao-Seed-2.0-Code** | `volcengine/doubao-seed-2.0-code` | 👨‍💻 首席工程师 | ⚠️ 按token计费 |
| **Doubao-Seed-Code** | `volcengine/doubao-seed-code` | 🔧 业务开发主力 | ⚠️ 按token计费 |
| **Ark-Code-Latest** | `volcengine/ark-code-latest` | ⚙️ 批量稳定代码 | ⚠️ 按token计费 |

---

## 三、垂直专家团队

| 模型 | 标识 | 定位 | 适用场景 |
|------|------|------|----------|
| **DeepSeek-V3.2** | `volcengine/deepseek-v3.2` | 🔢 算法专家 | 数学建模、逻辑推理、算法原型、LeetCode类 |
| **GLM-4.7** | `volcengine/glm-4.7` | 🌐 中文/翻译专家 | 中文政策解读、外文研报本地化、中英互译 |
| **Doubao-Seed-2.0-Lite** | `volcengine/doubao-seed-2.0-lite` | 🧹 数据清洗工 | 脏数据初筛、高并发批量任务、简单问答 |

---

## 四、图生视频团队（独立 API · 非 chat completion）

> ⚠️ Seedance 是火山引擎视频生成 API，**不走 `models.providers` 路由**（那层只管文本模型）。
> Key 统一使用 `$VOLCENGINE_API_KEY`（已在 `openclaw.json` env 层透传 + `~/.openclaw/.env`）。

| 模型 | model_id | 定位 | 调用方式 |
|------|----------|------|----------|
| **Seedance-2.0** | `doubao-seedance-2-0-260128` | 🎬 视频主力 | `exec curl` POST 到火山引擎视频API |
| **Seedance-1.0-Lite** | `doubao-seedance-1-0-lite-i2v` | 🎬 降级备选 | 同上，仅支持图+文 |

**视频生成 SOP（强制）：**
1. `POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`
   - Header: `Authorization: Bearer $VOLCENGINE_API_KEY`
   - 支持多模态: `image_url(reference_image)` + `video_url(reference_video)` + `audio_url(reference_audio)`
   - 参数: `ratio("9:16"/"16:9")`, `duration(≤11s)`, `generate_audio:true`, `watermark:false`
2. 每 20s 轮询 `GET .../tasks/{task_id}`，直到 `status=succeeded`
3. 取 `content.video_url`（链接 24h 有效）
4. 遇 `quota exceeded` → 检查 `.env` VOLCENGINE_API_KEY 余额，无法解决立即通报人类
