"""
Music AI Gateway — Port 1988
"""
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp, asyncio, json, os, re, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("music-gateway")

app = FastAPI(title="Music AI Gateway", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models.json")
OLLAMA_URL   = "http://100.74.49.115:11434/api/generate"
GRADIO_BASE  = "http://127.0.0.1:7860"
ACE_SERVICE  = "http://127.0.0.1:7861"   # ACE-Step direct pipeline service (bypasses Gradio)
LYRICS_MODEL = "qwen2.5vl:7b"

GENRE_PROMPTS = {
    "流行":   "pop, melodic, catchy, piano, synth, drums, radio-friendly",
    "古风":   "chinese traditional, guzheng, erhu, pipa, pentatonic scale, ancient folk, elegant",
    "摇滚":   "rock, electric guitar, bass guitar, drum kit, distortion, energetic, powerful",
    "爵士":   "jazz, piano, trumpet, double bass, saxophone, swing, smooth",
    "R&B":    "r&b, soul, electric piano, bass guitar, drum machine, groove",
    "电子":   "electronic, synthesizer, 808 bass, drum machine, edm, dance, atmospheric",
    "说唱":   "hip hop, rap, trap beats, 808, hi-hat, urban, rhythmic",
    "民谣":   "folk, acoustic guitar, fingerpicking, intimate, warm, storytelling",
    "古典":   "classical, orchestral, strings, piano, violin, cello, symphonic",
}
MOOD_PROMPTS = {
    "欢快": "upbeat, joyful, cheerful, energetic, bright",
    "悲伤": "melancholic, sad, emotional, heartbreak, tender",
    "激昂": "powerful, intense, passionate, inspiring, anthemic",
    "平静": "calm, peaceful, serene, ambient, gentle",
    "浪漫": "romantic, dreamy, tender, intimate, warm",
    "神秘": "mysterious, ethereal, atmospheric, dark, cinematic",
}

def load_models():
    with open(MODELS_FILE) as f:
        return json.load(f)

async def check_health(url: str, timeout=3.0) -> str:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                return "online" if r.status < 600 else "error"
    except:
        return "offline"

# ── API ───────────────────────────────────────────────────────────
@app.get("/api/models")
async def api_models():
    models = load_models()
    return [{**m, "id": mid, "status": await check_health(m["internal_url"])}
            for mid, m in models.items()]

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "version": "2.1"}

@app.post("/api/lyrics")
async def api_lyrics(request: Request):
    body = await request.json()
    theme         = body.get("theme", "").strip()
    genre         = body.get("genre", "流行")
    mood          = body.get("mood", "欢快")
    custom_lyrics = body.get("custom_lyrics", "").strip()

    FORMAT_EXAMPLE = (
        "严格使用以下标签格式，每个标签单独占一行，不加任何说明或解释：\n"
        "[verse]\n第一行\n第二行\n第三行\n第四行\n\n"
        "[chorus]\n第一行\n第二行\n第三行\n第四行"
    )

    if custom_lyrics:
        # User provided their own lyrics — assemble into ACP format
        user = (
            "将以下歌词整理成 ACP 格式。规则：识别段落（主歌/副歌/桥段），在每段第一行前单独加标签行（[verse]/[chorus]/[bridge]/[outro]），"
            "段落内部歌词保持不变，段落之间空一行。只输出整理后的歌词，不加任何解释。\n\n"
            f"歌词：\n{custom_lyrics}"
        )
        payload = {
            "model": LYRICS_MODEL, "prompt": user,
            "stream": False, "options": {"temperature": 0.2, "num_predict": 600}
        }
    else:
        if not theme:
            return JSONResponse({"error": "请输入主题"}, status_code=400)
        user = (
            f"只用中文写歌词，主题：{theme}，风格：{genre}，情绪：{mood}。\n"
            f"结构：2段[verse] + 1段[chorus]重复2次，每段4行，自然押韵。\n"
            f"{FORMAT_EXAMPLE}\n只输出歌词，不加任何说明。"
        )
        payload = {
            "model": LYRICS_MODEL, "prompt": user,
            "stream": False, "options": {"temperature": 0.85, "num_predict": 600}
        }

    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(OLLAMA_URL, json=payload,
                              timeout=aiohttp.ClientTimeout(total=60)) as r:
                result = await r.json()
        # qwen3 thinking 模型：response 字段是实际输出，thinking 字段是思维过程
        # 同时兼容旧格式（<think>...</think> 包在 response 里）
        raw = result.get("response", "")
        lyrics = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        return {"lyrics": lyrics}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/generate")
