#!/usr/bin/env python3
"""
Telegram Order Checker - 赚钱引擎
检查 Telegram bot 收件箱，有新消息/文件则处理
"""
import os, sys, json, tempfile, subprocess, shutil
import urllib.request, urllib.parse

BOT_TOKEN = "8055188738:AAEUcRH1KbuUSSKH4yxfS0x9gv4GbOuU6e4"
STATE_FILE = "/tmp/tg_order_state.json"
LOG_FILE = "/tmp/tg_order.log"

def log(msg):
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def tg_get(url, params=None):
    import urllib.request, urllib.parse
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"TG get error: {e}")
        return None

def tg_post(url, data):
    import urllib.request, urllib.parse
    enc = urllib.parse.urlencode(data).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=enc), timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"TG post error: {e}")
        return None

SERVICES = {
    "pdf": {
        "name": "PDF智能分析",
        "emoji": "📄",
        "price": "¥9.9",
        "prompt": (
            "You are a professional document analysis assistant. Analyze this document page carefully.\n"
            "Extract and return: 1) Document type/title, 2) Key findings & data points, "
            "3) Important numbers/dates, 4) Executive summary (3-5 sentences). "
            "Respond in Chinese if content appears Chinese, otherwise English. Format as structured markdown."
        )
    },
    "image": {
        "name": "商品图多语言描述",
        "emoji": "🖼️",
        "price": "$18",
        "prompt": (
            "You are an expert e-commerce product analyst. Analyze this product image. "
            "Generate in structured markdown: 1) Product category 2) Detailed description "
            "3) Five-point listing copy 4) SEO keywords 5) Platform tags (Amazon/Shopee/Taobao) "
            "6) Descriptions in English, Japanese, Korean, Thai."
        )
    }
}

def send_message(chat_id, text):
    return tg_post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", {
        "chat_id": chat_id, "text": str(text)[:4096], "parse_mode": "Markdown"
    })

def download_file(file_id, ext):
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.close()
    try:
        r = tg_get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", {"file_id": file_id})
        if not r or not r.get("ok"):
            return None
        file_path = r["result"]["file_path"]
        dl_url = f"https://api.telegram.org/bot{BOT_TOKEN}/file/{file_path}"
        with urllib.request.urlopen(dl_url, timeout=30) as resp:
            with open(tmp.name, "wb") as f:
                shutil.copyfileobj(resp, f)
        return tmp.name
    except Exception as e:
        log(f"Download error: {e}")
        try:
            os.unlink(tmp.name)
        except:
            pass
        return None

def pdf_to_images(pdf_path, max_pages=3):
    try:
        import fitz
        images = []
        tmpdir = tempfile.mkdtemp()
        doc = fitz.open(pdf_path)
        for i in range(min(max_pages, len(doc))):
            pix = doc[i].get_pixmap(dpi=150)
            out = f"{tmpdir}/p{i+1}.jpg"
            pix.save(out)
            images.append(out)
        doc.close()
        return images, tmpdir
    except Exception as e:
        log(f"PDF error: {e}")
        return [], ""

