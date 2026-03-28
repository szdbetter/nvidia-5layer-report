#!/usr/bin/env python3
"""
AI Services Telegram Bot v2 - 赚钱引擎P0
接单通道：PDF分析 + 图片描述
Uses MiniMax VL API via mcporter for image understanding.
PDF pages converted to images via PyMuPDF + PIL.
"""
import os, sys, json, tempfile, subprocess, shutil, re
from pathlib import Path

BOT_TOKEN = "8055188738:AAEUcRH1KbuUSSKH4yxfS0x9gv4GbOuU6e4"
STATE_FILE = "/tmp/ai_services_bot_state.json"
LOG_FILE = "/tmp/ai_services_bot.log"

SERVICES = {
    "pdf": {
        "name": "PDF\u667a\u80fd\u5206\u6790",
        "price": "\u00a59.9",
        "emoji": "\ud83d\udcc4",
        "prompt": (
            "You are a professional document analysis assistant. Analyze this document page carefully.\n"
            "Extract and return in structured format:\n"
            "1) Document type, title, and source\n"
            "2) Key findings, data points, and main arguments (be specific with numbers/dates)\n"
            "3) Important statistics, references, and citations\n"
            "4) Executive summary (3-5 sentences)\n"
            "Respond in Chinese if the content appears to be Chinese, otherwise English."
        )
    },
    "image": {
        "name": "\u5546\u54c1\u56fe\u591a\u8bed\u8a00\u63cf\u8ff0",
        "price": "$18",
        "emoji": "\ud83d\uddbc",
        "prompt": (
            "You are an expert e-commerce product analyst. Analyze this product image.\n"
            "Generate all of the following in structured markdown:\n"
            "1) Product category and type\n"
            "2) Detailed product description (2-3 sentences)\n"
            "3) Five-point listing copy (bullet points, action-oriented)\n"
            "4) SEO keywords (10-15 keywords)\n"
            "5) Platform tags for: Amazon, Shopee, Taobao\n"
            "6) Descriptions in: English, Japanese, Korean, Thai\n"
            "Format as clean markdown."
        )
    }
}

WELCOME = f"""\ud83d\udc4b *\u6b22\u8fce\u6765\u5230 AI Services Bot*\n\n\u63d0\u4f9b\u4e24\u79cd\u670d\u52a1\uff1a\n\n{SERVICES['pdf']['emoji']} *PDF\u667a\u80fd\u5206\u6790* \u2014 {SERVICES['pdf']['price']}/\u6587\u6863\n   PDF/\u62a5\u544a \u2192 \u5173\u952e\u4fe1\u606f+\u6458\u8981+\u6570\u636e\u63d0\u53d6\n\n{SERVICES['image']['emoji']} *\u5546\u54c1\u56fe\u591a\u8bed\u8a00\u63cf\u8ff0* \u2014 {SERVICES['image']['price']}/\u5f20\n   \u4ea7\u54c1\u56fe \u2192 \u82f1/\u65e5/\u97d3/\u6cf0\u4e94\u70b9\u63cf\u8ff0+SEO\n\n---\n\ud83d\udc47 \u6309\u4e0b\u65b9\u82f1\u6587\u6309\u94ae\u5f00\u59cb\u4e0b\u5355\uff01\n"""

def log(msg):
    ts = subprocess.getoutput("date '+%Y-%m-%d %H:%M:%S'")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def tg_request(method, params=None, data=None):
    import urllib.request, urllib.parse, urllib.error
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if data:
            enc = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(url, data=enc)
        elif params:
            req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"TG error {method}: {e}")
        return None

def send_message(chat_id, text, parse_mode="Markdown"):
    return tg_request("sendMessage", data={
        "chat_id": chat_id,
        "text": str(text)[:4096],
        "parse_mode": parse_mode
    })

def send_keyboard(chat_id, text, rows, parse_mode="Markdown"):
    keyboard = [[{"text": btn} for btn in row] for row in rows]
    return tg_request("sendMessage", data={
        "chat_id": chat_id,
        "text": str(text)[:4096],
        "parse_mode": parse_mode,
        "reply_markup": json.dumps({"inline_keyboard": keyboard})
    })

def answer_callback(query_id, text=""):
    return tg_request("answerCallbackQuery", data={
        "callback_query_id": query_id,
        "text": str(text)[:200],
        "show_alert": False
    })

