# Docker 部署指南

本指南介绍如何使用 Docker 和 Docker Compose 部署鑫琳医生系统。

## 📋 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

## 🚀 快速开始

### 1. 配置环境变量

复制环境变量模板并修改配置：

```bash
cp .env.docker .env
```

编辑 `.env` 文件，**必须修改以下配置**：

```bash
# 数据库密码（生产环境必须修改）
POSTGRES_PASSWORD=your_secure_password

# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your_jwt_secret_key_here
ADMIN_JWT_SECRET=your_admin_jwt_secret_key_here

# LLM API密钥（必须配置）
LLM_API_KEY=your_qwen_api_key_here
```

### 2. 启动所有服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问服务

- **前端管理后台**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 📦 服务说明

### PostgreSQL 数据库
- **容器名**: `xinlin-postgres`
- **端口**: 5432
- **数据库**: xinlin_prod
- **用户**: xinlin_prod
- **数据持久化**: Docker volume `postgres_data`

### 后端 API 服务
- **容器名**: `xinlin-backend`
- **端口**: 8000
- **框架**: FastAPI + Uvicorn
- **依赖**: PostgreSQL
- **上传文件**: 挂载到 `./backend/uploads`

### 前端 Web 服务
- **容器名**: `xinlin-frontend`
- **端口**: 80
- **服务器**: Nginx
- **反向代理**: `/api/*` → `backend:8000`

## 🔧 常用命令

### 启动和停止

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 重新构建

```bash
# 重新构建所有镜像
docker-compose build

# 重新构建特定服务
docker-compose build backend

# 重新构建并启动
docker-compose up -d --build
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U xinlin_prod -d xinlin_prod

# 进入前端容器
docker-compose exec frontend sh
```

## 🗄️ 数据库管理

### 数据库备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U xinlin_prod xinlin_prod > backup.sql

# 或使用完整命令
docker exec xinlin-postgres pg_dump -U xinlin_prod xinlin_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 数据库恢复

```bash
# 恢复数据库
docker-compose exec -T postgres psql -U xinlin_prod xinlin_prod < backup.sql
```

### 连接数据库

```bash
# 使用psql连接
docker-compose exec postgres psql -U xinlin_prod -d xinlin_prod

# 或从宿主机连接
psql -h localhost -p 5432 -U xinlin_prod -d xinlin_prod
```

## 🔍 健康检查

### 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost
```

### 查看资源使用

```bash
# 查看容器资源使用情况
docker stats

# 查看特定容器
docker stats xinlin-backend xinlin-frontend xinlin-postgres
```

## 🐛 故障排查

### 后端无法连接数据库

1. 检查数据库是否健康：
```bash
docker-compose ps postgres
docker-compose logs postgres
```

2. 检查数据库连接配置：
```bash
docker-compose exec backend env | grep DATABASE_URL
```

3. 手动测试数据库连接：
```bash
docker-compose exec postgres pg_isready -U xinlin_prod
```

### 前端无法访问后端API

1. 检查nginx配置：
```bash
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

2. 检查后端服务：
```bash
curl http://localhost:8000/health
```

3. 查看nginx日志：
```bash
docker-compose logs frontend
```

### 容器启动失败

1. 查看详细日志：
```bash
docker-compose logs [service-name]
```

2. 检查端口占用：
```bash
# macOS/Linux
lsof -i :80
lsof -i :8000
lsof -i :5432

# 或使用
netstat -an | grep LISTEN
```

3. 清理并重新启动：
```bash
docker-compose down -v
docker-compose up -d --build
```

## 🔐 生产环境部署建议

### 安全配置

1. **修改所有默认密码和密钥**
2. **禁用DEBUG模式**: 设置 `DEBUG=false`
3. **配置防火墙**: 只暴露必要的端口（80/443）
4. **使用HTTPS**: 配置SSL证书
5. **限制数据库访问**: 不要暴露5432端口到公网

### 性能优化

1. **调整数据库连接池**
2. **配置nginx缓存**
3. **启用gzip压缩**（已在nginx.conf中配置）
4. **使用CDN加速静态资源**

### 监控和日志

1. **配置日志轮转**
2. **设置资源限制**：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

3. **添加健康检查告警**

### 备份策略

1. **定期备份数据库**（建议每天）
2. **备份环境配置文件**
3. **保存Docker镜像版本**

## 📝 环境变量说明

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| POSTGRES_PASSWORD | PostgreSQL密码 | changeme123 | ✅ |
| JWT_SECRET_KEY | JWT签名密钥 | - | ✅ |
| ADMIN_JWT_SECRET | 管理员JWT密钥 | - | ✅ |
| LLM_API_KEY | 通义千问API密钥 | - | ✅ |
| DEBUG | 调试模式 | false | ❌ |
| SEED_DATA | 是否初始化种子数据 | true | ❌ |
| TEST_MODE | 测试模式 | true | ❌ |
| ENABLE_SMS_VERIFICATION | 启用短信验证 | false | ❌ |

## 🔄 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

## 📞 技术支持

如遇到问题，请：
1. 查看日志：`docker-compose logs -f`
2. 检查容器状态：`docker-compose ps`
3. 查看本文档的故障排查章节
