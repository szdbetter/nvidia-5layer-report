import json, urllib.request, websocket, threading, time, sys

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list").read())
tab = next((t for t in tabs if "goofish" in t.get("url", "")), None)

if not tab:
    urllib.request.urlopen("http://127.0.0.1:9222/json/new?https://www.goofish.com/im")
    time.sleep(8)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list").read())
    tab = next((t for t in tabs if "goofish" in t.get("url", "")), None)

if not tab:
    print("ERROR: no goofish tab")
    sys.exit(1)

print("Tab:", tab.get("url", "")[:60])
ws_url = tab["webSocketDebuggerUrl"]
res = {}
done = threading.Event()

def on_msg(ws, m):
    d = json.loads(m)
    if d.get("id") == 1:
        res["r"] = d
        done.set()
        ws.close()

def on_open(ws):
    js = """(async() => {
  try {
    const cookies = document.cookie;
    const loggedIn = cookies.includes('unb=') || cookies.includes('tracknick=');
    if (!loggedIn) return JSON.stringify({error:'not_logged_in', cookies: cookies.substring(0,200)});
    
    // Try mtop API through goofish page context
    const url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.im.chat.getconversationlist/1.0/?jsv=2.7.2&appKey=12574478&timestamp=' + Date.now() + '&v=1.0&type=json';
    const r = await fetch(url, {
      credentials: 'include',
      headers: {
        'referer': 'https://www.goofish.com/im',
        'content-type': 'application/json'
      }
    });
    const text = await r.text();
    return text.substring(0, 1000);
  } catch(e) {
    return 'err: ' + e.toString();
  }
})()"""
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))

wsapp = websocket.WebSocketApp(ws_url, on_message=on_msg, on_open=on_open)
t = threading.Thread(target=wsapp.run_forever, kwargs={"ping_timeout": 10})
t.daemon = True
t.start()
done.wait(30)
print(json.dumps(res.get("r", {}), ensure_ascii=False)[:3000])
