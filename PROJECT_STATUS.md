# 项目进度与上线待办

## 1. 进度总览

| 模块 | 完成度 | 核心功能 | 状态 |
|------|--------|----------|------|
| 后端 API | 85% | 用户认证、AI 诊断、科室/医生/疾病/药品管理、CrewAI 多智能体 | ✅ 可用 |
| 管理后台 | 80% | 登录、仪表盘、科室/医生/疾病/药品/知识库/反馈管理 | ✅ 可用 |
| iOS App | 75% | 登录、首页、问医生、查病查药、个人中心、AI 诊断 | ⚠️ 部分待完善 |

## 2. 上线前待办清单

### 2.1 安全与合规（高优先级）

| 任务 | 当前状态 | 行动项 | 影响 |
|------|---------|--------|------|
| 账号+密码登录 | ✅ 已完成 | 已实现密码字段、bcrypt哈希、注册/登录/重置密码接口 | 已可用 |
| JWT 密钥更换 | ⚠️ 示例密钥 | `.env` 中更换 `JWT_SECRET_KEY`、`ADMIN_JWT_SECRET` 为强随机字符串 | 安全风险 |
| HTTPS 部署 | ❌ 未配置 | 配置 SSL 证书并强制 HTTPS | 明文传输不安全 |
| CORS 策略收紧 | ⚠️ `*` | 仅允许前端与 iOS 正式域名 | 跨域攻击风险 |
| 用户协议/隐私政策 | ❌ 占位链接 | 编写正式协议并在 iOS 登录页更新链接 | 法律合规 |

### 2.2 数据库与存储（高优先级）

| 任务 | 当前状态 | 行动项 | 影响 |
|------|---------|--------|------|
| 生产数据库 | ⚠️ SQLite | 迁移 PostgreSQL/MySQL，配置连接池与备份 | SQLite 不适合生产 |
| 向量数据库 | ❌ 未集成 | 接入 pgvector/Milvus 以增强 RAG 检索 | 知识检索准确率 |
| 数据备份方案 | ❌ 无 | 建立数据库与文件定时备份，异地存储 | 数据丢失风险 |
| 文件存储 | ⚠️ 本地 | 迁移 OSS/S3 存储头像与皮肤图片 | 扩展性差 |

### 2.3 功能完善（中优先级）

| 模块 | 任务 | 当前状态 | 行动项 |
|------|------|---------|--------|
| iOS 用户模块 | 资料完善流程 | ✅ 已完成 | `ContentView` 已监听 `needsProfileSetup` 并自动弹出 `ProfileSetupView` |
| iOS 用户模块 | 个人中心菜单 | ❌ 空操作 | 实现诊疗记录、设置、资料编辑导航 |
| iOS 用户模块 | 头像上传 | ❌ 未实现 | 接入图片选择器 + OSS 上传 |
| iOS 登录 | 社交登录 | ❌ 占位按钮 | 接入微信/Apple Sign In |
| 后端埋点 | 事件追踪 | ⚠️ 仅日志 | 接入正式埋点系统 |
| iOS 埋点 | 事件追踪 | ⚠️ 仅打印 | 接入 Firebase/友盟 SDK |
| 管理后台 | 统计图 | ⚠️ 基础版 | 丰富趋势分析、AI 诊断质量监控 |

### 2.4 性能与监控（中优先级）

| 任务 | 当前状态 | 行动项 | 影响 |
|------|---------|--------|------|
| API 限流 | ⚠️ 仅短信 | 为全量接口增加 rate limit（按 IP/用户） | 恶意请求风险 |
| 日志聚合 | ⚠️ 本地 | 接入 ELK/Loki/云日志 | 难以排查故障 |
| 性能监控 | ❌ 无 | 部署 Sentry/Prometheus + Grafana | 无法监测瓶颈 |
| LLM 调用 | ⚠️ 同步 | 增加超时、重试、降级策略 | 调用失败无兜底 |
| 缓存策略 | ❌ 无 | Redis 缓存常用列表、session | 数据库压力大 |

### 2.5 运维与部署（高优先级）