async def api_generate(request: Request):
    body     = await request.json()
    lyrics   = body.get("lyrics", "")
    genre    = body.get("genre", "流行")
    mood     = body.get("mood", "欢快")
    duration = int(body.get("duration", 60))
    model_id = body.get("model", "ace-step")

    models = load_models()
    if model_id not in models:
        return JSONResponse({"error": f"模型 {model_id} 不存在"}, status_code=404)

    prompt = ", ".join(filter(None, [
        GENRE_PROMPTS.get(genre, "pop, melodic"),
        MOOD_PROMPTS.get(mood, "upbeat"),
    ]))

    ace_payload = {
        "lyrics": lyrics,
        "prompt": prompt,
        "audio_duration": duration,
        "format": "mp3",
        "infer_step": 60,
        "guidance_scale": 15.0,
    }

    async def stream():
        def evt(d): return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"
        try:
            yield evt({"status": "starting", "msg": "连接 ACE-Step..."})

            svc_health = await check_health(f"{ACE_SERVICE}/health")
            if svc_health != "online":
                yield evt({"status": "error", "msg": "ACE-Step 服务未启动，请稍候再试"}); return

            result_box: dict = {}
            error_box:  dict = {}
            done_event = asyncio.Event()

            async def do_generate():
                try:
                    async with aiohttp.ClientSession() as s:
                        async with s.post(
                            f"{ACE_SERVICE}/generate",
                            json=ace_payload,
                            timeout=aiohttp.ClientTimeout(total=600)
                        ) as r:
                            data = await r.json()
                            if r.status == 200:
                                result_box["data"] = data
                            else:
                                error_box["msg"] = data.get("detail", f"HTTP {r.status}")
                except Exception as e:
                    error_box["msg"] = str(e)
                finally:
                    done_event.set()

            task = asyncio.create_task(do_generate())
            elapsed = 0
            yield evt({"status": "generating", "msg": "ACE-Step 扩散生成中... 已等待 0 秒"})

            while not done_event.is_set():
                await asyncio.sleep(1)
                elapsed += 1
                yield evt({"status": "generating", "msg": f"ACE-Step 扩散生成中... 已等待 {elapsed} 秒"})

            await task

            if error_box:
                yield evt({"status": "error", "msg": error_box["msg"]}); return

            result = result_box.get("data", {})
            filename = result.get("filename", "")
            if not filename:
                yield evt({"status": "error", "msg": "生成完成但未返回音频文件"}); return

            yield evt({"status": "done", "audio_url": f"/api/audio/{filename}"})

        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield evt({"status": "error", "msg": str(e)})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    """从 ace-service 代理音频文件"""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{ACE_SERVICE}/outputs/{filename}",
                            timeout=aiohttp.ClientTimeout(total=30)) as r:
                content = await r.read()
                ctype = r.headers.get("content-type", "audio/mpeg")
        return Response(content=content, media_type=ctype,
                       headers={"Content-Disposition": f'inline; filename="{filename}"',
                                "Cache-Control": "public, max-age=3600"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ── HTTP Proxy ────────────────────────────────────────────────────
@app.api_route("/proxy/{model_id}/{path:path}",
               methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
async def proxy_http(model_id: str, path: str, request: Request):
    models = load_models()
    if model_id not in models:
        return JSONResponse({"error": f"Model {model_id} not found"}, status_code=404)
    base = models[model_id]["internal_url"].rstrip("/")
    url  = f"{base}/{path}"
    qs   = request.url.query
    if qs: url += f"?{qs}"
    body    = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host","content-length","connection","transfer-encoding")}
    SKIP = ("content-encoding","transfer-encoding","connection","content-length")
    async with aiohttp.ClientSession() as s:
        async with s.request(method=request.method, url=url,
                             headers=headers, data=body, allow_redirects=True,
                             timeout=aiohttp.ClientTimeout(total=300)) as r:
            content = await r.read()
            ctype   = r.headers.get("content-type", "")
    out_h = {k: v for k, v in r.headers.items() if k.lower() not in SKIP}
    pfx = f"/proxy/{model_id}"
    if "text/html" in ctype:
        text = content.decode("utf-8", errors="replace")
        text = text.replace('"api_prefix":"/gradio_api"', f'"api_prefix":"{pfx}/gradio_api"')
        text = text.replace('"/gradio_api', f'"{pfx}/gradio_api')
        text = text.replace("'/gradio_api", f"'{pfx}/gradio_api")
        text = text.replace('src="./assets/', f'src="{pfx}/assets/')
        text = text.replace("src='./assets/", f"src='{pfx}/assets/")
        text = text.replace('href="./assets/', f'href="{pfx}/assets/')
        content = text.encode("utf-8")
    out_h["content-length"] = str(len(content))
    return Response(content=content, status_code=r.status, headers=out_h, media_type=ctype)

# ── WebSocket Proxy ───────────────────────────────────────────────
@app.websocket("/proxy/{model_id}/{path:path}")
async def proxy_ws(websocket: WebSocket, model_id: str, path: str):
    models = load_models()
    if model_id not in models:
        await websocket.close(code=1008); return
    base = (models[model_id]["internal_url"]
            .replace("http://","ws://").replace("https://","wss://"))
    target = f"{base.rstrip('/')}/{path}"
    await websocket.accept()
    try:
        import websockets as wsl
        async with wsl.connect(target) as wst:
            async def c2t():
                async for msg in websocket.iter_bytes(): await wst.send(msg)
            async def t2c():
                async for msg in wst:
                    if isinstance(msg, bytes): await websocket.send_bytes(msg)
                    else: await websocket.send_text(msg)
            await asyncio.gather(c2t(), t2c())
    except Exception as e:
        logger.warning(f"WS: {e}")
    finally:
        try: await websocket.close()
        except: pass

# ── Studio HTML (Warm Editorial Design) ──────────────────────────
STUDIO_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>音乐创作室 · Reese</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #F7F5F2;
  --bg2:     #FFFFFF;
  --surface: #FFFFFF;
  --border:  #E8E4DF;
  --bh:      #C9B8A8;
  --ac:      #D4622A;
  --acl:     #E8763E;
  --ach:     #B8501F;
  --acbg:    #FDF1EB;
  --ind:     #4F46E5;
  --indbg:   #EEF2FF;
  --ok:      #16A34A;
  --okbg:    #F0FDF4;
  --err:     #DC2626;
  --errbg:   #FEF2F2;
  --tp:      #1C1917;
  --ts:      #78716C;
  --tm:      #A8A29E;
  --tl:      #C9C4BE;
  --font:    'Inter',-apple-system,sans-serif;
  --r:       10px;
  --rl:      16px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg);color:var(--tp);
  min-height:100vh;line-height:1.6;-webkit-font-smoothing:antialiased}

/* Header */
header{background:var(--bg2);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100}
.hdr{display:flex;align-items:center;justify-content:space-between;
  height:52px;max-width:860px;margin:0 auto;padding:0 24px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:inherit}
.logo-mark{width:30px;height:30px;border-radius:8px;background:var(--ac);
  display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-text{font-size:15px;font-weight:700;color:var(--tp);letter-spacing:-.4px}
.logo-text span{color:var(--ac)}
.nav-pill{font-size:12px;color:var(--ts);text-decoration:none;
  padding:5px 12px;border-radius:20px;border:1px solid var(--border);
  transition:all 150ms;background:var(--bg)}
.nav-pill:hover{border-color:var(--bh);color:var(--tp)}

/* Main layout */
.page{max-width:860px;margin:0 auto;padding:0 24px 80px}

/* Progress steps */
.steps{display:flex;align-items:center;padding:28px 0 24px;gap:0}
.stp{display:flex;align-items:center;gap:10px;flex:1}
.stp-n{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:13px;font-weight:600;flex-shrink:0;
  border:2px solid var(--border);color:var(--tm);background:var(--bg2);
  transition:all 250ms}
.stp-l{font-size:13px;color:var(--ts);transition:color 250ms;white-space:nowrap;
  font-weight:500}
.stp-line{flex:1;height:1px;background:var(--border);margin:0 10px;
  transition:background 250ms;min-width:20px}
.stp.active .stp-n{border-color:var(--ac);background:var(--ac);color:#fff}
.stp.active .stp-l{color:var(--ac);font-weight:600}
.stp.done .stp-n{border-color:var(--ok);background:var(--ok);color:#fff}
.stp.done .stp-l{color:var(--ok)}
.stp.done+.stp-line,.stp-line.done{background:var(--ok)}

/* Section label */
.section-label{font-size:11px;font-weight:600;color:var(--tm);text-transform:uppercase;
  letter-spacing:1.2px;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.section-label::before{content:'';display:block;width:20px;height:2px;background:var(--ac)}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--rl);padding:24px;margin-bottom:14px;
  box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.02)}
.card-hd{font-size:14px;font-weight:600;color:var(--tp);margin-bottom:14px}

/* Input */
label{display:block;font-size:12px;font-weight:500;color:var(--ts);margin-bottom:7px}
textarea, input[type=text]{
  width:100%;background:var(--bg);border:1.5px solid var(--border);
  border-radius:var(--r);padding:12px 14px;color:var(--tp);font-family:var(--font);
  font-size:14px;line-height:1.65;resize:vertical;outline:none;
  transition:border-color 180ms,box-shadow 180ms}
textarea:focus,input:focus{
  border-color:var(--ac);box-shadow:0 0 0 3px rgba(212,98,42,.12);background:#fff}
textarea::placeholder,input::placeholder{color:var(--tl)}

/* Lyrics textarea */
#lyrics-box{min-height:200px;font-family:'SF Mono','Fira Code','Consolas',monospace;
  font-size:13px;line-height:1.9;color:var(--tp)}

/* Chips */
.chip-grid{display:flex;flex-wrap:wrap;gap:8px}
.chip{padding:7px 16px;border-radius:20px;font-size:13px;font-weight:500;
  cursor:pointer;border:1.5px solid var(--border);color:var(--ts);background:#fff;
  font-family:var(--font);transition:all 140ms;user-select:none}
.chip:hover{border-color:var(--bh);color:var(--tp)}
.chip.on{border-color:var(--ac);background:var(--acbg);color:var(--ac);font-weight:600}

/* Duration chips */
.dur-chip{padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;
  cursor:pointer;border:1.5px solid var(--border);color:var(--ts);background:#fff;
  font-family:var(--font);transition:all 140ms}
.dur-chip:hover{border-color:var(--bh);color:var(--tp)}
.dur-chip.on{border-color:var(--ac);background:var(--acbg);color:var(--ac);font-weight:600}

/* Model selector */
.model-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.model-card{padding:14px 16px;border-radius:var(--r);border:2px solid var(--border);
  cursor:pointer;background:#fff;transition:all 140ms}
.model-card:hover{border-color:var(--bh)}
.model-card.on{border-color:var(--ac);background:var(--acbg)}
.model-card.unavail{opacity:.5;cursor:not-allowed}
.mc-name{font-size:13px;font-weight:600;color:var(--tp);margin-bottom:3px}
.mc-desc{font-size:11.5px;color:var(--ts);line-height:1.5}
.mc-badge{display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-weight:600;
  padding:2px 8px;border-radius:20px;margin-top:6px}
.mc-badge.online{background:var(--okbg);color:var(--ok)}
.mc-badge.offline{background:#FEF2F2;color:#DC2626}
.mc-badge.soon{background:#F5F3FF;color:#7C3AED}
.dot{width:5px;height:5px;border-radius:50%;background:currentColor}
.dot.online{animation:dp 2s infinite}
@keyframes dp{0%,100%{opacity:1}50%{opacity:.35}}

/* Buttons */
.btn-main{width:100%;padding:13px 20px;border-radius:var(--r);background:var(--ac);
  color:#fff;font-family:var(--font);font-size:14px;font-weight:600;cursor:pointer;
  border:none;display:flex;align-items:center;justify-content:center;gap:8px;
  transition:all 140ms;letter-spacing:-.1px}
.btn-main:hover:not(:disabled){background:var(--ach);transform:translateY(-1px);
  box-shadow:0 4px 16px rgba(212,98,42,.3)}
.btn-main:active:not(:disabled){transform:translateY(0)}
.btn-main:disabled{background:var(--border);color:var(--tm);cursor:not-allowed;transform:none;box-shadow:none}
.btn-ghost{font-size:12.5px;color:var(--ts);padding:6px 12px;border-radius:8px;
  border:1px solid var(--border);background:#fff;font-family:var(--font);
  cursor:pointer;transition:all 140ms}
.btn-ghost:hover{border-color:var(--bh);color:var(--tp)}

/* Status */
.status{display:none;align-items:flex-start;gap:10px;padding:12px 14px;
  border-radius:var(--r);font-size:13px;margin-top:12px;line-height:1.5}
.status.show{display:flex}
.status.generating{background:var(--indbg);border:1px solid #C7D2FE;color:var(--ind)}
.status.ok{background:var(--okbg);border:1px solid #BBF7D0;color:var(--ok)}
.status.error{background:var(--errbg);border:1px solid #FECACA;color:var(--err)}
.status-ico{flex-shrink:0;margin-top:1px}

/* Progress */
.prog{margin-top:16px;display:none}
.prog.show{display:block}
.prog-track{height:5px;background:var(--border);border-radius:3px;overflow:hidden}
.prog-fill{height:100%;background:linear-gradient(90deg,var(--ac),var(--acl));
  border-radius:3px;width:0;transition:width .4s ease}
.prog-fill.run{animation:pg 1.6s ease-in-out infinite}
@keyframes pg{0%,100%{transform:translateX(-100%)}50%{transform:translateX(0)}}
.prog-meta{display:flex;justify-content:space-between;margin-top:7px;
  font-size:11.5px;color:var(--tm)}

/* Audio result */
.result{margin-top:20px;display:none;padding:20px;background:var(--okbg);
  border:1px solid #BBF7D0;border-radius:var(--rl)}
.result.show{display:block}
.result-title{font-size:14px;font-weight:600;color:var(--ok);margin-bottom:12px;
  display:flex;align-items:center;gap:7px}
audio{width:100%;border-radius:8px;margin-bottom:12px}
.result-actions{display:flex;gap:8px;flex-wrap:wrap}
.result-actions a,.result-actions button{font-size:12.5px;padding:7px 14px;
  border-radius:8px;text-decoration:none;cursor:pointer;font-family:var(--font);
  transition:all 140ms}
.result-actions a{background:var(--ok);color:#fff;border:none}
.result-actions a:hover{opacity:.88}
.result-actions button{background:#fff;color:var(--ts);border:1px solid var(--border)}
.result-actions button:hover{border-color:var(--bh);color:var(--tp)}

/* Spinner */
.spin{width:15px;height:15px;border:2px solid currentColor;border-top-color:transparent;
  border-radius:50%;animation:s .7s linear infinite;flex-shrink:0}
@keyframes s{to{transform:rotate(360deg)}}

/* Divider */
.sep{height:1px;background:var(--border);margin:18px 0}

/* Hidden sections */
.sec{display:none}
.sec.on{display:block}

/* Lyrics hint */
.hint{font-size:11.5px;color:var(--tm);margin-top:7px;line-height:1.7}
.hint code{color:var(--ac);font-family:'SF Mono',monospace;font-size:11px;
  background:var(--acbg);padding:1px 5px;border-radius:3px}

/* Footer */
.foot{text-align:center;font-size:11.5px;color:var(--tm);margin-top:50px;
  padding-top:20px;border-top:1px solid var(--border)}

@media(max-width:540px){
  .steps{gap:2px}
  .stp-l{font-size:11px}
  .card{padding:16px}
  .model-cards{grid-template-columns:1fr}
}
</style>
</head>
<body>
<header>
  <div class="hdr">
    <a class="logo" href="/reese/">
      <div class="logo-mark">
        <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
          <path d="M9 18V5l12-2v13" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
          <circle cx="6" cy="18" r="3" stroke="#fff" stroke-width="2.2"/>
          <circle cx="18" cy="16" r="3" stroke="#fff" stroke-width="2.2"/>
        </svg>
      </div>
      <div class="logo-text">Music<span>AI</span> 创作室</div>
    </a>
    <a class="nav-pill" href="/reese/proxy/ace-step/" target="_blank">专业模式 ↗</a>
  </div>
</header>

<main class="page">

<!-- Steps -->
<div class="steps" id="steps">
  <div class="stp active" id="s1"><div class="stp-n">1</div><div class="stp-l">灵感</div></div>
  <div class="stp-line" id="l1"></div>
  <div class="stp" id="s2"><div class="stp-n">2</div><div class="stp-l">歌词</div></div>
  <div class="stp-line" id="l2"></div>
  <div class="stp" id="s3"><div class="stp-n">3</div><div class="stp-l">生成</div></div>
</div>

<!-- ── Step 1 ────────────────────────────────────────────── -->
<div id="p1" class="sec on">

  <div class="section-label">第一步：告诉我你想创作什么</div>

  <div class="card">
    <div class="card-hd" style="display:flex;align-items:center;justify-content:space-between">
      <span>主题 / 故事</span>
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12.5px;color:var(--ts);font-weight:500;margin:0">
        <input type="checkbox" id="own-lyrics-chk" onchange="toggleOwnLyrics(this.checked)"
          style="width:15px;height:15px;accent-color:var(--ac);cursor:pointer;margin:0">
        使用自己的歌词
      </label>
    </div>

    <!-- AI mode: theme input -->
    <div id="ai-mode">
      <label for="theme">用一句话描述你的歌曲想法</label>
      <textarea id="theme" rows="3"
        placeholder="例如：一个人在深夜的城市里骑车，路灯一盏一盏亮起来，想着离家千里的父母&#10;或者：初夏的校园，考完最后一门课，和同学一起看夕阳，知道要分开了&#10;或者：年轻人拼搏奋斗，相信努力会被看见"></textarea>
    </div>

    <!-- Custom lyrics mode: raw input -->
    <div id="custom-mode" style="display:none">
      <label for="custom-lyr">输入你的歌词（AI 会自动添加 [verse]/[chorus] 等结构标签）</label>
      <textarea id="custom-lyr" rows="10" spellcheck="false"
        placeholder="直接输入你写好的歌词&#10;AI 会识别段落结构，按照 ACP 格式组装&#10;&#10;例如：&#10;走在熟悉的街道&#10;风吹过心里的浪潮&#10;&#10;（副歌）&#10;我们的故事还没有结局"></textarea>
      <div class="hint" style="margin-top:8px">不需要手动加标签，AI 会根据内容自动判断段落类型</div>
    </div>
  </div>

  <div class="card" id="style-card">
    <div class="card-hd">音乐风格</div>
    <div class="chip-grid" id="genre-g">
      <button class="chip on" data-v="流行">流行</button>
      <button class="chip" data-v="古风">古风</button>
      <button class="chip" data-v="摇滚">摇滚</button>
      <button class="chip" data-v="爵士">爵士</button>
      <button class="chip" data-v="R&B">R&amp;B</button>
      <button class="chip" data-v="电子">电子</button>
      <button class="chip" data-v="说唱">说唱</button>
      <button class="chip" data-v="民谣">民谣</button>
      <button class="chip" data-v="古典">古典</button>
    </div>
  </div>

  <div class="card" id="mood-card">
    <div class="card-hd">情绪基调</div>
    <div class="chip-grid" id="mood-g">
      <button class="chip on" data-v="欢快">欢快</button>
      <button class="chip" data-v="悲伤">悲伤</button>
      <button class="chip" data-v="激昂">激昂</button>
      <button class="chip" data-v="平静">平静</button>
      <button class="chip" data-v="浪漫">浪漫</button>
      <button class="chip" data-v="神秘">神秘</button>
    </div>
  </div>

  <button class="btn-main" id="btn1" onclick="doLyrics()">
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" id="btn1-ico">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/>
    </svg>
    <span id="btn1-txt">用 AI 生成歌词</span>
  </button>
  <div class="status" id="st1">
    <div class="spin status-ico"></div>
    <span id="st1m">Qwen3 创作中，约 10~20 秒...</span>
  </div>

</div>

<!-- ── Step 2 ────────────────────────────────────────────── -->
<div id="p2" class="sec">

  <div class="section-label" style="justify-content:space-between;display:flex;align-items:center">
    <span style="display:flex;align-items:center;gap:8px">
      <span style="width:20px;height:2px;background:var(--ac);display:block"></span>
      第二步：确认歌词 &amp; 选择模型
    </span>
    <button class="btn-ghost" onclick="go(1)">← 重新输入</button>
  </div>

  <div class="card">
    <div class="card-hd" style="display:flex;align-items:center;justify-content:space-between">
      <span>歌词预览（可直接编辑）</span>
      <button class="btn-ghost" onclick="doLyrics(true)">🔄 重新生成</button>
    </div>
    <textarea id="lyr" rows="14" spellcheck="false"></textarea>
    <div class="hint">
      结构标签：<code>[verse]</code> 主歌 &nbsp;<code>[chorus]</code> 副歌 &nbsp;
      <code>[bridge]</code> 桥段 &nbsp;<code>[outro]</code> 尾声 — 请保留这些标签
    </div>
  </div>

  <div class="card">
    <div class="card-hd">生成模型</div>
    <div class="model-cards" id="model-cards">
      <!-- filled by JS -->
    </div>
  </div>

  <div class="card">
    <div class="card-hd">时长</div>
    <div class="chip-grid" id="dur-g">
      <button class="dur-chip" data-v="30">30 秒</button>
      <button class="dur-chip on" data-v="60">1 分钟</button>
      <button class="dur-chip" data-v="90">1.5 分钟</button>
      <button class="dur-chip" data-v="120">2 分钟</button>
      <button class="dur-chip" data-v="180">3 分钟</button>
    </div>
  </div>

  <button class="btn-main" id="btn2" onclick="doMusic()">
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
      <path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
      <circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="2.2"/>
      <circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="2.2"/>
    </svg>
    生成音乐
  </button>

  <div class="prog" id="prog">
    <div class="prog-track"><div class="prog-fill run" id="pf"></div></div>
    <div class="prog-meta"><span id="st2m">连接中...</span><span id="timer">0:00</span></div>
  </div>
  <div class="status" id="st2"></div>

  <div class="result" id="result">
    <div class="result-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
        <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      生成完成
    </div>
    <audio id="ap" controls></audio>
    <div class="result-actions">
      <a id="dl" download="music.mp3">⬇ 下载 MP3</a>
      <button onclick="doMusic()">🔄 重新生成</button>
      <button onclick="go(1)">✏️ 修改歌词</button>
    </div>
  </div>

</div>

<div class="foot">Powered by ACE-Step 1.5 · SongGeneration 2 · Qwen3:30B · Reese M3 Max 128GB</div>
</main>

<script>
const BASE = location.pathname.includes('/reese') ? '/reese' : '';
let ST = { genre:'流行', mood:'欢快', dur:60, model:'ace-step' };
let ticker = null;

// chips
function chips(id, key) {
  document.getElementById(id).querySelectorAll('.chip').forEach(b => {
    b.onclick = () => {
      document.getElementById(id).querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
      b.classList.add('on'); ST[key] = b.dataset.v;
    };
  });
}
function durChips() {
  document.getElementById('dur-g').querySelectorAll('.dur-chip').forEach(b => {
    b.onclick = () => {
      document.getElementById('dur-g').querySelectorAll('.dur-chip').forEach(x=>x.classList.remove('on'));
      b.classList.add('on'); ST.dur = +b.dataset.v;
    };
  });
}
chips('genre-g','genre'); chips('mood-g','mood'); durChips();

// steps
function go(n) {
  [1,2,3].forEach(i => {
    document.getElementById('p'+i)?.classList.remove('on');
    const s = document.getElementById('s'+i);
    s.classList.remove('active','done');
    if(i<n) s.classList.add('done');
    if(i===n) s.classList.add('active');
  });
  document.getElementById('p'+n)?.classList.add('on');
  document.getElementById('l1')?.classList.toggle('done', n>1);
  document.getElementById('l2')?.classList.toggle('done', n>2);
  window.scrollTo({top:0, behavior:'smooth'});
}

// status helpers
function st1(type, msg) {
  const el = document.getElementById('st1');
  if(type==='hide'){el.classList.remove('show');return;}
  el.className = 'status show ' + type;
  // 重建内容，保持 spin 只在 generating 时显示
  if(type==='generating') {
    el.innerHTML = '<div class="spin status-ico"></div><span id="st1m"></span>';
  } else {
    el.innerHTML = '<span id="st1m"></span>';
  }
  document.getElementById('st1m').textContent = msg;
}
function st2(type, msg) {
  const el = document.getElementById('st2');
  if(type==='hide'){el.classList.remove('show');return;}
  el.className = 'status show ' + type;
  el.innerHTML = msg;
}

// timer
function startT() {
  let s = 0; clearInterval(ticker);
  ticker = setInterval(()=>{
    s++; const m=Math.floor(s/60), ss=s%60;
    document.getElementById('timer').textContent = m+':'+(ss<10?'0':'')+ss;
  }, 1000);
}
function stopT() { clearInterval(ticker); }

// model cards
async function loadModels() {
  try {
    const ms = await (await fetch(BASE+'/api/models')).json();
    const wrap = document.getElementById('model-cards');
    const NAMES = {'ace-step':'ACE-Step 1.5','song-gen':'SongGeneration 2'};
    const DESCS = {
      'ace-step':'快速扩散生成，支持中文歌词，MIT 协议',
      'song-gen':'腾讯+清华联合研发，音乐性最强，4B 参数',
    };
    wrap.innerHTML = ms.map(m => {
      const avail = m.status==='online';
      const sel = m.id === ST.model;
      return `<div class="model-card${sel?' on':''}${!avail?' unavail':''}"
        onclick="${avail?`selModel('${m.id}',this)`:''}" id="mc-${m.id}">
        <div class="mc-name">${NAMES[m.id]||m.name}</div>
        <div class="mc-desc">${DESCS[m.id]||m.description}</div>
        <span class="mc-badge ${m.status}">
          <span class="dot ${m.status}"></span>${m.status==='online'?'可用':'离线'}
        </span>
      </div>`;
    }).join('');
    // Add SongGen placeholder if not registered yet
    if(!ms.find(m=>m.id==='song-gen')) {
      wrap.innerHTML += `<div class="model-card unavail">
        <div class="mc-name">SongGeneration 2</div>
        <div class="mc-desc">腾讯+清华联合研发，安装中...</div>
        <span class="mc-badge soon"><span class="dot"></span>安装中</span>
      </div>`;
    }
  } catch(e) {}
}
function selModel(id, el) {
  document.querySelectorAll('.model-card').forEach(c=>c.classList.remove('on'));
  el.classList.add('on'); ST.model = id;
}

// own lyrics toggle — 风格/情绪卡片始终保留，仅切换输入区
function toggleOwnLyrics(on) {
  document.getElementById('ai-mode').style.display = on ? 'none' : 'block';
  document.getElementById('custom-mode').style.display = on ? 'block' : 'none';
  document.getElementById('btn1-txt').textContent = on ? '格式化为 ACP 结构 →' : '用 AI 生成歌词';
}

// lyrics
async function doLyrics(regen=false) {
  const useOwn = document.getElementById('own-lyrics-chk').checked;
  const payload = {genre: ST.genre, mood: ST.mood};

  if(useOwn) {
    const custom = document.getElementById('custom-lyr').value.trim();
    if(!custom) {
      const ta = document.getElementById('custom-lyr');
      ta.style.borderColor='var(--err)'; ta.focus();
      setTimeout(()=>ta.style.borderColor='',1800); return;
    }
    payload.custom_lyrics = custom;
  } else {
    const theme = document.getElementById('theme').value.trim();
    if(!theme && !regen) {
      const ta = document.getElementById('theme');
      ta.style.borderColor='var(--err)'; ta.focus();
      setTimeout(()=>ta.style.borderColor='',1800); return;
    }
    payload.theme = theme;
  }

  const btn = document.getElementById('btn1');
  btn.disabled = true;
  document.getElementById('btn1-ico').style.display = 'none';
  document.getElementById('btn1-txt').textContent = useOwn ? 'ACP 格式化中...' : 'AI 生成中...';
  const spin1 = document.createElement('div'); spin1.className = 'spin'; spin1.id = 'btn1-spin';
  btn.insertBefore(spin1, btn.firstChild);

  // 实时计时器——qwen3:30b 思维模型通常需要 30~90 秒
  let elapsed = 0;
  const baseMsg = useOwn ? 'Qwen2.5 正在整理 ACP 歌词结构' : `Qwen2.5 正在创作「${ST.genre}·${ST.mood}」歌词`;
  const updateStatus = () => {
    elapsed++;
    const dots = '.'.repeat((elapsed % 3) + 1);
    document.getElementById('st1m').textContent = `${baseMsg}${dots}  已等待 ${elapsed} 秒`;
  };
  st1('generating', baseMsg + '...  已等待 0 秒');
  const statusTick = setInterval(updateStatus, 1000);

  try {
    const r = await fetch(BASE+'/api/lyrics', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const d = await r.json();
    if(d.error) throw new Error(d.error);

    // 空歌词保护：不要跳到第二步，给用户明确提示
    const lyrics = (d.lyrics || '').trim();
    if(!lyrics) throw new Error('模型未返回歌词内容，请点击重试');

    document.getElementById('lyr').value = lyrics;
    st1('hide');
    await loadModels();
    go(2);
  } catch(e) {
    st1('error', '处理失败：' + e.message + '（可直接点击重试）');
  } finally {
    clearInterval(statusTick);
    btn.disabled = false;
    document.getElementById('btn1-spin')?.remove();
    document.getElementById('btn1-ico').style.display = '';
    const isOwn = document.getElementById('own-lyrics-chk').checked;
    document.getElementById('btn1-txt').textContent = isOwn ? '格式化为 ACP 结构 →' : '用 AI 生成歌词';
  }
}

// generate music
async function doMusic() {
  const lyr = document.getElementById('lyr').value.trim();
  if(!lyr) { alert('歌词不能为空'); return; }

  const btn = document.getElementById('btn2');
  btn.disabled = true;
  btn.innerHTML = '<div class="spin"></div> 生成中...';

  document.getElementById('result').classList.remove('show');
  document.getElementById('prog').classList.add('show');
  document.getElementById('pf').className = 'prog-fill run';
  st2('hide');
  startT();
  document.getElementById('st2m').textContent = '连接中...';

  try {
    const resp = await fetch(BASE+'/api/generate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({lyrics:lyr, genre:ST.genre, mood:ST.mood, duration:ST.dur, model:ST.model})
    });
    const reader = resp.body.getReader(), dec = new TextDecoder();
    let buf = '';
    while(true) {
      const {done,value} = await reader.read();
      if(done) break;
      buf += dec.decode(value,{stream:true});
      const lines = buf.split('\\n'); buf = lines.pop();
      for(const ln of lines) {
        if(!ln.startsWith('data:')) continue;
        let p; try { p=JSON.parse(ln.slice(5).trim()); } catch{ continue; }
        if(p.status==='starting'||p.status==='generating') {
          document.getElementById('st2m').textContent = p.msg||'生成中...';
        } else if(p.status==='done') {
          stopT(); document.getElementById('prog').classList.remove('show'); st2('hide');
          const url = BASE + p.audio_url;
          document.getElementById('ap').src = url;
          document.getElementById('dl').href = url;
          document.getElementById('result').classList.add('show');
          document.getElementById('result').scrollIntoView({behavior:'smooth',block:'center'});
          document.getElementById('ap').play().catch(()=>{});
        } else if(p.status==='error') {
          stopT(); document.getElementById('prog').classList.remove('show');
          st2('error', '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" style="flex-shrink:0;margin-top:1px"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><span>生成失败：'+(p.msg||'未知错误')+'</span>');
        }
      }
    }
  } catch(e) {
    stopT(); document.getElementById('prog').classList.remove('show');
    st2('error', '<span>请求失败：'+e.message+'</span>');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="2.2"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="2.2"/></svg> 生成音乐';
  }
}

document.getElementById('theme').addEventListener('keydown', e => {
  if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)) doLyrics();
});
</script>
</body>
</html>
"""

# ── Dashboard (Warm Editorial) ────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Music AI · Reese</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#F7F5F2;--surf:#fff;--bd:#E8E4DF;--bh:#C9B8A8;
  --ac:#D4622A;--acl:#E8763E;--acbg:#FDF1EB;
  --ok:#16A34A;--okbg:#F0FDF4;--off:#DC2626;--offbg:#FEF2F2;
  --tp:#1C1917;--ts:#78716C;--tm:#A8A29E;--font:'Inter',-apple-system,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--tp);min-height:100vh;-webkit-font-smoothing:antialiased}
header{background:var(--surf);border-bottom:1px solid var(--bd);position:sticky;top:0;z-index:100}
.hdr{max-width:1100px;margin:0 auto;padding:0 28px;height:56px;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:inherit}
.logo-mk{width:32px;height:32px;border-radius:8px;background:var(--ac);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-tx{font-size:15px;font-weight:700;letter-spacing:-.3px}
.logo-tx span{color:var(--ac)}
.badge{font-size:11.5px;font-weight:500;color:var(--tm);padding:4px 10px;border-radius:20px;background:#F5F5F4;border:1px solid var(--bd)}
.wrap{max-width:1100px;margin:0 auto;padding:0 28px}
.hero{padding:52px 0 40px}
.hero-eyebrow{font-size:11px;font-weight:600;color:var(--ac);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}
.hero h1{font-size:clamp(28px,4vw,42px);font-weight:700;line-height:1.1;letter-spacing:-.8px;margin-bottom:14px;color:var(--tp)}
.hero h1 em{font-style:normal;color:var(--ac)}
.hero p{font-size:15px;color:var(--ts);max-width:520px;line-height:1.7;margin-bottom:28px}
.cta-row{display:flex;gap:10px;flex-wrap:wrap}
.cta{display:inline-flex;align-items:center;gap:7px;padding:11px 22px;border-radius:10px;
  font-size:13.5px;font-weight:600;text-decoration:none;transition:all 140ms;letter-spacing:-.1px}
.cta-p{background:var(--ac);color:#fff}
.cta-p:hover{background:var(--acl);transform:translateY(-1px);box-shadow:0 4px 16px rgba(212,98,42,.3)}
.cta-s{border:1.5px solid var(--bd);color:var(--ts);background:var(--surf)}
.cta-s:hover{border-color:var(--bh);color:var(--tp)}
.sec-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-top:8px}
.sec-lb{font-size:11px;font-weight:600;color:var(--tm);text-transform:uppercase;letter-spacing:1.3px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-bottom:60px}
.mc{background:var(--surf);border:1.5px solid var(--bd);border-radius:16px;padding:22px;
  cursor:pointer;transition:all 160ms;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.mc:hover{border-color:var(--bh);box-shadow:0 4px 16px rgba(0,0,0,.08);transform:translateY(-2px)}
.mc-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px}
.mc-ico{width:44px;height:44px;border-radius:12px;background:var(--acbg);border:1.5px solid #F5D5C5;
  display:flex;align-items:center;justify-content:center;color:var(--ac)}
.mc-sta{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:600;
  padding:3px 10px;border-radius:20px}
.mc-sta.online{background:var(--okbg);color:var(--ok)}
.mc-sta.offline{background:var(--offbg);color:var(--off)}
.mc-sta.checking{background:#FEF9C3;color:#CA8A04}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor}
.dot.online{animation:dp 2s infinite}
@keyframes dp{0%,100%{opacity:1}50%{opacity:.3}}
.mc-name{font-size:15px;font-weight:700;color:var(--tp);margin-bottom:3px;letter-spacing:-.2px}
.mc-auth{font-size:11.5px;color:var(--tm);margin-bottom:8px}
.mc-desc{font-size:13px;color:var(--ts);line-height:1.6;margin-bottom:14px}
.mc-caps{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.cap{font-size:11.5px;font-weight:500;color:var(--ac);background:var(--acbg);
  border:1px solid #F5D5C5;padding:2px 9px;border-radius:20px}
.btn{width:100%;padding:11px 16px;border-radius:10px;font-family:var(--font);font-size:13.5px;
  font-weight:600;cursor:pointer;border:none;display:flex;align-items:center;justify-content:center;gap:7px;transition:all 140ms}
.btn-p{background:var(--ac);color:#fff}
.btn-p:hover:not(:disabled){background:var(--acl);transform:translateY(-1px);box-shadow:0 4px 14px rgba(212,98,42,.3)}
.btn-p:disabled{background:#E7E5E4;color:var(--tm);cursor:not-allowed;transform:none;box-shadow:none}
.skel{background:linear-gradient(90deg,#F5F5F4 25%,#FAFAF9 50%,#F5F5F4 75%);background-size:200% 100%;animation:sh 1.4s infinite;border-radius:8px}
@keyframes sh{0%{background-position:200% 0}100%{background-position:-200% 0}}
footer{border-top:1px solid var(--bd);padding:28px 0}
.ftr{display:flex;align-items:center;justify-content:space-between;font-size:12px;color:var(--tm)}
.flinks{display:flex;gap:20px}
.flinks a{color:var(--tm);text-decoration:none;transition:color 140ms}
.flinks a:hover{color:var(--ts)}
</style>
</head>
<body>
<header><div class="hdr">
  <a class="logo" href="/reese/">
    <div class="logo-mk"><svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><circle cx="6" cy="18" r="3" stroke="#fff" stroke-width="2.2"/><circle cx="18" cy="16" r="3" stroke="#fff" stroke-width="2.2"/></svg></div>
    <div class="logo-tx">Music<span>AI</span></div>
  </a>
  <div class="badge">Reese · M3 Max · 128 GB</div>
</div></header>

<main><div class="wrap">
  <div class="hero">
    <div class="hero-eyebrow">AI 音乐创作平台</div>
    <h1>本地音乐大模型<br><em>统一创作入口</em></h1>
    <p>主题 → 歌词 → 音乐，一站式生成。支持多模型切换，中文歌词原生支持。</p>
    <div class="cta-row">
      <a class="cta cta-p" href="/reese/studio">🎵 开始创作</a>
      <a class="cta cta-s" href="/reese/api/models" target="_blank">查看 API</a>
    </div>
  </div>
  <div class="sec-hd">
    <span class="sec-lb">已注册模型</span>
    <span style="font-size:12px;color:var(--tm)" id="cnt">—</span>
  </div>
  <div class="grid" id="grid">
    <div class="mc" style="pointer-events:none">
      <div class="skel" style="height:44px;width:44px;border-radius:12px;margin-bottom:14px"></div>
      <div class="skel" style="height:17px;width:50%;margin-bottom:7px"></div>
      <div class="skel" style="height:13px;width:32%;margin-bottom:14px"></div>
      <div class="skel" style="height:13px;margin-bottom:7px"></div>
      <div class="skel" style="height:13px;width:80%;margin-bottom:16px"></div>
      <div class="skel" style="height:42px;border-radius:10px"></div>
    </div>
  </div>
</div></main>

<footer><div class="wrap"><div class="ftr">
  <span>Music AI Gateway v2.1 · Reese</span>
  <div class="flinks">
    <a href="/reese/studio">创作室</a>
    <a href="/reese/api/models">API</a>
    <a href="/reese/api/health">Health</a>
  </div>
</div></div></footer>

<script>
const BASE = location.pathname.startsWith('/reese') ? '/reese' : '';
const CAPS = {text2music:'Text→Music',audio2audio:'Audio Remix',cover:'Cover',repaint:'Repaint',lyric2music:'Lyrics→Song'};
const NAMES = {'ace-step':'ACE-Step 1.5','song-gen':'SongGeneration 2'};
const AUTHORS = {'ace-step':'ACE Studio × 阶跃星辰','song-gen':'腾讯 × 清华大学'};
const DESCS = {
  'ace-step':'快速扩散生成，支持中英日三语歌词，MIT 协议开源。',
  'song-gen':'商业级音质，PER 8.55%，全面超越开源基线，4B 参数。',
};

function render(models) {
  document.getElementById('cnt').textContent = models.length + ' 个模型';
  const grid = document.getElementById('grid');
  if(!models.length) { grid.innerHTML='<div style="color:var(--tm);padding:40px;grid-column:1/-1">暂无模型</div>'; return; }
  grid.innerHTML = models.map(m => {
    const off = m.status==='offline';
    const caps = (m.capabilities||[]).slice(0,4).map(c=>`<span class="cap">${CAPS[c]||c}</span>`).join('');
    const su = BASE+'/studio';
    return `<div class="mc" onclick="${off?'':\"window.location='\"+su+\"'\"}">
      <div class="mc-top">
        <div class="mc-ico"><svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="2"/></svg></div>
        <div class="mc-sta ${m.status}"><span class="dot ${m.status}"></span>${m.status==='online'?'在线':'离线'}</div>
      </div>
      <div class="mc-name">${NAMES[m.id]||m.name}</div>
      <div class="mc-auth">${AUTHORS[m.id]||m.author||''}</div>
      <div class="mc-desc">${DESCS[m.id]||m.description}</div>
      ${caps?`<div class="mc-caps">${caps}</div>`:''}
      <button class="btn btn-p" ${off?'disabled':''} onclick="event.stopPropagation();window.location='${su}'">🎵 开始创作</button>
    </div>`;
  }).join('');
}

async function load() {
  try { render(await (await fetch(BASE+'/api/models')).json()); }
  catch { document.getElementById('grid').innerHTML='<div style="color:var(--off);grid-column:1/-1;padding:40px">加载失败，请刷新</div>'; }
}
load(); setInterval(load, 30000);
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────
@app.get("/",             response_class=HTMLResponse)
@app.get("/reese",        response_class=HTMLResponse)
@app.get("/reese/",       response_class=HTMLResponse)
async def dashboard():    return DASHBOARD_HTML

@app.get("/studio",       response_class=HTMLResponse)
@app.get("/reese/studio", response_class=HTMLResponse)
async def studio():       return STUDIO_HTML

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1988, log_level="info")
