#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv
from jinja2 import Template

ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = SKILL_DIR / 'templates' / 'wechat_article.html'
DEFAULT_REGISTRY = ROOT / 'projects' / 'digital-twin-advisor' / 'CONTENT_REGISTRY.md'


def load_env():
    load_dotenv(Path('/root/.openclaw/.env'))
    load_dotenv(ROOT / '.env', override=False)
    load_dotenv(SKILL_DIR / 'examples' / '.env.example', override=False)


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def load_json(path: Optional[Path], default):
    if not path:
        return default
    return json.loads(read_text(path))


def slugify(text: str) -> str:
    s = re.sub(r'[^\w\u4e00-\u9fff-]+', '-', text.strip(), flags=re.UNICODE)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'article'


def inline_format(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    return text


def inject_images_into_markdown(md_text: str, body_images: List[Dict[str, str]]) -> str:
    lines = md_text.splitlines()
    out = []
    image_map = {item.get('before_heading', '').strip(): item.get('src', '').strip() for item in body_images if item.get('before_heading') and item.get('src')}
    for line in lines:
        stripped = line.strip()
        h2 = re.match(r'^##\s+(.+)$', stripped)
        if h2:
            heading = h2.group(1).strip()
            image_src = image_map.get(heading)
            if image_src:
                out.append(f'![]({image_src})')
                out.append('')
        out.append(line)
    return '\n'.join(out)


def render_via_ziliu(md_text: str) -> str:
    ziliu_key = env_first('ZILIU_API_KEY')
    if not ziliu_key:
        raise RuntimeError('缺少 ZILIU_API_KEY。')
    resp = requests.post(
        'https://ziliu.online/api/convert',
        json={'content': md_text, 'style': 'tech', 'platform': 'wechat'},
        headers={'Authorization': f'Bearer {ziliu_key}'},
        timeout=60,
    )
    data = resp.json()
    html_out = ((data.get('data') or {}).get('html')) if isinstance(data, dict) else None
    if resp.status_code != 200 or not html_out:
        raise RuntimeError(f'字流排版失败: {data}')
    return html_out


def render_markdown(md_text: str, body_images: List[Dict[str, str]]) -> Dict[str, Any]:
    lines = md_text.splitlines()
    body_parts: List[str] = []
    title = None
    in_ul = False
    in_ol = False
    in_blockquote = False
    in_code = False
    code_lines: List[str] = []
    used_images = []

    image_map = {item.get('before_heading', '').strip(): item.get('src', '').strip() for item in body_images if item.get('before_heading') and item.get('src')}

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            body_parts.append('</ul>')
            in_ul = False
        if in_ol:
            body_parts.append('</ol>')
            in_ol = False

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            body_parts.append('</blockquote>')
            in_blockquote = False

    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()

        if stripped.startswith('```'):
            close_lists()
            close_blockquote()
            if in_code:
                body_parts.append('<pre><code>{}</code></pre>'.format(html.escape('\n'.join(code_lines))))
                in_code = False
                code_lines = []
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if stripped == '':
            close_lists()
            close_blockquote()
            continue

        if stripped == '---':
            close_lists()
            close_blockquote()
            body_parts.append('<hr/>')
            continue

        h1 = re.match(r'^#\s+(.+)$', stripped)
        h2 = re.match(r'^##\s+(.+)$', stripped)
        h3 = re.match(r'^###\s+(.+)$', stripped)
        ul = re.match(r'^[-*]\s+(.+)$', stripped)
        ol = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        quote = re.match(r'^>\s?(.+)$', stripped)

        if h1:
            close_lists(); close_blockquote()
            title = h1.group(1).strip()
            continue

        if h2:
            close_lists(); close_blockquote()
            heading = h2.group(1).strip()
            image_src = image_map.get(heading)
            if image_src:
                body_parts.append(f'<p><img src="{html.escape(image_src)}" alt="section-image"/></p>')
                used_images.append({"before_heading": heading, "src": image_src})
            body_parts.append(f'<h2>{inline_format(heading)}</h2>')
            continue

        if h3:
            close_lists(); close_blockquote()
            body_parts.append(f'<h3>{inline_format(h3.group(1).strip())}</h3>')
            continue

        if ul:
            close_blockquote()
            if not in_ul:
                close_lists()
                body_parts.append('<ul>')
                in_ul = True
            body_parts.append(f'<li>{inline_format(ul.group(1).strip())}</li>')
            continue

        if ol:
            close_blockquote()
            if not in_ol:
                close_lists()
                body_parts.append('<ol>')
                in_ol = True
            body_parts.append(f'<li>{inline_format(ol.group(2).strip())}</li>')
            continue

        if quote:
            close_lists()
            if not in_blockquote:
                body_parts.append('<blockquote>')
                in_blockquote = True
            body_parts.append(f'<p>{inline_format(quote.group(1).strip())}</p>')
            continue

        close_lists(); close_blockquote()
        body_parts.append(f'<p>{inline_format(stripped)}</p>')

    close_lists(); close_blockquote()
    if in_code:
        body_parts.append('<pre><code>{}</code></pre>'.format(html.escape('\n'.join(code_lines))))

    return {
        'title': title or '未命名文章',
        'body_html': '\n'.join(body_parts),
        'used_images': used_images,
    }


def wrap_article(title: str, author: str, body_html: str) -> str:
    tpl = Template(read_text(TEMPLATE_PATH))
    full = tpl.render(title=title, author=author, body_html=body_html)
    m = re.search(r'<div class="sheet">(.*)</div>\s*</div>\s*</body>', full, flags=re.S)
    article_inner = m.group(1).strip() if m else body_html
    return article_inner


def registry_thumb_media_id(md_path: Path) -> str:
    if not DEFAULT_REGISTRY.exists():
        return ''
    text = read_text(DEFAULT_REGISTRY)
    rel = str(md_path.relative_to(ROOT)) if md_path.is_absolute() and md_path.is_relative_to(ROOT) else str(md_path)
    if rel not in text and md_path.name not in text:
        return ''
    m = re.search(r'^- Thumb Media ID:\s*(.+?)\s*$', text, flags=re.M)
    return m.group(1).strip() if m else ''


def build_payload(title: str, author: str, digest: str, content_html: str, thumb_media_id: str) -> Dict[str, Any]:
    if not thumb_media_id:
        raise ValueError('缺少 thumb_media_id。请通过 --thumb-media-id、WECHAT_THUMB_MEDIA_ID（兼容 WX_GZH_THUMB_MEDIA_ID）提供，或在 CONTENT_REGISTRY.md 中登记。')
    return {
        'articles': [{
            'title': title,
            'author': author,
            'digest': digest,
            'thumb_media_id': thumb_media_id,
            'content': content_html,
            'need_open_comment': 0,
            'only_fans_can_comment': 0,
        }]
    }


def env_first(*keys: str) -> str:
    for key in keys:
        val = os.getenv(key, '').strip()
        if val:
            return val
    return ''


def get_access_token() -> str:
    token = env_first('WECHAT_ACCESS_TOKEN')
    if token:
        return token
    app_id = env_first('WECHAT_APP_ID', 'WX_GZH_APPID')
    app_secret = env_first('WECHAT_APP_SECRET', 'WX_GZH_APPSECRET')
    if not app_id or not app_secret:
        raise RuntimeError('缺少 WECHAT_ACCESS_TOKEN 或 WECHAT_APP_ID/WECHAT_APP_SECRET（兼容 WX_GZH_APPID/WX_GZH_APPSECRET）。')
    params = urllib.parse.urlencode({
        'grant_type': 'client_credential',
        'appid': app_id,
        'secret': app_secret,
    })
    url = f'https://api.weixin.qq.com/cgi-bin/token?{params}'
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if 'access_token' not in data:
        raise RuntimeError(f'获取 access token 失败: {data}')
    return data['access_token']


def upload_inline_image(image_path: Path) -> str:
    token = get_access_token()
    url = f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={urllib.parse.quote(token)}'
    with image_path.open('rb') as f:
        resp = requests.post(url, files={'media': (image_path.name, f, 'image/png')}, timeout=60)
    data = resp.json()
    if 'url' not in data:
        raise RuntimeError(f'上传正文图片失败: {data}')
    return data['url']


def resolve_body_images(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    resolved = []
    for item in items:
        heading = str(item.get('before_heading', '')).strip()
        if not heading:
            continue
        src = str(item.get('src', '')).strip() or str(item.get('url', '')).strip()
        image_path = str(item.get('image_path', '')).strip() or str(item.get('path', '')).strip()
        media_id = str(item.get('media_id', '')).strip()
        if src:
            resolved.append({'before_heading': heading, 'src': src})
            continue
        if image_path:
            p = Path(image_path)
            if not p.is_absolute():
                p = ROOT / image_path
            resolved.append({'before_heading': heading, 'src': upload_inline_image(p)})
            continue
        if media_id:
            raise RuntimeError(f'正文图片配置 `{heading}` 仍是 media_id；微信公众号正文图片必须先上传成 URL，不能直接把 media_id 填进 img src。')
    return resolved


def publish_draft(payload: Dict[str, Any]) -> Dict[str, Any]:
    token = get_access_token()
    url = f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={urllib.parse.quote(token)}'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data


def summarize(title: str, output_dir: Path, payload: Dict[str, Any], used_images: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        'title': title,
        'output_dir': str(output_dir.relative_to(ROOT)) if output_dir.is_relative_to(ROOT) else str(output_dir),
        'payload_article_count': len(payload.get('articles', [])),
        'body_image_count': len(used_images),
        'used_images': used_images,
    }


def cmd_render(args):
    load_env()
    md_path = Path(args.input)
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    body_images = resolve_body_images(load_json(Path(args.images_json) if args.images_json else None, []))
    md_text = read_text(md_path)
    rendered = render_markdown(md_text, body_images)
    title = args.title or rendered['title']
    author = args.author or env_first('WECHAT_AUTHOR', 'WX_GZH_AUTHOR') or '岁月'
    digest = args.digest or env_first('WECHAT_DEFAULT_DIGEST', 'WX_GZH_DEFAULT_DIGEST')
    thumb_media_id = args.thumb_media_id or env_first('WECHAT_THUMB_MEDIA_ID', 'WX_GZH_THUMB_MEDIA_ID') or registry_thumb_media_id(md_path)
    try:
        content_html = render_via_ziliu(inject_images_into_markdown(md_text, body_images))
    except Exception:
        content_html = wrap_article(title, author, rendered['body_html'])

    output_dir = Path(args.output_dir) if args.output_dir else (SKILL_DIR / 'out' / slugify(title))
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    write_text(output_dir / 'rendered.html', content_html)
    payload = None
    if thumb_media_id:
        payload = build_payload(title, author, digest, content_html, thumb_media_id)
        write_text(output_dir / 'payload.json', json.dumps(payload, ensure_ascii=False, indent=2))
    summary = summarize(title, output_dir, payload or {'articles': []}, rendered['used_images'])
    write_text(output_dir / 'summary.json', json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_publish(args):
    load_env()
    md_path = Path(args.input)
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    body_images = resolve_body_images(load_json(Path(args.images_json) if args.images_json else None, []))
    md_text = read_text(md_path)
    rendered = render_markdown(md_text, body_images)
    title = args.title or rendered['title']
    author = args.author or env_first('WECHAT_AUTHOR', 'WX_GZH_AUTHOR') or '岁月'
    digest = args.digest or env_first('WECHAT_DEFAULT_DIGEST', 'WX_GZH_DEFAULT_DIGEST')
    thumb_media_id = args.thumb_media_id or env_first('WECHAT_THUMB_MEDIA_ID', 'WX_GZH_THUMB_MEDIA_ID') or registry_thumb_media_id(md_path)
    try:
        content_html = render_via_ziliu(inject_images_into_markdown(md_text, body_images))
    except Exception:
        content_html = wrap_article(title, author, rendered['body_html'])
    payload = build_payload(title, author, digest, content_html, thumb_media_id)
    data = publish_draft(payload)
    print(json.dumps({
        'title': title,
        'response': data,
        'body_image_count': len(rendered['used_images'])
    }, ensure_ascii=False, indent=2))


def build_parser():
    p = argparse.ArgumentParser(description='微信公众号草稿渲染与发布')
    sub = p.add_subparsers(dest='command', required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--input', required=True, help='Markdown 文件路径')
    common.add_argument('--images-json', help='正文图片 media_id 映射 JSON')
    common.add_argument('--title', help='覆盖标题')
    common.add_argument('--author', help='覆盖作者')
    common.add_argument('--digest', help='覆盖摘要')
    common.add_argument('--thumb-media-id', help='封面 media id')

    r = sub.add_parser('render', parents=[common], help='仅渲染，不发布')
    r.add_argument('--output-dir', help='输出目录')
    r.set_defaults(func=cmd_render)

    pb = sub.add_parser('publish', parents=[common], help='发布到草稿箱')
    pb.set_defaults(func=cmd_publish)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
