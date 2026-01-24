# 服务器部署配置

**项目:** 灵犀医生 (Home-Health)
**最后更新:** 2026-01-22
**版本:** 2.0.0

---

## 快速部署

### 第一步：本地配置

在项目根目录编辑 `.env.production` 文件：

```bash
# 复制模板（如果还没有）
cp .env.production.example .env.production

# 编辑配置，填入真实的密钥
vi .env.production
```

**必须修改的配置项：**
- `POSTGRES_PASSWORD` - 数据库密码
- `JWT_SECRET_KEY` - JWT 密钥（强随机）
- `ADMIN_JWT_SECRET` - Admin JWT 密钥（强随机）
- `LLM_API_KEY` - 阿里云 API 密钥
- `SMS_ACCESS_KEY_ID` - 短信服务 Key ID
- `SMS_ACCESS_KEY_SECRET` - 短信服务密钥

### 第二步：部署到服务器

```bash
# 方式一：使用自动化部署脚本（推荐）
./scripts/deploy.sh production

# 方式二：手动部署
# 1. 推送代码到 git
git add .env.production  # 仅首次需要
git commit -m "chore: update production config"
git push origin main

# 2. SSH 登录服务器
ssh -i xinlingyisheng.pem ubuntu@123.206.232.231

# 3. 拉取代码并启动
cd /opt/home-health/source
git pull origin main
cd /opt/home-health
sudo docker-compose up -d --build
```

---

## 配置文件说明

Docker Compose 启动时会自动按以下顺序加载配置：

| 优先级 | 文件 | 说明 |
|--------|------|------|
| 1 | `.env.production` | 生产环境配置（本地配置，随代码部署） |
| 2 | `.env` | 默认配置 |
| 3 | 默认值 | docker-compose.yml 中的默认值 |

**配置加载流程：**
1. 你在本地编辑 `.env.production`
2. Git 推送到服务器
3. 服务器上 `docker-compose up` 自动加载 `.env.production`

---

## 服务器信息

| 配置项 | 值 |
|--------|-----|
| 服务器IP | `123.206.232.231` |
| 用户名 | `ubuntu` |
| 密钥文件 | `xinlingyisheng.pem` (项目根目录) |
| 部署方式 | Docker Compose |

---

## SSH 连接

### 快速连接

```bash
ssh -i xinlingyisheng.pem ubuntu@123.206.232.231
```

### 从项目目录连接

```bash
cd /Users/zhuxinye/Desktop/project/home-health
ssh -i xinlingyisheng.pem ubuntu@123.206.232.231
```

---

## 项目部署路径

```
/opt/home-health/           # 项目根目录
├── source/                 # 源代码目录
│   ├── backend/           # 后端代码
│   ├── frontend/          # 前端代码
│   ├── .env               # 环境配置
│   └── app.db             # SQLite数据库
├── data/                   # 数据持久化
├── docker-compose.yml      # Docker编排文件
└── .env                    # Docker环境变量
```

---

## Docker 服务管理

### 查看容器状态

```bash
cd /opt/home-health
sudo docker ps
```

### 启动所有服务

```bash
cd /opt/home-health
sudo docker-compose up -d
```

### 停止所有服务

```bash
cd /opt/home-health
sudo docker-compose down
```

### 重启服务

```bash
cd /opt/home-health
sudo docker-compose restart

# 或重启单个服务
sudo docker-compose restart backend
sudo docker-compose restart frontend
```

### 查看服务日志

```bash
# 查看所有服务日志
sudo docker-compose logs -f

# 查看后端日志
sudo docker-compose logs -f backend

# 查看前端日志
sudo docker-compose logs -f frontend
```

### 进入容器

```bash
# 进入后端容器
sudo docker exec -it home-health-backend bash

# 进入数据库容器
sudo docker exec -it home-health-postgres psql -U postgres -d home_health
```

---

## 代码部署

### 方式一：在服务器上拉取代码

