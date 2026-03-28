#!/usr/bin/env python3
"""CDP script: inject cookies + fetch goofish IM messages via Chrome 9222"""
import json, time, sys, urllib.request

try:
    import websocket
except ImportError:
    print(json.dumps({"error":"websocket-client missing"})); sys.exit(1)

COOKIES = [
    ("tracknick","dbetter",".goofish.com"),
    ("unb","11466972",".goofish.com"),
    ("t","7449052816476968a9aea97d8fb4c31d",".goofish.com"),
    ("_m_h5_tk","959462a799d00a260c7f5d8d61b0eac5_1773739983559",".goofish.com"),
    ("cna","Nlc+IgD48FsCAUUFFP/WinmN",".goofish.com"),
    ("sgcookie","E100ubHjxNmX9p0di85tbsIzr0%2Fv7zqdqnGfQxZTu4U%2FDjVGoV9UsnPmtb7QbDn6sfb4YLxPQT%2BEwJjMcpYkPUsKCgb52tbKhB%2B%2F2vK7J1oYG%2Fw%3D",".goofish.com"),
    ("unb","11466972",".taobao.com"),
    ("t","7449052816476968a9aea97d8fb4c31d",".taobao.com"),
    ("_m_h5_tk","959462a799d00a260c7f5d8d61b0eac5_1773739983559",".taobao.com"),
    ("cna","Nlc+IgD48FsCAUUFFP/WinmN",".taobao.com"),
    ("sgcookie","E100ubHjxNmX9p0di85tbsIzr0%2Fv7zqdqnGfQxZTu4U%2FDjVGoV9UsnPmtb7QbDn6sfb4YLxPQT%2BEwJjMcpYkPUsKCgb52tbKhB%2B%2F2vK7J1oYG%2Fw%3D",".taobao.com"),
]

_id=[0]
def cdp(ws, method, params=None, timeout=10):
    _id[0]+=1; mid=_id[0]
    msg={"id":mid,"method":method}
    if params: msg["params"]=params
    ws.send(json.dumps(msg))
    dl=time.time()+timeout
    while time.time()<dl:
        ws.settimeout(max(0.5,dl-time.time()))
        try:
            r=json.loads(ws.recv())
            if r.get("id")==mid: return r
        except: break
    return None

def drain(ws, secs=1):
    """Drain events for secs"""
    dl=time.time()+secs
    while time.time()<dl:
        ws.settimeout(max(0.1,dl-time.time()))
        try: ws.recv()
        except: break