| 任务 | 当前状态 | 行动项 |
|------|---------|--------|
| 容器化 | ❌ 无 | 编写 Dockerfile 与 docker-compose |
| CI/CD | ❌ 无 | 配置 GitHub Actions/GitLab CI 自动部署 |
| 环境隔离 | ⚠️ 仅 dev | 建立 dev/staging/prod 配置与部署流水线 |
| 健康检查 | ✅ `/health` | 扩展检查数据库与 LLM 连通性 |
| iOS 上架 | ❌ 未开始 | 准备 App Store 物料、隐私合规、TestFlight 测试 |

### 2.6 测试与质量（低优先级）

| 任务 | 当前状态 | 行动项 |
|------|---------|--------|
| 单元测试 | ⚠️ 部分 | 覆盖认证、诊断、CrewAI 核心逻辑 |
| 集成测试 | ❌ 无 | 编写主要 API 端到端测试 |
| iOS UI 测试 | ❌ 无 | XCTest 自动化登录/问诊流程 |
| 压力测试 | ❌ 无 | 模拟高并发登录与 AI 诊断 |

## 3. 已完成功能详情

### 3.1 账号+密码认证系统（2025-01-12 完成）

#### 后端改动

**新增文件：**
- `backend/app/services/password_service.py` - 密码哈希服务（bcrypt）
- `backend/migrations/add_password_hash.py` - 数据库迁移脚本

**修改文件：**
- `backend/app/models/user.py` - 新增 `password_hash` 字段和 `has_password` 属性
- `backend/app/schemas/auth.py` - 新增密码认证相关 Schema
- `backend/app/services/auth_service.py` - 新增密码相关方法
- `backend/app/routes/auth.py` - 新增密码认证接口

**新增 API 接口：**
| 接口 | 方法 | 描述 |
|------|------|------|
| `/auth/check-phone` | GET | 检查手机号是否存在及是否设置密码 |
| `/auth/register-password` | POST | 密码注册/设置密码（需验证码） |
| `/auth/login-password` | POST | 密码登录 |
| `/auth/password/set` | POST | 已登录用户设置/更新密码 |
| `/auth/password/reset` | POST | 重置密码（需验证码） |

#### iOS 改动

**新增文件：**
- `ios/.../ViewModels/PasswordLoginViewModel.swift` - 密码登录 ViewModel
- `ios/.../Views/RegisterView.swift` - 密码注册页面
- `ios/.../Views/ResetPasswordView.swift` - 重置密码页面

**修改文件：**
- `ios/.../Services/APIConfig.swift` - 新增密码认证端点
- `ios/.../Services/APIService.swift` - 新增密码认证 API 方法
- `ios/.../Views/LoginView.swift` - 新增密码/验证码登录切换、协议链接常量
- `ios/.../ContentView.swift` - 自动触发 ProfileSetupView

#### 验证步骤

**后端验证：**
```bash
# 1. 运行数据库迁移
cd backend
python -m migrations.add_password_hash

# 2. 启动后端服务
python run.py

# 3. 测试 API（使用 curl 或 Postman）
# 发送验证码
curl -X POST http://127.0.0.1:8100/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'

# 密码注册（测试模式验证码 000000）
curl -X POST http://127.0.0.1:8100/auth/register-password \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "code": "000000", "password": "test123456"}'

# 密码登录
curl -X POST http://127.0.0.1:8100/auth/login-password \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "password": "test123456"}'
```

**iOS 验证：**
1. 在 Xcode 中打开项目并运行
2. 登录页面应显示"验证码登录/密码登录"切换
3. 切换到密码登录模式，测试登录流程
4. 点击"立即注册"测试注册流程
5. 点击"忘记密码"测试重置密码流程
6. 新用户登录后应自动弹出资料完善页面

## 4. MVP 上线建议

- **必须完成（2-3 周）**：~~账号+密码登录~~、生产密钥、PostgreSQL、HTTPS+CORS、OSS 文件存储、~~iOS 资料完善闭环~~、正式协议、基础监控、容器化。
- **建议完成（1-2 周）**：向量数据库、API 限流+缓存、iOS TestFlight 内测。
- **可延后**：社交登录、进阶统计、压力测试、灰度发布。
