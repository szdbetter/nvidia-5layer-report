#!/usr/bin/env python3
"""
ClawLabs 研报 PDF 生成器
Usage: python3 gen-report-pdf.py <markdown_file> [output_pdf] [--category 方案报告] [--subtitle "副标题"]
"""
import sys, os, json, re
from datetime import datetime
from pathlib import Path

try:
    from weasyprint import HTML, CSS
except ImportError:
    print("Installing weasyprint..."); os.system("pip install weasyprint -q")
    from weasyprint import HTML, CSS

# ── Config ────────────────────────────────────────────────────────────────────
REPORTS_DIR = Path(__file__).parent.parent / "public" / "reports"
META_FILE   = REPORTS_DIR / "reports.json"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Args ──────────────────────────────────────────────────────────────────────
md_path   = sys.argv[1] if len(sys.argv) > 1 else None
out_name  = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
category  = "方案报告"
subtitle  = ""
for i, a in enumerate(sys.argv):
    if a == "--category" and i+1 < len(sys.argv): category = sys.argv[i+1]
    if a == "--subtitle" and i+1 < len(sys.argv): subtitle = sys.argv[i+1]

if not md_path:
    print("Usage: gen-report-pdf.py <markdown_file> [output.pdf] [--category X] [--subtitle X]")
    sys.exit(1)

md_path = Path(md_path)
md_text = md_path.read_text(encoding="utf-8")

# ── Parse title from markdown ─────────────────────────────────────────────────
title_match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
title = title_match.group(1).strip() if title_match else md_path.stem
# Remove blockquote subtitle from body
md_body = re.sub(r'^>\s*.+\n\n?', '', md_text, count=1, flags=re.MULTILINE)

# ── Convert markdown to HTML ───────────────────────────────────────────────────
try:
    import markdown
    body_html = markdown.markdown(md_body, extensions=['tables', 'fenced_code'])
except ImportError:
    os.system("pip install markdown -q")
    import markdown
    body_html = markdown.markdown(md_body, extensions=['tables', 'fenced_code'])

today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
slug  = out_name or re.sub(r'[^\w\-]', '-', title.lower().replace(' ','')[:40]) + f"-{datetime.now().strftime('%Y%m%d')}.pdf"
if not slug.endswith(".pdf"): slug += ".pdf"
out_path = REPORTS_DIR / slug

