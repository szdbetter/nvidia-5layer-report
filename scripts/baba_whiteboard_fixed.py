#!/usr/bin/env python3
"""
BABA研报白板风格图片生成器 v2
策略：Gemini生成白板底图 → Pillow用NotoSansCJK精确渲染中文，彻底解决乱码
"""
import os, sys, json, time, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 字体路径
FONT_REGULAR = "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc"
FONT_BOLD    = "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc"
FONT_BLACK   = "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Black.ttc"

OUT_DIR = Path("/root/.openclaw/workspace/ppt_outputs/baba_whiteboard_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKILL_SCRIPT = Path("/root/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py")

W, H = 1792, 1024  # 16:9

# 颜色
BG_WHITE   = (252, 251, 248)
INK_BLACK  = (20, 20, 30)
INK_BLUE   = (30, 58, 95)
INK_RED    = (192, 57, 43)
INK_GREEN  = (39, 174, 96)
INK_GOLD   = (211, 153, 20)
INK_GRAY   = (120, 120, 130)
INK_LIGHT  = (200, 210, 220)

def font(size, bold=False, black=False):
    path = FONT_BLACK if black else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(path, size)

def gen_bg(name, prompt_hint):
    """用 Gemini 生成白板底图，失败则用纯色"""
    bg_path = OUT_DIR / f"_bg_{name}.png"
    if bg_path.exists():
        return Image.open(bg_path).resize((W, H))
    prompt = (
        f"Minimalist empty whiteboard background, clean white surface with very subtle texture, "
        f"slight imperfections and marker stains from previous use, realistic office whiteboard, "
        f"no text, no diagrams, no writing. {prompt_hint}"
    )
    try:
        env = os.environ.copy()
        result = subprocess.run(
            ["uv", "run", str(SKILL_SCRIPT),
             "--prompt", prompt,
             "--filename", str(bg_path),
             "--aspect-ratio", "16:9",
             "--resolution", "2K"],
            capture_output=True, text=True, timeout=120, env=env
        )
        if bg_path.exists():
            return Image.open(bg_path).resize((W, H))
    except Exception as e:
        print(f"  [bg gen failed: {e}] using solid color")
    # fallback: 纯白背景带轻微噪点感
    img = Image.new("RGB", (W, H), BG_WHITE)
    return img

def draw_divider(draw, y, x1=60, x2=None, color=INK_LIGHT, width=2):
    if x2 is None: x2 = W - 60
    draw.line([(x1, y), (x2, y)], fill=color, width=width)

def draw_bullet_list(draw, items, x, y, fnt, color=INK_BLACK, bullet="•", line_h=44):
    bf = font(fnt.size, bold=False)
    for item in items:
        draw.text((x, y), bullet, font=bf, fill=INK_BLUE)
        draw.text((x + 28, y), item, font=fnt, fill=color)
        y += line_h
    return y

def draw_table(draw, rows, x, y, col_widths, row_h=46, header_bg=INK_BLUE, header_fg=(255,255,255)):
    """绘制表格"""
    for r, row in enumerate(rows):
        cx = x
        for c, (cell, cw) in enumerate(zip(row, col_widths)):
            rx, ry, rw, rh = cx, y + r * row_h, cw, row_h
            if r == 0:
                draw.rectangle([rx, ry, rx+rw, ry+rh], fill=header_bg)
                fnt = font(20, bold=True)
                draw.text((rx+10, ry+12), str(cell), font=fnt, fill=header_fg)
            else:
                bg = (245, 247, 250) if r % 2 == 0 else (255, 255, 255)
                draw.rectangle([rx, ry, rx+rw, ry+rh], fill=bg, outline=INK_LIGHT, width=1)
                fnt = font(19)
                draw.text((rx+10, ry+12), str(cell), font=fnt, fill=INK_BLACK)
            cx += cw

def make_page(name, draw_fn, bg_hint=""):
    print(f"  生成: {name}")
    img = gen_bg(name, bg_hint)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw_fn(draw, img)
    result = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    out = OUT_DIR / f"{name}.png"
    result.save(out, quality=95)
    print(f"  ✅ {out}")
    return str(out)

# ─────────────────────────────────────────────
# 各页绘制函数
# ─────────────────────────────────────────────

def draw_cover(draw, bg):
    # 顶部深色条
    draw.rectangle([(0,0),(W,160)], fill=(20,20,40,230))
    draw.text((W//2, 30), "阿里巴巴（BABA）深度研报", font=font(72, black=True),
              fill=(255,255,255), anchor="mm")
    draw.text((W//2, 115), "10x Alpha 猎手 · 第二阶段 · v5.0  |  OpenClaw AI Research Engine · 2026-03-17",
              font=font(28), fill=INK_GOLD, anchor="mm")
    # 中央卡片
    draw.rectangle([(80, 200), (W-80, 560)], fill=(255,255,255,210), outline=INK_BLUE, width=3)
    draw.text((W//2, 260), "加权总分", font=font(32, bold=True), fill=INK_GRAY, anchor="mm")
    draw.text((W//2, 330), "7.16 / 10", font=font(90, black=True), fill=INK_BLUE, anchor="mm")
    draw.text((W//2, 415), "✅ Alpha — 具备超额收益潜力", font=font(36, bold=True), fill=INK_GREEN, anchor="mm")
    draw_divider(draw, 455, 200, W-200, INK_LIGHT)
    stats = [
        ("胜率", "68%", INK_BLUE),
        ("赔率", "1 : 2.8", INK_BLACK),
        ("目标价", "$205", INK_GREEN),
        ("止损", "$115", INK_RED),
        ("当前", "$136.85", INK_BLACK),
    ]
    sx = 160
    for label, val, col in stats:
        draw.text((sx, 475), label, font=font(22, bold=True), fill=INK_GRAY, anchor="mm")
        draw.text((sx, 520), val, font=font(34, black=True), fill=col, anchor="mm")
        sx += 300
    # 底部
    draw.rectangle([(0, H-80),(W, H)], fill=(20,20,40,180))
    draw.text((W//2, H-40), "投资建议：合理分批建仓（Moderate Accumulate）",
              font=font(30, bold=True), fill=(255,255,255), anchor="mm")

def draw_dashboard(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "🏁  投资决策驾驶舱", font=font(48, bold=True), fill=(255,255,255), anchor="lm")
    rows = [
        ["项目", "结论"],
        ["投资建议", "合理分批建仓（Moderate Accumulate）"],
        ["时机判断", "错杀修复期：反垄断清零 + AI战略落地 + 估值历史低位"],
        ["触发事件", "2026-03-19  Q3 FY2026 财报（3天后）"],
        ["当前价格", "$136.85（处于极度低估区间）"],
        ["胜率预测", "68%"],
        ["赔率预测", "1 : 2.8（12个月目标 $192-205，止损 $118）"],
    ]
    draw_table(draw, rows, 60, 110, [260, W-140], row_h=112)
    draw.rectangle([(60, H-90),(W-60, H-20)], fill=(255,240,240,200), outline=INK_RED, width=2)
    draw.text((W//2, H-55), "核心逻辑：中国云AI绝对领导者 + 电商低估值护城河 + 反垄断出清 → 双击估值+盈利修复",
              font=font(26, bold=True), fill=INK_RED, anchor="mm")

def draw_scorecard(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "📊  14维度评分卡（加权总分 7.16/10）", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    scores = [
        ["维度", "得分", "权重"],
        ["1. 技术护城河 (12%)", "7.5", "0.90"],
        ["2. 商业模式 (10%)", "7.5", "0.75"],
        ["3. 收入增长 (10%)", "6.5", "0.65"],
        ["4. 盈利能力 (8%)", "7.5", "0.60"],
        ["5. 现金流与财务 (8%)", "7.5", "0.60"],
        ["6. 市场地位 (8%)", "7.0", "0.56"],
        ["7. 管理团队 (6%)", "6.0", "0.36"],
        ["8. 股东结构 (6%)", "6.0", "0.36"],
        ["9. 估值合理性 (10%)", "8.5", "0.85 ⭐"],
        ["10. 政策与监管 (6%)", "6.0", "0.36"],
        ["11. 产品迭代 (6%)", "8.0", "0.48"],
        ["12. 客户基础 (4%)", "7.5", "0.30"],
        ["13. 供应链自主 (4%)", "5.5", "0.22"],
        ["14. 分析师共识 (2%)", "8.5", "0.17 ⭐"],
    ]
    col_w = [W - 400, 160, 200]
    draw_table(draw, scores, 60, 100, col_w, row_h=60)
    # 总分标注
    draw.rectangle([(W-350, H-80),(W-20, H-10)], fill=INK_GREEN)
    draw.text((W-185, H-45), "总分  7.16 / 10  ✅ Alpha", font=font(24, bold=True),
              fill=(255,255,255), anchor="mm")

def draw_logic(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "💡  核心投资逻辑：认知差与重估路径", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    # 左侧：市场认知
    draw.rectangle([(40, 110),(W//2-20, H-20)], fill=(255,245,245,200), outline=INK_RED, width=2)
    draw.text((W//4, 145), "市场当前定价", font=font(34, bold=True), fill=INK_RED, anchor="mm")
    draw.text((W//4, 195), "❌ 增长停滞的中国电商公司", font=font(26), fill=INK_RED, anchor="mm")
    draw_divider(draw, 230, 60, W//2-40, INK_LIGHT)
    left_pts = [
        "P/S 折价 66%（vs 10年中位数 6.74x）",
        "受监管压制、竞争侵蚀",
        "结构性衰退预期",
        "市值 $326B，严重低估",
    ]
    draw_bullet_list(draw, left_pts, 80, 250, font(24), INK_BLACK, "✗", 52)
    # 右侧：真实情况
    draw.rectangle([(W//2+20, 110),(W-40, H-20)], fill=(240,255,245,200), outline=INK_GREEN, width=2)
    draw.text((W*3//4, 145), "真实价值", font=font(34, bold=True), fill=INK_GREEN, anchor="mm")
    draw.text((W*3//4, 195), "✅ 中国最大AI基础设施运营商", font=font(26), fill=INK_GREEN, anchor="mm")
    draw_divider(draw, 230, W//2+40, W-60, INK_LIGHT)
    right_pts = [
        "Qwen：全球下载量3亿+，超GPT-5.2",
        "云AI收入连续8季三位数增长",
        "电商每年产生 $27B EBITA 输血云AI",
        "对标 Microsoft 2016 云转型路径",
    ]
    draw_bullet_list(draw, right_pts, W//2+60, 250, font(24), INK_BLACK, "✓", 52)
    # 中间箭头
    draw.text((W//2, H//2), "→", font=font(80, black=True), fill=INK_BLUE, anchor="mm")

def draw_segments(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "📦  业务板块拆解  FY2025", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    rows = [
        ["业务板块", "营收（估算）", "占比", "增速", "战略角色"],
        ["淘宝天猫集团 (TTG)", "~500B 元", "~50%", "+低单位数", "现金牛 🐄"],
        ["云智能集团", "~115B 元", "~12%", "+34% ⭐", "增长引擎 🚀"],
        ["国际数字商业", "~108B 元", "~11%", "+33%", "全球化扩张 🌍"],
        ["菜鸟物流", "~100B 元", "~10%", "+中单位数", "战略支撑"],
        ["本地生活 / 大文娱", "~170B 元", "~17%", "混合", "生态补充"],
        ["合 计", "~996B 元", "100%", "+5-6%", "—"],
    ]
    col_w = [340, 200, 120, 180, W-900]
    draw_table(draw, rows, 40, 100, col_w, row_h=120)
    draw.text((W//2, H-30), "⭐ 云智能是核心估值驱动：34%增速 + AI三位数增长 + 调整EBITA +26%",
              font=font(26, bold=True), fill=INK_RED, anchor="mm")

def draw_ai(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "🤖  AI战略：Qwen 开源生态", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    rows = [
        ["指标", "数据 / 结论"],
        ["Qwen系列开源模型数量", "200 +"],
        ["全球下载量", "3 亿 +"],
        ["衍生模型数量", "10 万 +"],
        ["Qwen 3.5 架构", "397B MoE，Apache 2.0 开源"],
        ["上下文窗口", "256K tokens，支持 201 种语言"],
        ["性能对标", "超 GPT-5.2（Math-Vision 基准）"],
        ["成本优化", "较上代降低 60%，性能提升 8x"],
        ["3年 AI 投资计划", "3800 亿元（$52B）2026-2029"],
        ["中国AI云市场份额", "35.8%（2025H1）#1"],
    ]
    col_w = [380, W-440]
    draw_table(draw, rows, 40, 100, col_w, row_h=86)
    draw.rectangle([(40, H-75),(W-40, H-10)], fill=(20,80,20,30), outline=INK_GREEN, width=2)
    draw.text((W//2, H-42), "战略目标：将 Qwen 打造为 AI 时代的操作系统（CEO Eddie Wu）",
              font=font(26, bold=True), fill=INK_GREEN, anchor="mm")

def draw_competition(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "⚔️  竞争格局矩阵", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    # 电商
    draw.text((60, 108), "中国电商竞争", font=font(30, bold=True), fill=INK_RED)
    ecom = [
        ["平台", "市场份额", "威胁度"],
        ["淘宝天猫（阿里）", "~44%", "—（自身）"],
        ["京东 (JD)", "~24%", "低"],
        ["拼多多 (PDD)", "~19%", "中"],
        ["抖音电商", "快速增长", "⚠️ 最高"],
    ]
    draw_table(draw, ecom, 40, 145, [380, 200, 250], row_h=84)
    # 云
    mid = W//2 + 20
    draw.text((mid, 108), "中国云计算竞争", font=font(30, bold=True), fill=INK_BLUE)
    cloud = [
        ["云服务商", "份额", "AI 能力"],
        ["阿里云", "36%  #1 👑", "Qwen 系列"],
        ["华为云", "~15%  #2", "昇腾芯片"],
        ["腾讯云", "~12%  #3", "混元大模型"],
        ["字节云", "快速增长", "豆包"],
    ]
    draw_table(draw, cloud, mid, 145, [300, 230, W-mid-570], row_h=84)
    draw.text((W//2, H-30), "关键判断：抖音是电商最大威胁；云计算阿里护城河稳固，AI增速领先",
              font=font(26, bold=True), fill=INK_BLACK, anchor="mm")

def draw_risks(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(192,57,43,220))
    draw.text((60, 45), "⚠️  风险矩阵与熔断条件", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    rows = [
        ["熔断类型", "触发条件", "风险等级"],
        ["估值熔断", "股价跌破 $115 或 P/S < 1.8x", "🔴 高"],
        ["质量熔断", "整体EBITA利润率连续两季 < 11%", "🟡 中"],
        ["增长熔断", "云智能收入增速连续两季 < 15%", "🟡 中"],
        ["人才熔断", "Qwen核心负责人离职确认", "🟡 中"],
        ["竞争熔断", "阿里云份额跌破 25%（连续两季）", "🟡 中"],
        ["监管黑天鹅", "BABA 从 NYSE 摘牌（概率 < 5%）", "🔴 尾部风险"],
    ]
    col_w = [260, W-560, 240]
    draw_table(draw, rows, 40, 100, col_w, row_h=115, header_bg=INK_RED)
    draw.text((W//2, H-30), "现有对冲：$50B+现金储备 | 香港上市(HK:9988)备选 | T-Head自研芯片降低GPU依赖",
              font=font(24, bold=True), fill=INK_RED, anchor="mm")

def draw_strategy(draw, bg):
    draw.rectangle([(0,0),(W,90)], fill=(30,58,95,220))
    draw.text((60, 45), "🎯  操作策略与关键监控", font=font(44, bold=True), fill=(255,255,255), anchor="lm")
    # 左：建仓策略
    draw.text((60, 108), "建仓策略", font=font(30, bold=True), fill=INK_BLUE)
    ops = [
        ["操作", "价格", "说明"],
        ["首次建仓", "$130 - 138", "当前区间，分批2-3次"],
        ["加仓（财报后）", "$138 - 155", "云收入超预期则加仓"],
        ["目标止盈（12月）", "$192 - 205", "分析师共识目标"],
        ["激进目标（18月）", "$240 - 260", "P/S修复至4-4.5x"],
        ["止损线", "$115", "跌破逻辑受损，清仓"],
        ["建议仓位", "5 - 8%", "中国科技主力配置"],
    ]
    draw_table(draw, ops, 40, 145, [280, 200, W//2-280], row_h=84)
    # 右：关键监控
    mid = W//2 + 40
    draw.text((mid, 108), "关键催化剂监控", font=font(30, bold=True), fill=INK_RED)
    monitors = [
        "⭐⭐⭐⭐⭐  2026-03-19  Q3 FY2026 财报",
        "→ 云收入增速（目标 > 20%）",
        "→ AI收入占比 | TTG EBITA利润率",
        "→ FCF变化 | Capex指引",
        "⭐⭐⭐⭐  管理层电话会：Eddie Wu AI战略表态",
        "⭐⭐⭐    Qwen核心团队人员变动跟踪",
        "⭐⭐⭐    中美科技政策动态",
    ]
    y = 155
    for m in monitors:
        col = INK_RED if "财报" in m else INK_BLACK
        draw.text((mid, y), m, font=font(26 if "⭐" in m else 22), fill=col)
        y += 52

# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
pages = [
    ("01_cover",       draw_cover,       "professional lighting"),
    ("02_dashboard",   draw_dashboard,   "clean office board"),
    ("03_scorecard",   draw_scorecard,   "clean board"),
    ("04_logic",       draw_logic,       "boardroom whiteboard"),
    ("05_segments",    draw_segments,    "clean board"),
    ("06_ai",          draw_ai,          "clean tech whiteboard"),
    ("07_competition", draw_competition, "clean board"),
    ("08_risks",       draw_risks,       "warning board"),
    ("09_strategy",    draw_strategy,    "strategy whiteboard"),
]

print(f"生成 {len(pages)} 张白板图片 → {OUT_DIR}")
paths = []
for name, fn, hint in pages:
    p = make_page(name, fn, hint)
    paths.append(p)
    time.sleep(0.3)

print("\n===== 全部完成 =====")
for p in paths:
    print(f"MEDIA:{p}")
