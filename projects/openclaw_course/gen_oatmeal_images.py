import requests, time
from pathlib import Path

API_KEY = "95a59971-9ee5-4705-9f9f-111a1b667ff3"
IMG_DIR = Path("/tmp/slides_oatmeal/images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

BASE = "VISUAL STYLE: The Oatmeal webcomic by Matthew Inman — expressive hand-drawn characters with EXTREMELY exaggerated emotions, thick bold outlines, flat colors. CANVAS: 16:9. COLOR PALETTE: Light gray-white #F8F8F8 background, bright orange #FF6B35 accents, deep gray #333333 linework, red #FF2442 highlights. CHARACTERS: Large expressive heads, tiny bodies, dramatic facial expressions. MOOD: Humorous, informative, energetic. Web comic infographic style. "

SCENES = [
    "Character with HUGE excited eyes looking at a giant speech bubble. Expression: pure amazement. Calendar with 2026. Hair stands on end with excitement. Energetic web comic opener.",
    "Absurdist comic: HUGE brain in throne giving advice, tiny character runs around doing ALL work. Brain looks smug. Character exhausted but polite. Classic Oatmeal frustration humor.",
    "Before/After: LEFT sad brain floating alone no hands. RIGHT happy brain PLUS robot hands. Character has EUREKA lightbulb moment expression. Big dramatic transformation.",
    "Giant fork in road. LEFT: character at computer exhausted. RIGHT: character on hammock with robot army working. Character at fork with dramatic decision face.",
    "EXTREME comparison: 6 tiny commanders dramatically gesturing. Below: 30 cheerful robots in organized rows. Numbers 6 and 30 shown BIG with Oatmeal expressions.",
    "ONE triumphant character at desk arms raised. 4 robot helpers around them each with task labels. Championship winner expression. Solo but not alone energy.",
    "Character reads official scroll with HUGE surprised eyes. 70% in giant numbers on scroll. Character jaw drops dramatically. Company logo boxes float around. Classic Oatmeal shock.",
    "6 different tech platform characters each with personality. All connected by lines in same race. Competitive friendly chaos. Oatmeal competitive energy.",
    "Super-AI with 4 arms doing 4 things at once: typing, analyzing, talking, coding. Looks DELIGHTED. Human nearby watches with impressed expression taking notes.",
    "Philosophical dialogue: Human and AI robot face each other calmly. Robot responds with wisdom AND admits limits honestly. Both look respected. Mature Oatmeal energy.",
    "3 BIG numbered stepping stones. Character confidently runs UP steps. Step 1 small obstacle. Step 2 medium progress. Step 3 VICTORY pose at top.",
    "Epic final panel: Two future thought bubbles. Future A: Character plus robot team, success, big smile. Future B: Robot army passing exhausted solo character. Character choosing A with determined face. Sunrise."
]

for i, scene in enumerate(SCENES, 1):
    path = IMG_DIR / f"img-{i:02d}.jpg"
    if path.exists():
        print(f"SKIP {i}")
        continue
    try:
        resp = requests.post(
            "https://ark.cn-beijing.volces.com/api/v3/images/generations",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "doubao-seedream-3-0-t2i-250415", "prompt": BASE + scene, "size": "1280x720", "n": 1},
            timeout=60
        )
        data = resp.json()
        img_url = data["data"][0]["url"]
        path.write_bytes(requests.get(img_url, timeout=30).content)
        print(f"DONE {i}/12")
    except Exception as e:
        print(f"FAIL {i}: {e}")
    time.sleep(1)
print("ALL DONE")