def main():
    out={"steps":[]}
    # 1. Get browser WS
    ver=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/version",timeout=5).read())
    bws=ver["webSocketDebuggerUrl"]
    out["steps"].append("got_browser_ws")

    # 2. Get target list
    targets=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list",timeout=5).read())
    out["steps"].append(f"targets={len(targets)}")
    out["target_urls"]=[t.get("url","")[:120] for t in targets if t.get("type")=="page"]

    # 3. Find or create a tab for goofish
    page_target=None
    for t in targets:
        if t.get("type")=="page" and "goofish" in t.get("url",""):
            page_target=t; break
    if not page_target:
        for t in targets:
            if t.get("type")=="page":
                page_target=t; break

    if not page_target:
        nt=json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/new?about:blank",timeout=5).read())
        page_target=nt
        out["steps"].append("created_tab")

    page_ws_url=page_target["webSocketDebuggerUrl"]
    out["steps"].append(f"using_tab={page_target.get('url','')[:80]}")

    # 4. Connect to page target
    ws=websocket.create_connection(page_ws_url, timeout=20, suppress_origin=True)
    out["steps"].append("ws_connected")

    cdp(ws,"Network.enable")
    cdp(ws,"Page.enable")
    drain(ws,0.5)

    # 5. Inject cookies
    ok=0
    for name,val,domain in COOKIES:
        r=cdp(ws,"Network.setCookie",{
            "name":name,"value":val,"domain":domain,"path":"/",
            "httpOnly":False,"secure":True
        },timeout=5)
        if r and r.get("result",{}).get("success"): ok+=1
    out["steps"].append(f"cookies_ok={ok}/{len(COOKIES)}")

    # 6. Navigate to goofish.com/im
    nav=cdp(ws,"Page.navigate",{"url":"https://www.goofish.com/im"},timeout=15)
    nav_res=nav.get("result",{}) if nav else {}
    out["steps"].append(f"nav_frameId={nav_res.get('frameId','?')}")

    # 7. Wait for load
    time.sleep(8)
    drain(ws,1)

    # 8. Re-inject cookies after navigation (some get cleared)
    ok2=0
    for name,val,domain in COOKIES:
        r=cdp(ws,"Network.setCookie",{
            "name":name,"value":val,"domain":domain,"path":"/",
            "httpOnly":False,"secure":True
        },timeout=3)
        if r and r.get("result",{}).get("success"): ok2+=1
    out["steps"].append(f"cookies_reinject={ok2}/{len(COOKIES)}")

    # 9. Check current URL
    r=cdp(ws,"Runtime.evaluate",{"expression":"window.location.href","returnByValue":True},timeout=5)
    cur_url=r.get("result",{}).get("result",{}).get("value","") if r else ""
    out["current_url"]=cur_url

    # 10. Check page state
    page_check='''(function(){
        var o={title:document.title, bodyLen:(document.body?document.body.innerText.length:0)};
        o.hasLogin=!!(document.querySelector('[class*="login"],[class*="Login"],#login')||document.title.indexOf("登录")>-1);
        o.snippet=(document.body?document.body.innerText.substring(0,1500):"");
        return JSON.stringify(o);
    })()'''
    r=cdp(ws,"Runtime.evaluate",{"expression":page_check,"returnByValue":True},timeout=8)
    if r:
        v=r.get("result",{}).get("result",{}).get("value","")
        try: out["page_state"]=json.loads(v)
        except: out["page_state_raw"]=str(v)[:1500]

    # 11. Attempt fetch to IM API from page context
    fetch_js='''(async function(){
        try{
            var ts=Date.now();
            // Try goofish web IM conversation list
            var apis=[
                "https://h5api.m.goofish.com/h5/mtop.taobao.idle.im.session.page.list/1.0/",
                "https://h5api.m.goofish.com/h5/mtop.taobao.idle.im.conversation.list/1.0/",
                "https://g.alicdn.com/??",
            ];
            var results=[];
            for(var i=0;i<2;i++){
                try{
                    var u=apis[i]+"?jsv=2.7.4&appKey=12574478&t="+ts+"&type=originaljson&dataType=json&timeout=10000&data="+encodeURIComponent(JSON.stringify({pageSize:20}));
                    var r=await fetch(u,{credentials:"include",headers:{"Accept":"application/json"}});
                    var t2=await r.text();
                    results.push({api:apis[i].split("/").pop(),status:r.status,body:t2.substring(0,2000)});
                }catch(e){results.push({api:apis[i].split("/").pop(),error:e.message});}
            }
            return JSON.stringify(results);
        }catch(e){return JSON.stringify({error:e.message});}
    })()'''
    r=cdp(ws,"Runtime.evaluate",{"expression":fetch_js,"awaitPromise":True,"returnByValue":True},timeout=25)
    if r:
        v=r.get("result",{}).get("result",{}).get("value","")
        try: out["api_results"]=json.loads(v)
        except: out["api_results_raw"]=str(v)[:2000]

    # 12. Also try reading cookies back to verify injection
    cookie_check='''document.cookie'''
    r=cdp(ws,"Runtime.evaluate",{"expression":cookie_check,"returnByValue":True},timeout=5)
    if r:
        out["doc_cookies"]=r.get("result",{}).get("result",{}).get("value","")[:500]

    # 13. Get all cookies via CDP
    r=cdp(ws,"Network.getCookies",{"urls":["https://www.goofish.com","https://h5api.m.goofish.com"]},timeout=5)
    if r:
        cookies_list=r.get("result",{}).get("cookies",[])
        out["cdp_cookies"]=[{"name":c["name"],"domain":c["domain"]} for c in cookies_list[:30]]

    ws.close()
    out["status"]="done"
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
