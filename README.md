# 📖 灵犀健康 - 团队入职手册

> **最后更新**: 2026-02-11
> **版本**: v2.0
> **面向**: 所有新加入项目的 Agent (后端/前端/iOS)
> **必读**: ⭐⭐⭐⭐⭐

---

## 🎯 30秒快速导航

| 需求 | 跳转 |
|------|------|
| 我是新来的，快速了解项目 | → [项目概述](#项目概述) |
| 我要启动开发环境 | → [开发环境启动](#开发环境启动) |
| 我是后端 Agent | → [后端开发指南](#后端开发指南) |
| 我是前端 Agent | → [前端开发指南](#前端开发指南) |
| 我是 iOS Agent | → [iOS 开发指南](#ios-开发指南) |
| 我要运行测试 | → [测试指南](#测试指南) |
| 我要提交代码 | → [代码提交规范](#代码提交规范) |
| 遇到问题了 | → [常见问题](#常见问题) |
| 查看工作进度 | → [PROGRESS.md](./PROGRESS.md) |

---

## 项目概述

### 项目简介

**灵犀健康** 是一个医疗健康咨询应用，通过 AI 分身系统为用户提供智能医疗咨询服务。

```
┌─────────────────────────────────────────────────────────────────┐
│                        灵犀健康系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│  客户端层                     │  API 层                 │  服务层  │
│  ┌──────────┬──────────┐      │  ┌──────────────┐      │  ┌──────┐ │
│  │  iOS App │ Web Admin│      │  │  FastAPI     │      │  │  AI   │ │
│  │ (SwiftUI) │ (React)  │──────┼─│  Port: 8100   │──────┼─│ Agent│ │
│  └──────────┴──────────┘      │  └──────────────┘      │  └──────┘ │
│                                │                        │          │
│  数据层                        │  ┌──────────────┐      │          │
│  ┌──────────────────────┐     │  │  PostgreSQL   │      │          │
│  │  PostgreSQL (业务)   │     │  │  Port: 5433   │      │          │
│  │  SQLite (知识库)      │─────┼─│  Docker       │      │          │
│  └──────────────────────┘     │  └──────────────┘      │          │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 模块 | 技术 | 端口 |
|------|------|------|
| 后端 | Python + FastAPI + SQLAlchemy | `8100` |
| 前端 | React + TypeScript + Vite + shadcn/ui | `5173` |
| iOS | Swift + SwiftUI | - |
| 数据库 | PostgreSQL (Docker) | `5433` |

### 目录结构

```
home-health/
├── backend/               # 后端服务
│   ├── app/
│   │   ├── models/        # ORM 数据模型
│   │   ├── routes/        # API 路由
│   │   ├── schemas/       # Pydantic 验证
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 入口
│   ├── test/              # 28个测试文件
│   └── requirements.txt
├── frontend/              # Web 前端
│   ├── src/
│   │   ├── pages/         # 页面
│   │   ├── components/    # 组件
│   │   ├── api/           # API封装
│   │   └── types/         # 类型
│   └── package.json
├── ios/                   # iOS应用
│   └── xinlingyisheng/
│       ├── xinlingyisheng/Views/       # 视图
│       ├── xinlingyisheng/ViewModels/  # 视图模型
│       └── xinlingyisheng/Services/     # 服务
├── docs/                   # 核心文档 ⭐
│   ├── *.md               # 启动、架构、API、配置
│   ├── planning/          # 技术债务、路线图
│   └── plans/             # 设计报告 (66份)
├── PROGRESS.md            # ⭐ 工作进度追踪
└── README.md              # 本文档
```

---

## 开发环境启动

### ⚠️ 启动顺序（重要！）

```
1. Docker 容器 (数据库)     ← 必须先启动
   ↓
2. 后端服务 (Python)
   ↓
3. 前端服务 (可选)
   ↓
4. iOS 模拟器 (可选)
```

### 1. 启动数据库

```bash
# 检查容器状态
docker ps | grep home_health_db

# 启动容器
docker start home_health_db

# 验证连接
docker exec -it home_health_db psql -U postgres -d home_health -c "SELECT 1;"
```

### 2. 启动后端

```bash
cd backend
./venv/bin/python start_server.py

# 验证: curl http://localhost:8100/
# API文档: http://localhost:8100/docs
```

### 3. 启动前端（可选）

```bash
cd frontend
npm run dev

# 访问: http://localhost:5173
```

### 4. 启动 iOS（可选）

```bash
open ios/xinlingyisheng/xinlingyisheng.xcodeproj
# 在 Xcode 中运行 (⌘+R)
```

---

## 后端开发指南

### 核心文件

| 文件 | 说明 |
|------|------|
| `app/main.py` | 应用入口 |
| `app/config.py` | 配置管理 |
| `app/database.py` | 数据库连接 |
| `app/services/auth_service.py` | 认证服务 |
| `app/routes/doctor_workstation.py` | 医生工作台 API |

### 路由定义规范

```python
from fastapi import APIRouter, Depends
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/xxx", tags=["xxx"])

# ⚠️ 重要: 具体路径必须在参数化路径之前
@router.get("/create")  # ← 先定义
async def create(...): pass

@router.get("/{id}")     # ← 后定义
async def get(id: int): pass
```

### 添加新功能流程

```
1. 创建数据模型 (models/)
2. 创建 Schema (schemas/)
3. 创建路由 (routes/)
4. 创建测试 (test/)
5. 更新 API 文档
```

### 后端测试

```bash
cd backend
pytest test/ -v                          # 运行所有测试
pytest test/test_your_feature.py -v       # 运行特定测试
pytest test/ --cov=app --cov-report=html   # 生成覆盖率报告
```

---

## 前端开发指南

### 核心文件

| 文件 | 说明 |
|------|------|
| `src/App.tsx` | 应用入口、路由配置 |
| `src/api/index.ts` | API 封装 |
| `src/types/` | TypeScript 类型定义 |
| `src/components/ui/` | shadcn/ui 组件 |

### 组件开发

```typescript
// 1. 使用 shadcn/ui 组件
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 2. 使用类型
import { type User } from '@/types/auth';

// 3. 状态管理
import { useAuthStore } from '@/stores/authStore';
```

### 添加新页面

```
1. 创建页面组件 src/pages/NewPage.tsx
2. 添加路由到 App.tsx
3. 添加导航菜单（如需要）
```

### 前端测试

```bash
cd frontend
npm run test              # 单元测试
npm run test:e2e          # E2E测试
npm run build             # 构建验证
```

---

## iOS 开发指南

### 核心文件

| 文件 | 说明 |
|------|------|
| `xinlingyisheng/App.swift` | 应用入口 |
| `Services/AuthManager.swift` | 认证管理 |
| `Services/KeychainManager.swift` | 安全存储 |
| `ViewModels/UnifiedChatViewModel.swift` | 聊天视图模型 |
| `Theme/HealingColorTheme.swift` | 主题颜色 |

### SwiftUI 开发

```swift
// 1. 使用主题颜色
Text("Hello")
    .foregroundColor(HealingColorTheme.text)
    .background(HealingColorTheme.background)

// 2. Keychain 存储敏感信息 (禁止用 UserDefaults)
KeychainManager.shared.save(token, key: .authToken)

// 3. 使用 ViewModels
@StateObject private var viewModel = UnifiedChatViewModel()
```

### iOS 构建

```bash
# 命令行构建
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator clean build

# 或在 Xcode 中: Product → Build (⌘+B)
```

---

## 测试指南

| 模块 | 命令 |
|------|------|
| 后端 | `cd backend && pytest test/ -v` |
| 前端 | `cd frontend && npm run test` |
| iOS | `cd ios && xcodebuild test` |

---

## 代码提交规范

### Commit 格式

```
<type>(<scope>): <subject>

类型:
- feat: 新功能
- fix: Bug修复
- docs: 文档更新
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例:
feat(backend): add patient assignment API
fix(frontend): correct routing order
docs(api): update authentication docs
```

### 提交前检查

- [ ] 代码 lint 通过
- [ ] 测试全部通过
- [ ] iOS 编译成功
- [ ] 文档已更新

---

## 常见问题

### 数据库连接失败

```bash
docker ps | grep home_health_db  # 检查容器
docker start home_health_db       # 启动容器
```

### 后端启动失败

```bash
cd backend
./venv/bin/python start_server.py  # 查看错误
pip list | grep fastapi            # 检查依赖
```

### iOS 编译失败

```bash
rm -rf ~/Library/Developer/Xcode/DerivedData  # 清理缓存
xcodebuild clean build                              # 重新构建
```

---

## 文档维护

### ⭐ 每个 Agent 必须维护文档

1. **工作前**: 阅读 README.md 和相关文档
2. **工作中**: 更新 PROGRESS.md 记录进度
3. **完成后**: 创建/更新报告文档到 `docs/plans/`

### 文档位置

| 文档 | 位置 |
|------|------|
| 入职手册 | `README.md` |
| 工作进度 | `PROGRESS.md` |
| 核心文档 | `docs/*.md` |
| 设计报告 | `docs/plans/*.md` |

---

## 联系

- **项目路径**: `/Users/zhuxinye/Desktop/project/home-health`
- **文档路径**: `docs/`

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-06 | 初始版本 |
| v2.0 | 2026-02-11 | 重写为详尽入职手册 |