# ── HTML Template ─────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  @import url('data:text/css,');
  @page {{
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @bottom-center {{
      content: "ClawLabs Research  ·  第 " counter(page) " 页，共 " counter(pages) " 页";
      font-size: 9pt;
      color: #999;
      font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif;
    }}
    @top-right {{
      content: "{today}";
      font-size: 9pt;
      color: #999;
      font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif;
    }}
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Noto Serif CJK SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #1a1a1a;
    background: #fff;
  }}

  /* Cover Page */
  .cover {{
    page-break-after: always;
    height: 257mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0 10mm;
    background: linear-gradient(160deg, #0a1628 0%, #0f2952 60%, #1a3a6b 100%);
    color: #fff;
    position: relative;
  }}
  .cover-logo {{
    position: absolute;
    top: 18mm;
    left: 10mm;
    font-size: 13pt;
    font-weight: 700;
    letter-spacing: 2px;
    color: rgba(255,255,255,0.7);
  }}
  .cover-tag {{
    display: inline-block;
    background: rgba(88,166,255,0.2);
    border: 1px solid rgba(88,166,255,0.5);
    color: #58a6ff;
    font-size: 9pt;
    padding: 3px 10px;
    border-radius: 3px;
    letter-spacing: 1px;
    margin-bottom: 12mm;
    font-family: "Noto Sans CJK SC", sans-serif;
  }}
  .cover-title {{
    font-size: 24pt;
    font-weight: 700;
    line-height: 1.35;
    color: #fff;
    margin-bottom: 6mm;
    letter-spacing: 0.5px;
  }}
  .cover-subtitle {{
    font-size: 12pt;
    color: rgba(255,255,255,0.65);
    margin-bottom: 16mm;
    line-height: 1.6;
  }}
  .cover-divider {{
    width: 40mm;
    height: 2px;
    background: #58a6ff;
    margin-bottom: 10mm;
  }}
  .cover-meta {{
    font-size: 9.5pt;
    color: rgba(255,255,255,0.5);
    line-height: 1.8;
    font-family: "Noto Sans CJK SC", sans-serif;
  }}
  .cover-footer {{
    position: absolute;
    bottom: 12mm;
    left: 10mm;
    right: 10mm;
    border-top: 1px solid rgba(255,255,255,0.15);
    padding-top: 5mm;
    font-size: 8pt;
    color: rgba(255,255,255,0.3);
    display: flex;
    justify-content: space-between;
    font-family: "Noto Sans CJK SC", sans-serif;
  }}

  /* Body */
  .body-content {{ padding-top: 4mm; }}
  h1 {{ display: none; }}
  h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: #0f2952;
    margin: 8mm 0 4mm;
    padding-bottom: 2mm;
    border-bottom: 2px solid #e0e8f5;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11pt;
    font-weight: 600;
    color: #1a3a6b;
    margin: 5mm 0 2mm;
    page-break-after: avoid;
  }}
  p {{
    margin-bottom: 3.5mm;
    text-align: justify;
    text-justify: inter-character;
  }}
  strong {{ color: #0f2952; font-weight: 700; }}
  em {{ color: #555; }}
  ul, ol {{
    margin: 2mm 0 3.5mm 5mm;
    padding-left: 4mm;
  }}
  li {{ margin-bottom: 1.5mm; }}
  blockquote {{
    border-left: 3px solid #58a6ff;
    background: #f0f6ff;
    padding: 3mm 5mm;
    margin: 3mm 0 4mm;
    color: #2c4a7a;
    font-style: normal;
    border-radius: 0 4px 4px 0;
  }}
  hr {{
    border: none;
    border-top: 1px solid #e0e8f5;
    margin: 5mm 0;
  }}
  .disclaimer {{
    margin-top: 10mm;
    padding-top: 4mm;
    border-top: 1px solid #e0e8f5;
    font-size: 8pt;
    color: #999;
    line-height: 1.6;
    font-style: italic;
    font-family: "Noto Sans CJK SC", sans-serif;
  }}
</style>
</head>
<body>

<!-- Cover Page -->
<div class="cover">
  <div class="cover-logo">ClawLabs Research</div>
  <span class="cover-tag">{category}</span>
  <div class="cover-title">{title}</div>
  {"<div class='cover-subtitle'>" + subtitle + "</div>" if subtitle else ""}
  <div class="cover-divider"></div>
  <div class="cover-meta">
    发布日期：{today}<br>
    出品方：ClawLabs × 中孚投资<br>
    研究范围：深圳市建筑公务署医疗项目
  </div>
  <div class="cover-footer">
    <span>本报告仅供内部参考，不构成投资建议</span>
    <span>clawlabs.top</span>
  </div>
</div>

<!-- Body -->
<div class="body-content">
{body_html}
<div class="disclaimer">
  免责声明：本报告由 ClawLabs 研究团队基于公开信息和行业调研撰写，仅供参考交流使用。
  报告中引用的第三方数据、案例及观点，版权归原始来源所有。
  本报告不构成任何采购建议或合同承诺，具体方案以正式合同为准。
</div>
</div>

</body>
</html>"""

# ── Generate PDF ───────────────────────────────────────────────────────────────
print(f"Generating PDF: {out_path}")
HTML(string=html, base_url=str(REPORTS_DIR)).write_pdf(str(out_path))
print(f"✓ PDF written: {out_path} ({out_path.stat().st_size // 1024} KB)")

# ── Update reports.json metadata ──────────────────────────────────────────────
reports = []
if META_FILE.exists():
    try: reports = json.loads(META_FILE.read_text())
    except: reports = []

# Remove old entry with same slug
reports = [r for r in reports if r.get("file") != slug]
reports.insert(0, {
    "file": slug,
    "title": title,
    "subtitle": subtitle,
    "category": category,
    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "size_kb": out_path.stat().st_size // 1024,
})
META_FILE.write_text(json.dumps(reports, ensure_ascii=False, indent=2))
print(f"✓ Metadata updated: {META_FILE}")
print(f"\n  URL: https://clawlabs.top/reports/{slug}")
