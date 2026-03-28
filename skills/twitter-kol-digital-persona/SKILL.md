---
name: twitter-kol-digital-persona
description: 批量抓取推特KOL并生成数字分身。Use /twitter-kol-digital-persona to invoke.
disable-model-invocation: true
---

# Twitter KOL Digital Persona Skill

## 功能概述
本Skill用于批量抓取推特大V历史推文并生成数字分身档案，支持按月分片绕过Twitter深度限制。

## 安装依赖
```bash
# 需要安装 bird CLI（推特抓取工具）
npm install -g @bird/cli
# 或根据实际安装方式配置
```

## 使用方法

### 1. 快速抓取单个KOL
```bash
# 进入工作目录
cd ~/.openclaw/workspace/projects/digital-twin-advisor

# 创建用户目录
mkdir -p USERNAME

# 按月抓取（近12个月）
for month in 2025-03 2025-04 2025-05 2025-06 2025-07 2025-08 2025-09 2025-10 2025-11 2025-12 2026-01 2026-02 2026-03; do
  bird search "from:USERNAME since:${month}-01 until:${month}-01+1month" > "USERNAME/${month}.txt" 2>&1
  sleep 2
done

# 合并所有月份
cat $(ls -r USERNAME/*.txt) > "USERNAME/all_tweets_raw.txt"
```

### 2. 批量抓取多个KOL
```bash
# 编辑用户列表
USERS=("user1" "user2" "user3")

# 运行批量脚本
./crawl_kol_batch.sh
```

### 3. 生成数字分身档案
基于抓取的数据，按照以下框架生成MD文件：
- 基本信息（用户名、昵称、定位）
- 核心投研框架（优先级、必看信息、价值判断）
- 完整交易体系（入场、仓位、止盈止损）
- 个人习惯与能力边界
- 数字分身复用模板

## 数据存储结构
```
twitter_archives/
├── USERNAME/
│   ├── 2025-03.txt      # 月度原始数据
│   ├── 2025-04.txt
│   ├── ...
│   └── all_tweets_raw.txt  # 合并后的完整数据
└── USERNAME_digital_persona.md  # 生成的数字分身档案
```

## 注意事项
1. **Cookie有效性**：bird工具需要有效的Twitter Cookie（auth_token, ct0）
2. **抓取频率**：建议每个查询间隔2-3秒，避免触发限流
3. **数据完整性**：部分账号可能因隐私设置或推文较少导致数据不足
4. **时间范围**：默认抓取近12个月，可根据需要调整

## 故障排查

### 问题：抓取数据为空或极少
**原因**：
- 账号设置了隐私保护
- 账号近期活跃度低
- Cookie失效

**解决**：
- 检查Cookie有效性
- 尝试直接访问该账号主页确认可见性
- 对于数据极少的账号，标记为"数据不足"

### 问题：bird命令报错
**原因**：
- bird未安装或不在PATH中
- 参数格式错误

**解决**：
```bash
# 检查bird是否可用
which bird
bird --version

# 测试单条查询
bird search "from:btcdayu since:2026-01-01 until:2025-02-01"
```

## 扩展功能
- 支持自定义时间范围
- 支持按关键词过滤推文
- 支持导出JSON格式便于程序处理
- 支持增量更新（只抓取新增推文）

## 参考文档
- 原始Prompt模板：`~/.openclaw/workspace/skills/twitter-kol-digital-persona/twitter-crypto+trade-prompt.md`
- 示例档案：`/root/.openclaw/workspace/projects/digital-twin-advisor/twitter_archives/*_digital_persona.md`
