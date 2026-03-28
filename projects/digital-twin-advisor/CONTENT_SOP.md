# 公众号写作SOP（强制收口版）

## 适用范围
所有公众号文章产出，包括但不限于：
- 数字分身项目相关文章
- 工作复盘与经验沉淀
- 产品方法论输出
- 行业分析与观点文章

## SOP步骤

### 1. 锁定写作协议
- 明确文章主题与目标读者
- 确定文章风格（卡兹克式/其他）
- 确定文章视角（老板第一人称/第三人称）
- 锁定交付时间节点

### 2. 生成文章内容
- 撰写正文Markdown
- 生成配图提示词（全中文）
- 确认段落结构（观点鲜明、句子短、信息密度高）

### 3. 格式化与排版
- 转换为公众号发布格式
- 处理图片上传
- 确认预览效果

### 4. 推送草稿箱
- 调用字流API或微信草稿箱接口
- 获取草稿返回结果
- 记录草稿ID与预览链接

### 5. 强制收口（Finalize）

只有同时满足以下**四个条件**，才视为"文章已完成"：

| 条件 | 要求 | 证据 |
|------|------|------|
| 1. 内容文件 | 文章Markdown已落盘 | 文件路径存在 |
| 2. 配图文件 | 配图提示词已落盘 | 文件路径存在 |
| 3. 草稿推送 | 已推送至公众号草稿箱 | 返回media_id或草稿ID |
| 4. 状态登记 | 已写入CONTENT_REGISTRY.md | 登记记录存在 |

**异常处理**：
- 缺少任一条件 → 报告为"执行中"/"待推送"/"待登记"
- 不允许宣布"已完成"直到四条件全部满足

## 文件存储规范

```
projects/digital-twin-advisor/content/
├── {article_id}_article.md        # 文章正文
├── {article_id}_image_prompts.md  # 配图提示词
└── {article_id}_meta.json         # 元数据（标题、摘要、草稿ID等）
```

## CONTENT_REGISTRY.md 格式

```markdown
# 公众号文章登记表

## {article_id}
- Title: {文章标题}
- Status: draft/published
- Created: {创建时间}
- Published: {发布时间，如已发布}
- Draft ID: {草稿ID}
- Preview URL: {预览链接}
- Files:
  - {article_id}_article.md
  - {article_id}_image_prompts.md
  - {article_id}_meta.json
```

---

**版本**: v1.0
**创建时间**: 2026-03-12
**适用项目**: 数字分身顾问系统及所有公众号内容产出