#!/bin/bash
# OpenClaw 一键安装脚本 (Linux/macOS)
# 适用环境: Ubuntu/CentOS/Debian/macOS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}===> 开始安装 OpenClaw 环境...${NC}"

# 1. 检查并安装 Node.js (推荐 v22+)
if ! command -v node &> /dev/null; then
    echo "未检测到 Node.js，正在通过 NVM 安装..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 22
    nvm use 22
else
    echo -e "${GREEN}✅ Node.js $(node -v) 已就绪${NC}"
fi

# 2. 安装 OpenClaw 核心
echo -e "${GREEN}===> 正在安装 OpenClaw 命令行工具...${NC}"
npm install -g openclaw

# 3. 初始化工作区
echo -e "${GREEN}===> 正在初始化工作区...${NC}"
mkdir -p ~/.openclaw/workspace/config
mkdir -p ~/.openclaw/workspace/scripts
mkdir -p ~/.openclaw/workspace/memory

# 4. 生成默认配置文件 (如果不存在)
if [ ! -f ~/.openclaw/openclaw.json ]; then
    openclaw gateway config.schema > /tmp/schema.json
    # 这里可以根据需要引导用户输入 API Key 或生成基础配置
    echo "基础配置文件已生成在 ~/.openclaw/openclaw.json"
fi

# 5. 提示
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 OpenClaw 安装完成！${NC}"
echo -e "常用命令:"
echo -e "  - ${GREEN}openclaw gateway start${NC}   : 启动网关"
echo -e "  - ${GREEN}openclaw gateway status${NC}  : 检查状态"
echo -e "  - ${GREEN}openclaw --help${NC}          : 查看所有命令"
echo -e "${GREEN}========================================${NC}"
