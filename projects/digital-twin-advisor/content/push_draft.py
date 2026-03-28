#!/usr/bin/env python3
"""Deprecated wrapper.

已迁移到 skills/wechat/scripts/publish.py。
封面 media id、作者、摘要等配置应从 .env / 参数读取，禁止硬编码。
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace')
NEW_SCRIPT = ROOT / 'skills' / 'wechat' / 'scripts' / 'publish.py'
DEFAULT_INPUT = ROOT / 'projects' / 'digital-twin-advisor' / 'content' / 'kazike_boss_wechat_article_v1.md'


def main():
    cmd = [
        sys.executable,
        str(NEW_SCRIPT),
        'render',
        '--input', str(DEFAULT_INPUT),
        '--output-dir', str(ROOT / 'skills' / 'wechat' / 'out' / 'legacy-render-preview')
    ]
    raise SystemExit(subprocess.call(cmd))


if __name__ == '__main__':
    main()
