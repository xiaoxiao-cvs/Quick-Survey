# Quick-Survey 部署指南

## 📋 部署步骤概览

1. 本地构建前端和打包后端
2. 上传到服务器
3. 配置后端服务 (systemd)
4. 配置前端 (Nginx)

---

## 🏠 本地操作

### 1. 构建前端

```bash
cd frontend
pnpm install
pnpm build
# 构建产物在 frontend/dist 目录
```

### 2. 打包后端

```bash
# 运行打包脚本
./deploy/pack.sh
# 或者手动打包
cd backend
tar -czvf ../deploy/backend.tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='data/*.db' \
    .
```

### 3. 上传到服务器

```bash
# 上传后端包
scp deploy/backend.tar.gz user@your-server:/opt/quick-survey/

# 上传前端构建产物
scp -r frontend/dist/* user@your-server:/var/www/quick-survey/
```

---

## 🖥️ 服务器操作

### 1. 安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip nginx

# CentOS/RHEL
sudo dnf install python3.11 python3.11-venv nginx
```

### 2. 部署后端

```bash
# 创建目录
sudo mkdir -p /opt/quick-survey
cd /opt/quick-survey

# 解压后端
tar -xzvf backend.tar.gz

# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data uploads

# 修改配置文件
cp config.example.yml config.yml
nano config.yml  # 编辑配置
```

### 3. 配置 systemd 服务

```bash
# 复制服务文件
sudo cp /opt/quick-survey/deploy/quick-survey.service /etc/systemd/system/

# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start quick-survey

# 设置开机自启
sudo systemctl enable quick-survey

# 查看状态
sudo systemctl status quick-survey

# 查看日志
sudo journalctl -u quick-survey -f
```

### 4. 配置 Nginx

```bash
# 复制配置文件
sudo cp /opt/quick-survey/deploy/nginx.conf /etc/nginx/sites-available/quick-survey

# 启用站点
sudo ln -s /etc/nginx/sites-available/quick-survey /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 🔧 常用命令

### 服务管理

```bash
# 启动/停止/重启
sudo systemctl start quick-survey
sudo systemctl stop quick-survey
sudo systemctl restart quick-survey

# 查看状态
sudo systemctl status quick-survey

# 查看日志
sudo journalctl -u quick-survey -f
sudo journalctl -u quick-survey --since "1 hour ago"
```

### 更新部署

```bash
# 更新后端
cd /opt/quick-survey
sudo systemctl stop quick-survey
tar -xzvf backend.tar.gz
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start quick-survey

# 更新前端
sudo cp -r /path/to/dist/* /var/www/quick-survey/
```

---

## ⚙️ 配置说明

### 后端配置 (config.yml)

```yaml
server:
  host: "127.0.0.1"  # 生产环境只监听本地，由 Nginx 代理
  port: 8000
  debug: false        # 生产环境关闭 debug

cors:
  allowed_origins: ["https://your-domain.com"]  # 设置实际域名
```

### Nginx 配置

- 前端静态文件目录: `/var/www/quick-survey/`
- 后端 API 代理: `/api/` -> `http://127.0.0.1:8000`
- 上传文件代理: `/uploads/` -> `http://127.0.0.1:8000/uploads/`

---

## 🔒 安全建议

1. **防火墙**: 只开放 80/443 端口，后端 8000 端口只允许本地访问
2. **HTTPS**: 使用 Let's Encrypt 配置 SSL 证书
3. **权限**: 使用非 root 用户运行服务
4. **配置**: 确保 `config.yml` 文件权限为 600

```bash
# 配置 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```
