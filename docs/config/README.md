# 项目配置文档总览

**项目:** 灵犀医生 (Home-Health)
**最后更新:** 2026-01-22

---

## 配置文档索引

| 文档 | 说明 |
|------|------|
| [短信服务配置](./sms-service.md) | 阿里云号码认证服务配置 |
| [服务器部署](./deployment.md) | 服务器连接和部署配置 |
| [API接口文档](../API_CONTRACT.md) | 后端API接口定义 |
| [开发指南](../DEVELOPMENT_GUIDELINES.md) | 代码规范和开发流程 |
| [iOS开发指南](../IOS_DEVELOPMENT_GUIDE.md) | iOS客户端开发规范 |

---

## 快速配置清单

### 后端配置 (backend/.env.local)

```bash
# 数据库
DATABASE_URL=postgresql+psycopg://xinlin_prod:wszxy123@localhost:5432/xinlin_prod

# JWT认证
JWT_SECRET_KEY=xinlin-doctor-secret-key-2024

# LLM配置 (通义千问)
LLM_API_KEY=sk-61e2b328d6614408867ac61240423740
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
QWEN_VL_MODEL=qwen3-vl-plus

# 短信服务
SMS_PROVIDER=aliyun
SMS_ACCESS_KEY_ID=[从阿里云控制台获取]
SMS_ACCESS_KEY_SECRET=[从阿里云控制台获取]
SMS_SIGN_NAME=速通互联验证码
SMS_TEMPLATE_CODE=100001

# 功能开关
ENABLE_SMS_VERIFICATION=true
TEST_MODE=true  # 生产环境改为 false
```

### iOS客户端配置 (ios/xinlingyisheng/.../APIConfig.swift)

```swift
// API服务 (通过80端口Nginx代理)
static let baseURL = "http://123.206.232.231/api"

// 语音转写服务
static let baseURL = "http://123.206.232.231/api/v1"
```

**注意:** iOS 客户端通过 **80端口 + /api/** 路径访问服务器（Nginx代理到后端8100）

---

## 默认凭证

| 服务 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 后端管理员 | admin | admin123 | 管理后台登录 |
| 测试Token | test_1 | - | API测试用 (userId=1) |
| 服务器SSH | ubuntu | 密钥文件 `xinlingyisheng.pem` | 生产服务器 |

---

## 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端API (容器) | **8100** | Docker容器内部端口 |
| 服务器入口 | **80** | Nginx反向代理 |
| API访问路径 | `/api/*` | Nginx代理到后端8100 |
| 服务器地址 | `123.206.232.231` | 生产环境 |
| 前端管理后台 | 5173 | Vite Dev Server |
| 前端生产环境 | 80 | 服务器: 123.206.232.231 |
| iOS模拟器 | - | Xcode |

**重要说明:**
- 后端容器运行在 8100 端口，但防火墙未开放此端口
- 所有外部访问通过 **80端口 Nginx 反向代理**
- API请求路径: `http://123.206.232.231/api/*` → Nginx → `http://home-health-backend:8100/*`

---

## 数据库Schema

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| doctors | 医生分身表 |
| sessions | 会话记录表 (统一，支持多科室) |
| messages | 消息记录表 |
| knowledge_bases | 知识库表 |
| diseases | 疾病数据表 (1701条) |
| drugs | 药品数据表 (641条) |

---

## 外部服务

| 服务 | 提供商 | 用途 |
|------|--------|------|
| LLM | 阿里云通义千问 | AI对话 |
| 多模态 | 阿里云 Qwen-VL | 图像识别 |
| 短信 | 阿里云号码认证 | 验证码发送 |

---

## 项目结构速查

```
home-health/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── routes/       # API路由
│   │   ├── services/     # 业务逻辑
│   │   │   └── agents/   # AI智能体
│   │   ├── models/       # 数据库模型
│   │   └── config.py     # 配置文件
│   └── .env.local        # 本地配置 (敏感信息)
├── frontend/             # React 管理后台
│   └── src/
│       ├── pages/        # 页面组件
│       └── api/          # API调用
├── ios/                  # SwiftUI 客户端
│   └── xinlingyisheng/
│       ├── Services/     # API服务
│       ├── ViewModels/   # MVVM视图模型
│       └── Views/        # UI视图
└── docs/                 # 项目文档
    ├── config/           # 配置文档 (本目录)
    ├── plans/            # 开发计划
    └── API_CONTRACT.md   # API文档
```

---

## 查找问题

当你需要查找某个配置时：

1. **服务配置** → 查看 `docs/config/` 目录
2. **API定义** → 查看 `docs/API_CONTRACT.md`
3. **开发问题** → 查看 `docs/DEVELOPMENT_GUIDELINES.md`
4. **iOS问题** → 查看 `docs/IOS_DEVELOPMENT_GUIDE.md`
5. **代码中的配置** → 查看 `backend/app/config.py`
6. **本地敏感配置** → 查看 `backend/.env.local` (不提交Git)
