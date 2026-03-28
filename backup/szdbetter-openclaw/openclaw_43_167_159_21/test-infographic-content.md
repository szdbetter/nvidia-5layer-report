# 微信公众号自动化发布流程

## 第一层：核心目标
一句话指令，AI 自动成文、精美排版并推送到草稿箱

## 第二层：三大关键步骤

### 步骤1：撰写内容
AI 根据主题自动生成 Markdown 文章

### 步骤2：精美排版
调用字流 API，Markdown → 精美 HTML
支持 8 种风格：tech / elegant / blogger 等

### 步骤3：推送草稿箱
调用微信 API，上传封面 → 塞进草稿箱
返回 media_id 确认成功

## 第三层：三大核心踩坑

### 坑1：中文 JSON 编码
必须使用 ensure_ascii=False + UTF-8
否则触发 45003 错误

### 坑2：字流 API 字段
字段名是 content，不是 markdown
传错报 400 Invalid input

### 坑3：封面图限制
草稿箱不认外链图片
必须先上传素材库获取 media_id

## 第四层：最终效果
从构思到草稿箱：3 分钟
成本：几毛钱/篇