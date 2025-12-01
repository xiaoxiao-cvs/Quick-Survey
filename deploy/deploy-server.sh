#!/bin/bash
# Quick-Survey 服务器部署脚本
# 在服务器上运行此脚本进行首次部署
# 使用方法: sudo ./deploy-server.sh

set -e

echo "🚀 Quick-Survey 服务器部署脚本"
echo "================================"
echo ""

# 检查是否为 root 或 sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 配置变量
BACKEND_DIR="/opt/quick-survey"
FRONTEND_DIR="/var/www/quick-survey"
SERVICE_USER="www-data"

# 创建目录
echo "📁 创建目录..."
mkdir -p "$BACKEND_DIR"
mkdir -p "$FRONTEND_DIR"

# 检查包文件是否存在
if [ ! -f "backend.tar.gz" ]; then
    echo "❌ 找不到 backend.tar.gz，请先上传后端包"
    exit 1
fi

if [ ! -f "frontend.tar.gz" ]; then
    echo "❌ 找不到 frontend.tar.gz，请先上传前端包"
    exit 1
fi

# 部署后端
echo ""
echo "🐍 部署后端..."
cd "$BACKEND_DIR"
tar -xzvf /path/to/backend.tar.gz  # 修改为实际路径

# 创建虚拟环境
echo "🔧 创建 Python 虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 创建数据目录
mkdir -p data uploads
chown -R $SERVICE_USER:$SERVICE_USER data uploads

# 部署前端
echo ""
echo "🌐 部署前端..."
cd "$FRONTEND_DIR"
tar -xzvf /path/to/frontend.tar.gz  # 修改为实际路径
chown -R $SERVICE_USER:$SERVICE_USER "$FRONTEND_DIR"

# 安装 systemd 服务
echo ""
echo "⚙️  安装 systemd 服务..."
cp "$BACKEND_DIR/deploy/quick-survey.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable quick-survey

# 安装 Nginx 配置
echo ""
echo "🌍 配置 Nginx..."
cp "$BACKEND_DIR/deploy/nginx.conf" /etc/nginx/sites-available/quick-survey
ln -sf /etc/nginx/sites-available/quick-survey /etc/nginx/sites-enabled/

# 测试 Nginx 配置
nginx -t

# 启动服务
echo ""
echo "🚀 启动服务..."
systemctl start quick-survey
systemctl reload nginx

echo ""
echo "================================"
echo "✅ 部署完成！"
echo ""
echo "📋 后续步骤:"
echo "1. 编辑配置文件: nano $BACKEND_DIR/config.yml"
echo "2. 编辑 Nginx 配置，设置域名: nano /etc/nginx/sites-available/quick-survey"
echo "3. 重启服务: systemctl restart quick-survey && systemctl reload nginx"
echo "4. 配置 HTTPS: certbot --nginx -d your-domain.com"
echo ""
echo "🔍 检查服务状态:"
echo "  systemctl status quick-survey"
echo "  journalctl -u quick-survey -f"
echo ""
