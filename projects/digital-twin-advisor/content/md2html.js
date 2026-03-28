const fs = require('fs');
const MarkdownIt = require('markdown-it');

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

// 读取markdown文件
const markdownContent = fs.readFileSync('/root/.openclaw/workspace/projects/digital-twin-advisor/content/kazike_boss_wechat_article_v1.md', 'utf8');

// 转换为HTML
const htmlContent = md.render(markdownContent);

// 输出HTML
console.log(htmlContent);
