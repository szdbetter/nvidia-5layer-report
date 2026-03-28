#!/usr/bin/env python3
"""Deprecated wrapper.

公众号发布脚本已迁移到 skills/wechat/scripts/publish.py。
所有凭证一律从 .env / 环境变量读取，禁止硬编码。
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace')
NEW_SCRIPT = ROOT / 'skills' / 'wechat' / 'scripts' / 'publish.py'
DEFAULT_IMAGES = ROOT / 'skills' / 'wechat' / 'examples' / 'body_images.json'
DEFAULT_INPUT = ROOT / 'projects' / 'digital-twin-advisor' / 'content' / 'kazike_boss_wechat_article_v1.md'


def main():
    if not NEW_SCRIPT.exists():
        raise SystemExit('missing new script: skills/wechat/scripts/publish.py')
    if os.getenv('WECHAT_ACCESS_TOKEN'):
        print('警告：检测到 WECHAT_ACCESS_TOKEN；建议优先改为 WECHAT_APP_ID + WECHAT_APP_SECRET 自动换取 token。', file=sys.stderr)
    cmd = [
        sys.executable,
        str(NEW_SCRIPT),
        'render',
        '--input', str(DEFAULT_INPUT),
        '--images-json', str(DEFAULT_IMAGES),
        '--output-dir', str(ROOT / 'skills' / 'wechat' / 'out' / 'legacy-wrapper-preview')
    ]
    raise SystemExit(subprocess.call(cmd))


if __name__ == '__main__':
    main()