```bash
ssh -i xinlingyisheng.pem ubuntu@123.206.232.231

cd /opt/home-health/source
git pull origin main

# 重建并重启容器
cd /opt/home-health
sudo docker-compose up -d --build
```

### 方式二：本地推送后服务器拉取

```bash
# 本地执行
git push origin main

# 然后在服务器上执行上述命令
```

---

## 服务端口

| 服务 | 容器端口 | 对外端口 | 说明 |
|------|---------|---------|------|
| 后端API | 8100 | - (内部) | Docker容器内 |
| 前端界面 | 80 | 80 | Nginx反向代理 |
| API代理路径 | - | /api/* | 80端口 /api/* → 后端8100 |
| PostgreSQL | 5432 | - (内部) | Docker网络 |
| Redis | 6379 | - (内部) | Docker网络 |

**重要:** 防火墙只开放 80 端口，8100 端口不对外开放。所有API请求通过 80 端口的 Nginx 反向代理访问。

---

## 生产环境配置

### Docker配置 (/opt/home-health/.env)

```bash
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=home_health_pass_2024
POSTGRES_DB=home_health

# JWT 密钥
JWT_SECRET_KEY=home_health_secret_key_2024_hxl
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# 测试模式
TEST_MODE=false
ENABLE_SMS_VERIFICATION=false
```

### 后端配置 (/opt/home-health/source/.env)

需要根据实际情况配置：
- LLM API Key
- 短信服务配置
- 其他第三方服务

---

## Nginx 反向代理配置

### 代理规则

前端容器内的 Nginx 配置了以下代理规则：

```nginx
# 管理后台 API 代理
location /api/ {
    proxy_pass http://home-health-backend:8100/;
}

# iOS 患者端 API 代理（精确匹配优先）
location = /auth { proxy_pass http://home-health-backend:8100/auth; }
location = /sessions { proxy_pass http://home-health-backend:8100/sessions; }
location = /departments { proxy_pass http://home-health-backend:8100/departments; }
location = /diseases { proxy_pass http://home-health-backend:8100/diseases; }
location = /drugs { proxy_pass http://home-health-backend:8100/drugs; }
location = /medical-events { proxy_pass http://home-health-backend:8100/medical-events; }
location /ai { proxy_pass http://home-health-backend:8100/ai; }
location /v2 { proxy_pass http://home-health-backend:8100/v2; }

# 子路径代理
location /auth/ { proxy_pass http://home-health-backend:8100/auth/; }
location /sessions/ { proxy_pass http://home-health-backend:8100/sessions/; }
# ... 其他路径
```

### 访问方式

| 客户端 | URL示例 |
|--------|---------|
| 管理后台 | `http://123.206.232.231/` |
| API请求 | `http://123.206.232.231/api/auth/login` |
| iOS患者端 | `http://123.206.232.231/api/sessions` |
| 语音转写 | `http://123.206.232.231/api/v1/transcriptions` |

### 更新Nginx配置

```bash
# 进入前端容器
sudo docker exec -it home-health-frontend bash

# 编辑配置
vi /etc/nginx/conf.d/default.conf

# 退出并重启Nginx
exit
sudo docker restart home-health-frontend
```

---

## 数据库管理

### 连接数据库

```bash
# 方式1: 进入容器
sudo docker exec -it home-health-postgres psql -U postgres -d home_health

# 方式2: 直接用 psql
psql -h 123.206.232.231 -U postgres -d home_health
```

### 备份数据库

```bash
sudo docker exec home-health-postgres pg_dump -U postgres home_health > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
sudo docker exec -i home-health-postgres psql -U postgres home_health < backup_20260122.sql
```

---

## 日志查看

### Docker 日志

```bash
# 实时查看所有日志
sudo docker-compose logs -f

# 查看最近100行
sudo docker-compose logs --tail=100

# 查看特定服务
sudo docker-compose logs -f backend
sudo docker-compose logs -f frontend
```

### 容器内日志

```bash
# 进入后端容器查看
sudo docker exec -it home-health-backend bash
ls -la logs/
```

---

## 常用命令速查

```bash
# === 连接服务器 ===
ssh -i xinlingyisheng.pem ubuntu@123.206.232.231

# === 进入项目目录 ===
cd /opt/home-health

# === 查看容器状态 ===
sudo docker ps

# === 重启服务 ===
sudo docker-compose restart

# === 查看日志 ===
sudo docker-compose logs -f backend

# === 更新代码 ===
cd /opt/home-health/source && git pull
cd /opt/home-health && sudo docker-compose up -d --build

# === 系统资源 ===
htop
df -h
free -h
```

---

## 容器信息

| 容器名 | 镜像 | 状态 |
|--------|------|------|
| home-health-frontend | nginx:alpine | 运行中 (端口80) |
| home-health-backend | python:3.12-slim | 运行中 (端口8100) |
| home-health-postgres | postgres:16-alpine | 运行中 |
| home-health-redis | redis:7-alpine | 运行中 |

---

## 健康检查与监控

### 健康检查端点

| 端点 | 用途 |
|------|------|
| `/api/health` | 基础健康检查 |
| `/api/health/detailed` | 详细健康状态（含数据库、LLM） |
| `/api/health/ready` | 就绪检查（Kubernetes） |
| `/api/health/live` | 存活检查（Kubernetes） |

### 监控命令

```bash
# 基础健康检查
curl http://123.206.232.231/api/health

# 详细健康状态
curl http://123.206.232.231/api/health/detailed | jq

# 持续监控
watch -n 5 'curl -s http://123.206.232.231/api/health/detailed | jq'
```

### 详细健康状态响应示例

```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T10:00:00",
  "version": "2.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "llm": {"status": "configured", "provider": "qwen"}
  },
  "environment": {
    "debug": false,
    "test_mode": false,
    "cors_origins_configured": true
  },
  "response_time_ms": 15.23
}
```

---

## 故障排查

### 服务无法启动

```bash
# 1. 检查容器状态
sudo docker ps -a

# 2. 查看失败容器日志
sudo docker logs <container_id>

# 3. 检查端口占用
netstat -tlnp | grep 8100
```

### 代码更新不生效

```bash
# 强制重建镜像
cd /opt/home-health
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

### 数据库连接问题

```bash
# 检查数据库容器状态
sudo docker ps | grep postgres

# 测试连接
sudo docker exec -it home-health-postgres psql -U postgres -c "SELECT 1;"
```

---

## 安全建议

- [x] CORS 配置限制为特定域名
- [x] JWT 密钥使用强随机值
- [x] 敏感配置不提交到 Git
- [ ] 配置 HTTPS/SSL 证书
- [ ] 定期更新系统和 Docker 镜像
- [ ] 配置防火墙规则 (只开放 80, 443, 22)
- [ ] 定期备份数据库
- [ ] 监控容器资源使用

---

## 部署前检查清单

### 配置文件

- [ ] `backend/.env.production` 已创建并配置
- [ ] `JWT_SECRET_KEY` 已设置为强随机值
- [ ] `ADMIN_JWT_SECRET` 已设置为不同的强随机值
- [ ] `LLM_API_KEY` 已配置
- [ ] `CORS_ALLOWED_ORIGINS` 已设置正确的域名
- [ ] 短信服务配置已填写（如需要）

### 代码检查

- [ ] 本地测试通过
- [ ] 代码已提交到 Git
- [ ] iOS 代码编译通过

### 服务器检查

- [ ] SSH 密钥文件可访问
- [ ] 服务器磁盘空间充足
- [ ] 数据库备份计划已确认

---

## 部署后验证

部署完成后，请验证以下功能：

```bash
# 1. 检查容器状态
sudo docker ps

# 2. 检查健康状态
curl http://localhost/api/health/detailed

# 3. 检查前端访问
curl http://localhost/

# 4. 检查 API 连通
curl http://localhost/api/auth/login
```
