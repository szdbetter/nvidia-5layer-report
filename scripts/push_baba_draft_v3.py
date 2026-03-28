#!/usr/bin/env python3
"""
BABA 研报公众号草稿推送脚本 v3
1. 上传10张白板图片到微信素材库
2. 在文章正文关键节点插入图片
3. 推送到草稿箱
"""
import os, json, time, requests
from pathlib import Path

# ── 配置 ──
APPID  = os.environ.get("WX_GZH_APPID", "")
SECRET = os.environ.get("WX_GZH_APPSECRET", "")
IMG_DIR = Path("/root/.openclaw/workspace/ppt_outputs/baba_whiteboard_v3")
ARTICLE_MD = Path("/root/.openclaw/workspace/reports/wechat_article_BABA_2026-03-18.md")

# 图片列表（按插入位置排序）
IMAGES = [
    ("01_cover.jpg",      "封面：研报总览"),
    ("02_dashboard.jpg",  "投资决策驾驶舱"),
    ("03_scorecard.jpg",  "14维度评分卡"),
    ("04_logic.jpg",      "核心投资逻辑"),
    ("05_segments.jpg",   "业务板块拆解"),
    ("06_ai.jpg",         "AI战略·Qwen生态"),
    ("07_competition.jpg","竞争格局矩阵"),
    ("08_risks.jpg",      "风险矩阵"),
    ("09_strategy.jpg",   "操作策略"),
    ("10_closing.jpg",    "结语"),
]

def get_token():
    r = requests.get(
        "https://api.weixin.qq.com/cgi-bin/token",
        params={"grant_type": "client_credential", "appid": APPID, "secret": SECRET}
    )
    data = r.json()
    if "access_token" not in data:
        raise Exception(f"获取token失败: {data}")
    return data["access_token"]

def upload_image(token, img_path, upload_perm=False):
    """
    upload_perm=False: 仅用 uploadimg，返回 (None, content_url)
    upload_perm=True:  先 add_material 拿 media_id，再 uploadimg 拿 content_url
    """
    # 文章内嵌图片 URL（必须用 uploadimg 接口）
    with open(img_path, "rb") as f:
        r = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}",
            files={"media": (img_path.name, f, "image/jpeg")}
        )
    img_url = r.json().get("url", "").replace("http://", "https://")

    media_id = ""
    if upload_perm:
        with open(img_path, "rb") as f:
            r2 = requests.post(
                f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
                files={"media": (img_path.name, f, "image/jpeg")}
            )
        media_id = r2.json().get("media_id", "")

    print(f"  ✅ {img_path.name} → url={img_url[:50]}...")
    return media_id, img_url

def md_to_html(md_text, img_media_ids):  # img_media_ids here are actually full URLs
    """
    简单的 Markdown → HTML 转换
    在关键段落后插入图片（按顺序分配）
    """
    lines = md_text.split("\n")
    html_parts = []
    img_idx = 0
    # 插入封面图作为第一张
    def img_tag(url):
        return f'<p><img data-src="{url}" src="{url}" alt="" style="width:100%;"/></p>'

    if img_media_ids:
        html_parts.append(img_tag(img_media_ids[0]))
        img_idx = 1

    # 触发图片插入的段落关键词（按文章顺序）
    insert_triggers = [
        "2B基因，是别人学不走的东西",
        "悟空，是我见过最接近",
        "为什么闭环是最难的那个字",
        "一个有意思的估值对比",
        "我真正想说的是什么",
    ]
    trigger_idx = 0

    for line in lines:
        stripped = line.strip()

        # 标题
        if stripped.startswith("# "):
            html_parts.append(f'<h1>{stripped[2:]}</h1>')
        elif stripped.startswith("## "):
            title = stripped[3:]
            html_parts.append(f'<h2>{title}</h2>')
            # 插图触发：每个H2后插一张（从第2张开始）
            if img_idx < len(img_media_ids):
                html_parts.append(img_tag(img_media_ids[img_idx]))
                img_idx += 1
        elif stripped.startswith("---"):
            html_parts.append('<hr/>')
        elif stripped == "":
            html_parts.append("<br/>")
        else:
            import re
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            html_parts.append(f'<p>{text}</p>')

    # 末尾插入结语图
    if img_idx < len(img_media_ids):
        html_parts.append(img_tag(img_media_ids[img_idx]))

    return "\n".join(html_parts)

def push_draft(token, title, content_html, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = {
        "articles": [{
            "title": title,
            "author": "Reese · OpenClaw AI Research",
            "digest": "阿里研报·7.16分·目标$205",
            "content": content_html,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]
    }
    r = requests.post(url, json=payload)
    return r.json()

def main():
    if not APPID or not SECRET:
        raise Exception("WECHAT_APPID / WECHAT_SECRET 未配置")

    print("🔑 获取 access_token...")
    token = get_token()
    print(f"  ✅ token 获取成功")

    print("\n📤 上传图片素材...")
    img_urls  = []
    thumb_media_id = ""
    for i, (fname, desc) in enumerate(IMAGES):
        path = IMG_DIR / fname
        if not path.exists():
            print(f"  ⚠️  缺少: {fname}")
            continue
        mid, url = upload_image(token, path, upload_perm=False)
        img_urls.append(url)
        if i == 0:
            # 封面：先用 uploadimg url，再单独上传 add_material
            with open(path, "rb") as f:
                rc = requests.post(
                    f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
                    files={"media": (path.name, f, "image/jpeg")}
                )
            rc_data = rc.json()
            if "media_id" in rc_data:
                thumb_media_id = rc_data["media_id"]
                print(f"  📌 封面 media_id: {thumb_media_id[:20]}...")
            else:
                print(f"  ⚠️ 封面 add_material 失败: {rc_data}")
        time.sleep(0.5)

    print(f"\n  共上传 {len(img_urls)} 张图片")

    print("\n📝 生成文章 HTML...")
    md_text = ARTICLE_MD.read_text(encoding="utf-8")
    html = md_to_html(md_text, img_urls)

    print("\n🚀 推送草稿箱...")
    result = push_draft(
        token,
        title='阿里深度研报：AI闭环，7.16分，目标$205',
        content_html=html,
        thumb_media_id=thumb_media_id,
    )

    if "media_id" in result:
        print(f"\n✅ 草稿推送成功！media_id: {result['media_id']}")
    else:
        print(f"\n❌ 推送失败: {result}")

    return result

if __name__ == "__main__":
    main()
