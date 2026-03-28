
import sys, urllib.request, io, json
url = sys.argv[1]
try:
    from PIL import Image
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = urllib.request.urlopen(req, timeout=10).read()
    img = Image.open(io.BytesIO(data)).convert('RGB')
    w, h = img.size
    region = img.crop((w*2//3, h//4, w, h*3//4))
    pixels = list(region.getdata())
    grey = sum(1 for r,g,b in pixels if abs(r-g)<25 and abs(g-b)<25 and 80<r<220)
    ratio = grey / len(pixels)
    print(json.dumps({"grey_ratio": round(ratio, 3), "claimed": ratio > 0.15}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