def download_file(file_id, ext):
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.close()
    try:
        # Get file path
        r = tg_request("getFile", params={"file_id": file_id})
        if not r or not r.get("ok"):
            return None
        file_path = r["result"]["file_path"]
        # Download
        dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        req = urllib.request.Request(dl_url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(tmp.name, "wb") as f:
                shutil.copyfileobj(resp, f)
        return tmp.name
    except Exception as e:
        log(f"Download error: {e}")
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        return None

def pdf_to_images(pdf_path, max_pages=3):
    """Convert PDF pages to JPEG images using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        images = []
        tmpdir = tempfile.mkdtemp()
        doc = fitz.open(pdf_path)
        for i in range(min(max_pages, len(doc))):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            out_path = f"{tmpdir}/page_{i+1}.jpg"
            pix.save(out_path)
            images.append(out_path)
        doc.close()
        return images, tmpdir
    except Exception as e:
        log(f"PDF convert error: {e}")
        return [], ""

def minimax_image(prompt, image_path):
    """Call MiniMax VL via mcporter"""
    cmd = [
        "mcporter", "call", "MiniMax.understand_image",
        f"prompt={prompt}",
        f"image_source={image_path}",
        "--output", "json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            content = data.get("content", [])
            if isinstance(content, list) and content:
                return content[0].get("text", "")
            return str(data)[:500]
        return f"[mcporter error] {result.stderr[:200]}"
    except Exception as e:
        return f"[Exception] {e}"

def process_service(chat_id, service_type, file_path, file_ext):
    send_message(chat_id, f"\u23f3 \u5f00\u59cb\u5206\u6790 {SERVICES[service_type]['emoji']} {SERVICES[service_type]['name']}\uff0c\u8bf7\u7a0d\u5019...\n\n(\u901a\u5e38\u9700\u8981 15-60 \u79d2)")
    
    svc = SERVICES[service_type]
    
    if service_type == "pdf":
        images, tmpdir = pdf_to_images(file_path, max_pages=3)
        if not images:
            send_message(chat_id, "\u26a0\ufe0f PDF \u89e3\u6790\u5931\u8d25\uff0c\u8bf7\u786e\u8ba4\u6587\u4ef6\u662f\u6709\u6548 PDF\u3002")
            return
        
        results = []
        for i, img in enumerate(images, 1):
            send_message(chat_id, f"\ud83d\udcc5 \u5206\u6790\u7b2c {i}/{len(images)} \u9875...")
            result = minimax_image(svc["prompt"], img)
            results.append(f"--- \u7b2c {i} \u9875 ---\n{result}")
        
        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        analysis = "\n\n".join(results)
        price_usd = 9.9
        
        msg = (
            f"\u2705 *\u5206\u6790\u5b8c\u6210\uff01*\n\n{analysis[:3500]}\n\n"
            f"---\n\ud83d\udcb0 \u4ef7\u683c: \u00a5{price_usd}\uff08\u7b2c\u4e00\u6b21\u514d\u8d39\u8bd5\u7528\uff09\n"
            f"\ud83d\udcde \u8054\u7cFB\u4ed8\u6b3e: @dbetter \u6216 Discord Reese#0001\n"
            f"\u2705 \u652f\u4ed8\u5b8d\u540e\u53ef\u5f97\u5230\u5b8c\u6574\u62a5\u544a"
        )
        send_message(chat_id, msg)
    
    elif service_type == "image":
        result = minimax_image(svc["prompt"], file_path)
        if result.startswith("["):
            send_message(chat_id, f"\u26a0\ufe0f \u5206\u6790\u5f02\u5e38: {result[:200]}\n\n\u8bf7\u8054\u7cFB @dbetter \u5904\u7406")
            return
        
        price_usd = 18
        msg = (
            f"\u2705 *\u5206\u6790\u5b8c\u6210\uff01*\n\n{result[:3500]}\n\n"
            f"---\n\ud83d\udcb0 \u4ef7\u683c: ${price_usd}\uff08\u7b2c\u4e00\u6b21\u514d\u8d39\u8bd5\u7528\uff09\n"
            f"\ud83d\udcde \u8054\u7cfb\u4ed8\u6b3e: @dbetter \u6216 Discord Reese#0001"
        )
        send_message(chat_id, msg)

def handle_update(update):
    state = load_state()
    try:
        # Callback query
        if "callback_query" in update:
            q = update["callback_query"]
            from_id = str(q["from"]["id"])
            data = q["data"]
            answer_callback(q["id"])
            
            user = state.get(from_id, {})
            step = user.get("step", "idle")
            
            if data == "order_pdf":
                user["step"] = "await_content"
                user["service"] = "pdf"
                send_message(q["from"]["id"],
                    f"\u2705 \u5df2\u9009\u62e9 *PDF\u5206\u6790* \u2014 \u00a59.9/\u6b21\n\n"
                    f"\u8bf7\u76f4\u63a5\u53d1\u9001PDF\u6587\u4ef6\uff0c\u6211\u4eec\u5c06\u81ea\u52a8\u5f00\u59cb\u5206\u6790~")
            elif data == "order_image":
                user["step"] = "await_content"
                user["service"] = "image"
                send_message(q["from"]["id"],
                    f"\u2705 \u5df2\u9009\u62e9 *\u5546\u54c1\u56fe\u63cf\u8ff0* \u2014 $18/\u5f20\n\n"
                    f"\u8bf7\u76f4\u63a5\u53d1\u9001\u5546\u54c1\u56fe\u7247\uff0c\u6211\u4eec\u5c06\u81ea\u52a8\u751f\u6210\u591a\u8bed\u8a00\u63cf\u8ff0~")
            
            state[from_id] = user
            save_state(state)
            return
        
        # Message
        msg = update.get("message", {})
        if not msg:
            return
        
        chat_id = msg["chat"]["id"]
        from_id = str(msg["from"]["id"])
        text = msg.get("text", "")
        user = state.get(from_id, {"step": "idle"})
        step = user.get("step", "idle")
        
        # Commands
        if text.startswith("/"):
            cmd = text.split()[0]
            if cmd == "/start":
                send_keyboard(chat_id, WELCOME, [
                    [f"{SERVICES['pdf']['emoji']} PDF\u5206\u6790", f"{SERVICES['image']['emoji']} \u5546\u54c1\u56fe\u63cf\u8ff0"]
                ])
                user = {"step": "idle"}
                state[from_id] = user
                save_state(state)
                return
        
        # Step: choose service (via keyboard or text)
        if step == "choose_service":
            if text in ("1", SERVICES["pdf"]["emoji"] + " PDF\u5206\u6790", "\u5f00\u59cbPDF") or "\u5206\u6790" in text:
                user["service"] = "pdf"
                user["step"] = "await_content"
            elif text in ("2", SERVICES["image"]["emoji"], "\u5f00\u59cb\u56fe\u7247", "\u56fe\u7247") or "\u5546\u54c1" in text:
                user["service"] = "image"
                user["step"] = "await_content"
            else:
                send_message(chat_id, "\u8bf7\u8f93\u51651\u62162\u9009\u62e9\u670d\u52a1~")
                return
        
        # File processing
        file_path = None
        file_ext = ""
        
        if "document" in msg:
            doc = msg["document"]
            mime = doc.get("mime_type", "")
            fname = doc.get("file_name", "")
            if mime == "application/pdf" or fname.lower().endswith(".pdf"):
                file_ext = ".pdf"
                file_path = download_file(doc["file_id"], ".pdf")
        
        elif "photo" in msg:
            photos = msg["photo"]
            best = max(photos, key=lambda p: p.get("width", 0))
            file_ext = ".jpg"
            file_path = download_file(best["file_id"], ".jpg")
        
        # If file received
        if file_path and os.path.exists(file_path):
            svc_type = user.get("service", None)
            if svc_type is None:
                # Try to auto-detect
                svc_type = "pdf" if file_ext == ".pdf" else "image"
                user["service"] = svc_type
            
            process_service(chat_id, svc_type, file_path, file_ext)
            
            # Reset state
            user["step"] = "idle"
            user["service"] = None
            state[from_id] = user
            save_state(state)
            
            # Cleanup
            try:
                os.unlink(file_path)
            except:
                pass
            return
        
        # Text-only message (no file) in await_content step
        if step == "await_content":
            if "\u53d6\u6d88" in text or "cancel" in text.lower():
                user["step"] = "idle"
                send_message(chat_id, "\u274c \u5df2\u53d6\u6d88\u3002\u53d1\u9001 /start \u91cd\u65b0\u5f00\u59cb~")
                state[from_id] = user
                save_state(state)
            elif text == "/start":
                send_keyboard(chat_id, WELCOME, [
                    [f"{SERVICES['pdf']['emoji']} PDF\u5206\u6790", f"{SERVICES['image']['emoji']} \u5546\u54c1\u56fe\u63cf\u8ff0"]
                ])
                user = {"step": "idle"}
                state[from_id] = user
                save_state(state)
            else:
                send_message(chat_id, "\ud83d\udcce \u8bf7\u53d1\u9001\u6587\u4ef6\uff08PDF\u6216\u56fe\u7247\uff09\uff0c\u800c\u975e\u6587\u5b57\u3002")
            return
        
        # Default: show welcome
        send_keyboard(chat_id, WELCOME, [
            [f"{SERVICES['pdf']['emoji']} PDF\u5206\u6790", f"{SERVICES['image']['emoji']} \u5546\u54c1\u56fe\u63cf\u8ff0"]
        ])
        user = {"step": "idle"}
        state[from_id] = user
        save_state(state)
        
    except Exception as e:
        log(f"Handle error: {e} | {update}")
        import traceback
        log(traceback.format_exc())

def poll(offset=0):
    """Long polling loop"""
    log("Bot polling started")
    while True:
        try:
            r = tg_request("getUpdates", params={"timeout": 25, "offset": offset})
            if not r or not r.get("ok"):
                import time; time.sleep(3)
                continue
            for upd in r.get("result", []):
                handle_update(upd)
                offset = upd["update_id"] + 1
        except Exception as e:
            log(f"Poll loop error: {e}")
            import time; time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "poll":
            poll()
        elif sys.argv[1] == "test":
            chat_id = sys.argv[2] if len(sys.argv) > 2 else None
            if not chat_id:
                print("Usage: bot.py test <chat_id>")
            else:
                send_message(chat_id, "\ud83d\udd0b Bot \u8fde\u63a5\u6d4b\u8bd5\u6210\u529f\uff01")
    else:
        print("Usage: python3 ai_services_bot.py poll")
        print("       python3 ai_services_bot.py test <chat_id>")
