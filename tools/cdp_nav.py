#!/usr/bin/env python3
"""CDP WebSocket navigator - connect to Chrome on Fiona via node proxy"""
import sys, json, urllib.request

CHROME_HOST = "127.0.0.1"
CHROME_PORT = 9222

def get_tabs():
    r = urllib.request.urlopen(f"http://{CHROME_HOST}:{CHROME_PORT}/json/list")
    return json.loads(r.read())

def navigate(tab_id, url):
    """Use CDP HTTP endpoint to navigate"""
    # Can't use HTTP for CDP commands, need WebSocket
    # But we can create a new tab with the URL
    r = urllib.request.urlopen(f"http://{CHROME_HOST}:{CHROME_PORT}/json/new?{url}")
    result = json.loads(r.read())
    return result

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.goofish.com/im"
    print(json.dumps(navigate(None, url), indent=2))