def minimax_image(prompt, image_path):
    cmd = [
        "mcporter", "call", "MiniMax.understand_image",
        f"prompt={prompt}",
        f"image_source={image_path}",
        "--output", "json"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            content = data.get("content", [])
            if isinstance(content, list) and content:
                return content[0].get("text", "")
            return str(data)[:300]
        return f"[err] {r.stderr[:100]}"
    except Exception as e:
        return f"[exc] {e}"

def process_file(chat_id, file_path, file_ext, service_hint=None):
    svc_type = service_hint or ("pdf" if file_ext == ".pdf" else "image")
    svc = SERVICES[svc_type]
    
    send_message(chat_id, f"⏳ 收到{svc['emoji']}{svc['name']}请求，分析中（15-60秒）...")
    
    if svc_type == "pdf":
        images, tmpdir = pdf_to_images(file_path, 3)
        if not images:
            send_message(chat_id, "⚠️ PDF解析失败，请确认文件有效。")
            return
        results = []
        for i, img in enumerate(images, 1):
            send_message(chat_id, f"📄 分析第{i}/{len(images)}页...")
            results.append(f"--- 第{i}页 ---\n{minimax_image(svc['prompt'], img)}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        analysis = "\n\n".join(results)
    else:
        analysis = minimax_image(svc['prompt'], file_path)
        if analysis.startswith("[err]") or analysis.startswith("[exc]"):
            send_message(chat_id, f"⚠️ 分析异常: {analysis[:200]}\n\n请联系 @dbetter 处理")
            return
    
    msg = (
        f"✅ *分析完成！*\n\n{analysis[:3500]}\n\n"
        f"---\n💰 价格: {svc['price']}（首次免费试用）\n"
        f"💳 付款: @dbetter 或 Discord Reese#0001\n"
        f"📩 问题联系: @dbetter"
    )
    send_message(chat_id, msg)

def welcome(chat_id):
    text = (
        "👋 *欢迎来到AI服务下单！*\n\n"
        "📄 *PDF智能分析* — ¥9.9/文档\n"
        "   PDF/报告 → 关键信息+摘要+数据\n\n"
        "🖼️ *商品图多语言描述* — $18/张\n"
        "   产品图 → 英日韩泰五点描述+SEO\n\n"
        "直接发送PDF或图片即可自动分析~\n"
        "首次试用免费！\n\n"
        "有问题联系: @dbetter"
    )
    send_message(chat_id, text)

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

def main():
    log("=== Telegram order checker started ===")
    state = load_state()
    
    # Get updates
    offset = state.get("offset", 0)
    r = tg_get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
               {"timeout": 0, "limit": 10, "offset": offset})
    
    if not r or not r.get("ok"):
        log(f"getUpdates failed: {r}")
        return
    
    updates = r.get("result", [])
    if not updates:
        log("No new updates")
        return
    
    log(f"Got {len(updates)} updates")
    
    for upd in updates:
        upd_id = upd.get("update_id", 0)
        
        # Message
        msg = upd.get("message", {})
        if not msg:
            continue
        
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        from_id = str(msg.get("from", {}).get("id", ""))
        
        log(f"Message from {from_id} in chat {chat_id}: {text[:50]}")
        
        # File handling
        file_path = None
        file_ext = ""
        service_hint = state.get(f"pending_{from_id}")
        
        if "document" in msg:
            doc = msg["document"]
            if doc.get("mime_type", "").startswith("application/pdf") or doc.get("file_name", "").lower().endswith(".pdf"):
                file_ext = ".pdf"
                file_path = download_file(doc["file_id"], ".pdf")
        elif "photo" in msg:
            photos = msg["photo"]
            best = max(photos, key=lambda p: p.get("width", 0))
            file_ext = ".jpg"
            file_path = download_file(best["file_id"], ".jpg")
        
        if file_path and os.path.exists(file_path):
            process_file(chat_id, file_path, file_ext, service_hint)
            try:
                os.unlink(file_path)
            except:
                pass
            # Clear pending
            for k in list(state.keys()):
                if k.startswith("pending_"):
                    del state[k]
        
        elif text in ("/start", "/help", "start", "help"):
            welcome(chat_id)
        
        elif text == "/order":
            send_message(chat_id, "📦 请直接发送PDF文件或产品图片~\n\n📄 PDF分析 | 🖼️ 图片描述\n\n发送即开始自动处理，首次试用免费！")
        
        elif text:
            # Auto-detect service from text
            if any(k in text.lower() for k in ["pdf", "文档", "报告", "分析"]):
                state[f"pending_{from_id}"] = "pdf"
                send_message(chat_id, "📄 已选择PDF分析，请发送PDF文件~")
            elif any(k in text.lower() for k in ["图片", "产品", "电商", "描述"]):
                state[f"pending_{from_id}"] = "image"
                send_message(chat_id, "🖼️ 已选择图片描述，请发送产品图片~")
            else:
                welcome(chat_id)
        
        state["offset"] = upd_id + 1
    
    save_state(state)
    log("=== Done ===")

if __name__ == "__main__":
    main()
