#!/usr/bin/env python3
"""Convert agent-framework-2026.md to styled HTML and PDF"""

import subprocess
import sys

md_file = "/root/.openclaw/workspace/projects/reports/agent-framework-2026.md"
html_file = "/root/.openclaw/workspace/projects/reports/agent-framework-2026.html"
pdf_file = "/root/.openclaw/workspace/projects/reports/agent-framework-2026.pdf"

# Read markdown
with open(md_file, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML using python-markdown or manual conversion
try:
    import markdown
    body_html = markdown.markdown(md_content, extensions=["tables", "fenced_code", "toc"])
except ImportError:
    # Fallback: use pandoc if available
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html", md_file],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        body_html = result.stdout
    else:
        # Manual basic conversion
        import re
        body_html = md_content
        body_html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', body_html, flags=re.MULTILINE)
        body_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', body_html, flags=re.MULTILINE)
        body_html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', body_html, flags=re.MULTILINE)
        body_html = re.sub(r'^\*\*(.+?)\*\*$', r'<strong>\1</strong>', body_html, flags=re.MULTILINE)
        body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_html)
        body_html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', body_html)
        body_html = re.sub(r'`(.+?)`', r'<code>\1</code>', body_html)
        # Tables
        lines = body_html.split('\n')
        new_lines = []
        in_table = False
        for line in lines:
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    new_lines.append('<table>')
                    in_table = True
                if re.match(r'^\|[-| :]+\|$', line.strip()):
                    continue  # skip separator
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                row = '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
                new_lines.append(row)
            else:
                if in_table:
                    new_lines.append('</table>')
                    in_table = False
                new_lines.append(line)
        if in_table:
            new_lines.append('</table>')
        body_html = '\n'.join(new_lines)
        # Paragraphs
        paragraphs = body_html.split('\n\n')
        body_html = '\n'.join(
            f'<p>{p}</p>' if not p.strip().startswith('<') and p.strip() else p
            for p in paragraphs
        )

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@400;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #1a1a2e;
    background: #ffffff;
}

/* Cover Page */
.cover {
    page-break-after: always;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 60px 40px;
    color: white;
}

.cover-logo {
    font-size: 14pt;
    font-weight: 300;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 60px;
    border: 1px solid #a78bfa;
    padding: 8px 24px;
    border-radius: 20px;
}

.cover h1 {
    font-size: 32pt;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 20px;
    line-height: 1.3;
    border: none;
    background: none;
    padding: 0;
}

.cover h2 {
    font-size: 16pt;
    font-weight: 300;
    color: #c4b5fd;
    margin-bottom: 60px;
    border: none;
    background: none;
    padding: 0;
}

.cover-meta {
    font-size: 11pt;
    color: #8b8ba7;
    margin-top: 40px;
}

.cover-divider {
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    margin: 30px auto;
    border-radius: 2px;
}

/* Page Layout */
@page {
    size: A4;
    margin: 20mm 22mm 20mm 22mm;
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #888;
    }
}

/* Content */
.content {
    padding: 0;
}

h1 {
    font-size: 22pt;
    font-weight: 700;
    color: #1a1a2e;
    margin: 40px 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 3px solid #7c3aed;
    page-break-before: always;
}

h1:first-child {
    page-break-before: avoid;
}

h2 {
    font-size: 16pt;
    font-weight: 600;
    color: #2d2d5a;
    margin: 30px 0 15px 0;
    padding-left: 16px;
    border-left: 4px solid #7c3aed;
    background: linear-gradient(90deg, #f5f3ff, transparent);
    padding: 8px 16px;
    border-radius: 0 4px 4px 0;
}

h3 {
    font-size: 13pt;
    font-weight: 600;
    color: #4c1d95;
    margin: 24px 0 12px 0;
}

h4 {
    font-size: 11pt;
    font-weight: 600;
    color: #5b21b6;
    margin: 16px 0 8px 0;
}

p {
    margin-bottom: 12px;
    text-align: justify;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 9.5pt;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    border-radius: 8px;
    overflow: hidden;
}

thead tr {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: white;
}

thead th, table tr:first-child td {
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
}

tbody tr:nth-child(even) {
    background: #f5f3ff;
}

tbody tr:hover {
    background: #ede9fe;
}

td {
    padding: 9px 12px;
    border-bottom: 1px solid #e9e7f0;
    vertical-align: top;
}

/* Code blocks */
pre {
    background: #1e1e3f;
    color: #a9b1d6;
    padding: 16px 20px;
    border-radius: 8px;
    margin: 16px 0;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.6;
    border-left: 4px solid #7c3aed;
}

code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    background: #f3f0ff;
    color: #5b21b6;
    padding: 2px 6px;
    border-radius: 4px;
}

pre code {
    background: none;
    color: inherit;
    padding: 0;
}

/* Lists */
ul, ol {
    margin: 12px 0 12px 24px;
}

li {
    margin-bottom: 6px;
}

/* Blockquote */
blockquote {
    border-left: 4px solid #7c3aed;
    background: #faf5ff;
    padding: 12px 20px;
    margin: 16px 0;
    border-radius: 0 8px 8px 0;
    color: #4c1d95;
    font-style: italic;
}

/* Strong/em */
strong { color: #4c1d95; font-weight: 700; }

/* Horizontal rule */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #7c3aed, transparent);
    margin: 30px 0;
}

/* Highlight boxes */
.highlight-box {
    background: linear-gradient(135deg, #faf5ff, #f0f9ff);
    border: 1px solid #d8b4fe;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
}

/* Product badges */
.badge {
    display: inline-block;
    background: #7c3aed;
    color: white;
    font-size: 8pt;
    padding: 2px 8px;
    border-radius: 12px;
    margin-right: 4px;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 8.5pt;
    color: #9ca3af;
    border-top: 1px solid #e5e7eb;
    padding-top: 16px;
    margin-top: 40px;
}
"""

# Build full HTML
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>企业AI Agent部署方案全景研报 - ClawLabs 2026</title>
<style>
{CSS}
</style>
</head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">ClawLabs Research</div>
    <h1>企业AI Agent<br>部署方案全景研报</h1>
    <div class="cover-divider"></div>
    <h2>OpenClaw生态与主流竞品深度对比分析</h2>
    <div class="cover-meta">
        <p>2026年3月 &nbsp;|&nbsp; 出品：ClawLabs</p>
        <p style="margin-top:8px; font-size:9pt;">涵盖15个主流AI Agent框架与平台的深度调研</p>
    </div>
</div>

<!-- Main Content -->
<div class="content">
{body_html}
</div>

<div class="footer">
    <p>© 2026 ClawLabs · 企业AI Agent部署方案全景研报 · 内部参考资料</p>
    <p>本报告仅供内部决策参考，数据截至2026年3月</p>
</div>

</body>
</html>"""

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ HTML generated: {html_file}")

# Generate PDF
print("📄 Generating PDF with WeasyPrint...")
result = subprocess.run(
    ["/usr/local/bin/weasyprint", html_file, pdf_file],
    capture_output=True, text=True
)

if result.returncode == 0:
    import os
    size = os.path.getsize(pdf_file)
    print(f"✅ PDF generated: {pdf_file}")
    print(f"📊 PDF size: {size:,} bytes ({size/1024:.1f} KB)")
else:
    print(f"❌ WeasyPrint error: {result.stderr}")
    sys.exit(1)
