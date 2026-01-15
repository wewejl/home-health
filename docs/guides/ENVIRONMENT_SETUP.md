# 环境配置指南

**版本**: V1.0  
**更新日期**: 2026-01-15  
**适用范围**: 全项目开发环境配置

---

## 目录

1. [系统要求](#系统要求)
2. [后端环境配置](#后端环境配置)
3. [前端环境配置](#前端环境配置)
4. [iOS 环境配置](#ios-环境配置)
5. [Docker 环境配置](#docker-环境配置)
6. [常见问题](#常见问题)

---

## 系统要求

### 开发机器要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| macOS | 13.0 (Ventura) | 14.0+ (Sonoma) |
| Python | 3.10 | 3.11+ |
| Node.js | 18.0 | 20.0+ |
| Xcode | 15.0 | 16.0+ |
| Docker | 24.0 | 25.0+ |

---

## 后端环境配置

### 1. 安装 Python 虚拟环境

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制示例文件并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下配置：

```env
# ==================== 数据库配置 ====================
DATABASE_URL=sqlite:///./app.db

# ==================== JWT 配置 ====================
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
ADMIN_JWT_SECRET=your-admin-secret-key-change-in-production

# ==================== LLM 配置 ====================
LLM_PROVIDER=qwen
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-your-api-key-here
LLM_TEMPERATURE=0.7

# ==================== 服务配置 ====================
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 4. 初始化数据库

```bash
python -m app.seed
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 验证

访问 API 文档确认服务正常：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 前端环境配置

### 1. 安装 Node.js 依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
touch .env
```

添加以下内容：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 验证

访问 http://localhost:5173 确认前端正常运行。

---

## iOS 环境配置

### 1. 打开项目

使用 Xcode 打开项目：

```bash
open ios/xinlingyisheng/xinlingyisheng.xcodeproj
```

### 2. 配置 API 地址

编辑 `ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`：

```swift
struct APIConfig {
    // 开发环境
    #if DEBUG
    static let baseURL = "http://localhost:8000"
    #else
    // 生产环境
    static let baseURL = "https://api.your-domain.com"
    #endif
}
```

### 3. 配置签名

1. 选择项目 → Signing & Capabilities
2. 选择你的开发团队
3. 确保 Bundle Identifier 唯一

### 4. 选择模拟器或设备

1. 选择目标设备（iPhone 15 Pro 推荐）
2. 点击运行 (⌘+R)

### 注意事项

- 模拟器访问本机后端使用 `localhost`
- 真机测试需要使用电脑的 IP 地址

```swift
// 真机测试时修改为电脑 IP
static let baseURL = "http://192.168.x.x:8000"
```

---

## Docker 环境配置

### 1. 配置 Docker 环境变量

项目根目录的 `.env.docker` 文件：

```env
# 数据库
DATABASE_URL=sqlite:///./app.db

# JWT
JWT_SECRET_KEY=docker-secret-key
ADMIN_JWT_SECRET=docker-admin-secret

# LLM
LLM_PROVIDER=qwen
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-your-api-key

# 服务配置
HOST=0.0.0.0
PORT=8000
```

### 2. 启动所有服务

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

### 服务访问地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| 前端管理后台 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |

---

## 环境变量说明

### 必填配置

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./app.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 随机字符串，32位以上 |
| `LLM_API_KEY` | 大模型 API 密钥 | `sk-xxxx` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `qwen` |
| `LLM_MODEL` | 模型名称 | `qwen-plus` |
| `LLM_TEMPERATURE` | 生成温度 | `0.7` |
| `DEBUG` | 调试模式 | `false` |
| `PORT` | 服务端口 | `8000` |

---

## 常见问题

### Q1: 后端启动报错 "ModuleNotFoundError"

**原因**: 虚拟环境未激活或依赖未安装

**解决**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Q2: iOS 无法连接后端

**原因**: 网络配置问题

**解决**:
1. 确认后端服务正在运行
2. 模拟器使用 `localhost`，真机使用电脑 IP
3. 检查防火墙设置

### Q3: LLM API 调用失败

**原因**: API Key 无效或余额不足

**解决**:
1. 检查 `.env` 中的 `LLM_API_KEY`
2. 登录阿里云控制台确认服务状态
3. 检查 API 调用配额

### Q4: 前端显示空白页面

**原因**: 后端服务未启动或 CORS 配置问题

**解决**:
1. 确认后端服务正在运行
2. 检查浏览器控制台错误信息
3. 确认 `VITE_API_BASE_URL` 配置正确

### Q5: Docker 容器启动失败

**原因**: 端口冲突或资源不足

**解决**:
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 停止占用端口的进程
kill -9 <PID>

# 重新启动
docker-compose up -d
```

---

## 快速启动脚本

### 一键启动所有服务 (开发环境)

创建 `scripts/dev-start.sh`:

```bash
#!/bin/bash

# 启动后端
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 启动前端
cd ../frontend
npm run dev &

echo "✅ 服务已启动"
echo "   后端: http://localhost:8000"
echo "   前端: http://localhost:5173"
echo "   API文档: http://localhost:8000/docs"
```

### 停止所有服务

```bash
#!/bin/bash
pkill -f "uvicorn"
pkill -f "vite"
echo "✅ 所有服务已停止"
```

---

**文档维护人**: 开发团队  
**最后更新**: 2026-01-15
