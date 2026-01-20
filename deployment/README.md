# Home-Health 部署指南

## 自动部署配置

### GitHub Secrets 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `DEPLOY_HOST` | 服务器 IP 地址 | `123.206.232.231` |
| `DEPLOY_USER` | SSH 用户名 | `root` |
| `DEPLOY_KEY` | SSH 私钥内容 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `POSTGRES_USER` | 数据库用户名 | `postgres` |
| `POSTGRES_PASSWORD` | 数据库密码 | `your_password` |
| `POSTGRES_DB` | 数据库名称 | `home_health` |
| `JWT_SECRET_KEY` | JWT 密钥 | 随机字符串 |
| `LLM_API_KEY` | 通义千问 API Key | `sk-xxx` |
| `ALIYUN_SMS_ACCESS_KEY_ID` | 阿里云 AccessKey ID | `LTAI5xxx` |
| `ALIYUN_SMS_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret | `xxx` |

### 获取 SSH 私钥

```bash
# 读取私钥内容（复制到 GitHub Secrets）
cat xinlingyisheng.pem
```

### 部署流程

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Git Push      │ -> │ GitHub Actions    │ -> │ ghcr.io 镜像    │
│   main/develop  │    │ 构建 & 推送镜像   │    │ 存储            │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       │
                                                       v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   健康检查       │ <- │ SSH 远程部署      │ <- │ 服务器拉取镜像  │
│                 │    │ docker-compose up│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 手动部署

使用提供的部署脚本：

```bash
cd deployment

# 首次部署
./deploy.sh

# 指定镜像标签
IMAGE_TAG=main-abc1234 ./deploy.sh
```

### 环境变量

复制 `.env.example` 到服务器：

```bash
scp xinlingyisheng.pem root@123.206.232.231:/opt/home-health/
scp .env.example root@123.206.232.231:/opt/home-health/.env
```

### SSL 证书（可选）

如需启用 HTTPS，将证书文件放到 `ssl/` 目录：

```
deployment/
├── ssl/
│   ├── nginx.crt    # SSL 证书
│   └── nginx.key    # 私钥
```

### 服务访问

| 服务 | 地址 |
|------|------|
| 前端 | http://123.206.232.231/ |
| 后端 API | http://123.206.232.231:8100/ |
| API 文档 | http://123.206.232.231:8100/docs |

### 故障排查

```bash
# 查看服务状态
ssh -i xinlingyisheng.pem root@123.206.232.231
cd /opt/home-health
docker compose ps

# 查看日志
docker compose logs backend
docker compose logs frontend

# 重启服务
docker compose restart backend
```
