# 微信公众号自动化全链路实战

## 1. 抓取文章与踩坑分析

**抓取方式**：
通用 `web_fetch` 和 `Jina` 容易被微信反爬或只抓到外壳。我改用原生 Python + `BeautifulSoup` + 伪装 `User-Agent`，直接解析了 `#js_content`，成功提取了全文。

**从文章和实际操作中提取的核心坑点（已解决）**：
1. **中文 JSON 序列化（致命报错 45003）**：
   向微信 `cgi-bin/draft/add` 接口提交数据时，如果标题或内容包含中文，绝不能直接序列化。必须严格使用 `json.dumps(payload, ensure_ascii=False).encode('utf-8')`，否则微信直接报错 `45003`。
2. **字流 API 字段变更（报错 Invalid input）**：
   文章里写着传 `{"markdown": "内容"}`，但字流最新的 API 已经改成了 `{"content": "内容"}`。传错会一直报 400 错误。
3. **封面图机制**：
   草稿箱不接受外链图片。必须先调用微信 `material/add_material` 接口，把本地图片上传，拿到 `thumb_media_id`，再塞进草稿 payload 中。

---

## 2. 封面配图 Prompt 固化

根据你提供的附件配图，这种风格是典型的“现代极简科技风”，注重信息层级和 UI 感。

**固化的默认生成 Prompt (Tech 风格)**：
```text
科技感公众号头图，极简排版，大留白，高级灰与蓝紫（或主体色）渐变背景，
卡片式信息布局，柔和的磨砂玻璃光感（Glassmorphism），发光几何装饰元素，
现代UI视觉语言，适合AI技术文章封面，非写实，排版精致、克制、专业，比例 16:9。
```

---

## 3. 文章生成与发布测试

我结合这两天的实战（打通 Polymarket 守护进程、接入 Agent Reach、攻克微信 API），撰写了一篇名为《让 OpenClaw 接管公众号发布：踩坑与全自动化实战》的 Markdown 文章。

**执行流程**：
1. 上传附件图片至微信素材库，获取 `thumb_media_id`。
2. 调用字流 API，指定 `style: "tech"`，将 Markdown 渲染为极客风 HTML。
3. 携带正确的 UTF-8 编码，调用微信草稿箱 API 发布。

**结果**：
✅ 已发布到公众号草稿箱