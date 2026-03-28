#!/usr/bin/env python3
import os, requests, json, time
from pathlib import Path

API_KEY = "STABILITY_API_KEY_REDACTED"
SLIDES_DIR = Path("/tmp/slides_constructivism")
IMG_DIR = SLIDES_DIR / "images"
IMG_DIR.mkdir(exist_ok=True)

SLIDE_PROMPTS = [
    "Soviet constructivism propaganda poster style. Dramatic diagonal red geometric shapes. Multiple silhouetted worker figures marching forward with determination, one figure elevated as a leader. Bold red #CC0000 and deep black. No text. High contrast.",
    "Soviet constructivism style. A large glowing brain floating above, connected by red beams to tiny human figures doing paperwork below. Boss figure sitting relaxed while workers run around. Geometric shapes background. Red and black only. No text.",
    "Soviet constructivism style. Split composition: left side shows glowing red brain with circuit patterns, right side shows powerful mechanical robot arms extending outward. Red diagonal beam connecting both halves. Black background. No text.",
    "Soviet constructivism style. Bold diagonal road splitting into two paths. Left: small figures at a computer screen. Right: commanding figure directing an army of robots. Giant red geometric shapes at the fork. Black background. No text.",
    "Soviet constructivism style. 6 human command figures at top directing an army of 30 robotic worker silhouettes in geometric formation below. Propaganda poster feel. Bold red geometric shapes overhead. No text.",
    "Soviet constructivism style. Single heroic human silhouette standing tall, surrounded by swirling code fragments and multiple robotic mechanical hands building things. Giant red star or rising sun geometric shape in background. No text.",
    "Soviet constructivism style. Government building silhouette with massive red star burst at center. Multiple bold red upward arrows from below. Strong geometric composition. Black background. No text.",
    "Soviet constructivism style. Six bold red squares in grid, each with a simple geometric tech icon. Red connecting lines forming ecosystem web. Central command figure above them all. Bold black background. No text.",
    "Soviet constructivism style. Central AI robot figure with multiple red mechanical arms extending radially, each arm performing different tasks: document writing, data analysis, customer service, coding. Dynamic radial burst composition. No text.",
    "Soviet constructivism style. Powerful robot figure stopped at an invisible barrier made of geometric shapes representing human values. A human hand reaching down in control from above. Red warning geometric shapes around barrier. No text.",
    "Soviet constructivism style. Three massive red geometric steps ascending diagonally (numbered 1-2-3 as geometric forms). Human silhouette climbing upward with determination. Bright red diagonal beams showing momentum. No text.",
    "Soviet constructivism style. Epic split composition: left side shows empowered human commanding red robot army with raised fist, right side shows diminished figure trapped as a gear in a machine. Giant red sun/star rising center. Dramatic finale. No text.",
]

def generate_image(prompt, output_path, slide_num):
    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    payload = {"model": "doubao-seedream-3-0-t2i-250415", "prompt": prompt, "size": "1280x720", "n": 1}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            img_url = resp.json()["data"][0]["url"]
            img_resp = requests.get(img_url, timeout=30)
            with open(output_path, 'wb') as f:
                f.write(img_resp.content)
            print(f"DONE slide-{slide_num:02d}: {output_path}")
            return True
        except Exception as e:
            print(f"FAIL slide-{slide_num:02d} attempt {attempt+1}: {e}")
            time.sleep(3)
    return False

for i, prompt in enumerate(SLIDE_PROMPTS, 1):
    img_path = IMG_DIR / f"img-{i:02d}.jpg"
    if img_path.exists():
        print(f"SKIP slide-{i:02d} (exists)")
        continue
    generate_image(prompt, img_path, i)
    time.sleep(1)

print("ALL_DONE")
