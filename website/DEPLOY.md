# 服务器部署指南

## 部署架构

```
外网用户 → natapp (xinling.natapp1.cc) → 本地 3344 端口 → Docker 容器 (nginx)
```

## 前置要求

服务器需要安装：
- Docker
- Docker Compose

## 部署步骤

### 1. 上传文件到服务器

```bash
# 在本地，将整个 website 目录上传到服务器
scp -r website/ user@your-server:/path/to/deploy/
```

### 2. 下载 natapp

在服务器上下载 natapp：

```bash
cd /path/to/deploy/website

# Linux 64位
wget https://cdn.natapp.cn/assets/download/natapp_linux_amd64_3.2.3.zip -O natapp.zip
unzip natapp.zip
mv natapp ./
chmod +x natapp
```

### 3. 部署启动

```bash
chmod +x deploy.sh stop.sh
./deploy.sh
```

### 4. 访问网站

- 本地: http://localhost:3344
- 外网: http://xinling.natapp1.cc

## 常用命令

### 查看服务状态
```bash
# Docker 容器状态
docker ps

# natapp 运行状态
ps aux | grep natapp
```

### 查看日志
```bash
# Docker 日志
docker logs -f lingxi-health-website

# natapp 日志
tail -f natapp.log
```

### 重启服务
```bash
./deploy.sh
```

### 停止服务
```bash
./stop.sh
```

## natapp 配置说明

当前使用的 authtoken: `e8fdfa13885d4594`

隧道配置需要在 natapp 控制台配置：
- 隧道协议: HTTP
- 本地端口: 3344
- 域名: xinling.natapp1.cc

## 故障排查

### 容器无法启动
```bash
# 查看详细日志
docker logs lingxi-health-website

# 重新构建
docker compose up -d --build
```

### natapp 无法连接
```bash
# 检查 natapp 日志
cat natapp.log

# 手动测试 natapp
./natapp --authtoken=e8fdfa13885d4594
```

### 端口冲突
如果 3344 端口被占用，修改 `docker-compose.yml` 中的端口映射。
