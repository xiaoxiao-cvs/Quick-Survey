#!/bin/bash
# Quick-Survey 打包脚本
# 在项目根目录运行: ./deploy/pack.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📦 Quick-Survey 打包脚本"
echo "========================"
echo ""

# 创建输出目录
OUTPUT_DIR="$SCRIPT_DIR/output"
mkdir -p "$OUTPUT_DIR"

# 打包后端
echo "🐍 打包后端..."
cd "$PROJECT_ROOT/backend"
tar -czvf "$OUTPUT_DIR/backend.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='data/*.db' \
    --exclude='data/survey.db' \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='.vscode' \
    --exclude='*.log' \
    .

echo "✅ 后端打包完成: $OUTPUT_DIR/backend.tar.gz"

# 构建前端
echo ""
echo "🏗️  构建前端..."
cd "$PROJECT_ROOT/frontend"

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo "📥 安装前端依赖..."
    pnpm install
fi

pnpm build

# 打包前端构建产物
echo "📦 打包前端构建产物..."
cd dist
tar -czvf "$OUTPUT_DIR/frontend.tar.gz" .

echo "✅ 前端打包完成: $OUTPUT_DIR/frontend.tar.gz"

# 复制部署配置文件
echo ""
echo "📋 复制部署配置文件..."
cp "$SCRIPT_DIR/quick-survey.service" "$OUTPUT_DIR/"
cp "$SCRIPT_DIR/nginx.conf" "$OUTPUT_DIR/"
cp "$SCRIPT_DIR/README.md" "$OUTPUT_DIR/"

echo ""
echo "========================"
echo "✅ 打包完成！"
echo ""
echo "输出目录: $OUTPUT_DIR"
echo ""
echo "包含文件:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "📤 上传到服务器:"
echo "  scp $OUTPUT_DIR/backend.tar.gz user@server:/opt/quick-survey/"
echo "  scp $OUTPUT_DIR/frontend.tar.gz user@server:/var/www/"
echo ""
