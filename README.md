# AI 医生分身系统

基于方案文档实现的完整 AI 医生分身系统，包含后端 API、管理后台和 iOS 客户端。

## 系统架构

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   iOS App       │◄────────┤   FastAPI        │◄────────┤  Admin Web      │
│  (患者端)        │  HTTP   │   Backend        │  HTTP   │  (管理后台)      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                              ┌──────▼──────┐
                              │   SQLite    │
                              │  (开发环境)   │
                              └─────────────┘
                                     │
                              ┌──────▼──────┐
                              │  LLM API    │
                              │ (Qwen/GPT)  │
                              └─────────────┘
```

## 项目结构

```
home-health/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── models/   # 数据模型
│   │   ├── routes/   # API 路由
│   │   ├── schemas/  # Pydantic 模型
│   │   └── services/ # 业务服务
│   └── requirements.txt
├── frontend/         # React 管理后台
│   ├── src/
│   │   ├── api/      # API 调用
│   │   ├── layouts/  # 布局组件
│   │   └── pages/    # 页面组件
│   └── package.json
└── ios/              # iOS 客户端
    └── xinlingyisheng/
```

## 快速开始

### 1. 启动后端服务

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务 (会自动创建数据库和初始化数据)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行

- API 文档: http://localhost:8000/docs
- 默认管理员账号: `admin` / `admin123`

### 2. 启动管理后台

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

管理后台将在 http://localhost:5173 运行

### 3. iOS 客户端

使用 Xcode 打开 `ios/xinlingyisheng/xinlingyisheng.xcodeproj`，运行即可。

确保在 `APIConfig.swift` 中配置正确的后端地址。

## 核心功能

### 后端 API

**用户端 API:**
- `POST /auth/login` - 用户登录
- `GET /departments` - 获取科室列表
- `GET /departments/{id}/doctors` - 获取科室医生
- `POST /sessions` - 创建会话
- `POST /sessions/{id}/messages` - 发送消息
- `POST /sessions/{id}/feedback` - 提交反馈

**管理后台 API:**
- `POST /admin/auth/login` - 管理员登录
- `GET /admin/stats/overview` - 统计概览
- `GET/POST/PUT/DELETE /admin/doctors` - 医生管理
- `GET/POST/PUT/DELETE /admin/departments` - 科室管理
- `GET/POST/PUT/DELETE /admin/knowledge-bases` - 知识库管理
- `GET/POST /admin/documents` - 文档管理
- `GET/PUT /admin/feedbacks` - 反馈管理

### 管理后台功能

1. **仪表盘** - 统计概览、待处理事项
2. **科室管理** - 科室的增删改查
3. **医生管理** - AI 医生配置、Prompt 设置、模型参数、测试对话
4. **知识库管理** - 知识库和文档管理、审核流程
5. **反馈管理** - 用户反馈查看和处理
6. **统计分析** - 趋势数据、审计日志

### AI 医生配置

每个 AI 医生支持配置：
- **ai_persona_prompt**: 自定义人格化提示词
- **ai_model**: 使用的 LLM 模型 (qwen-turbo/qwen-plus/qwen-max)
- **ai_temperature**: 生成温度 (0-2)
- **ai_max_tokens**: 最大输出 token 数
- **knowledge_base_id**: 关联的知识库

### RAG 知识库

支持为每个医生配置专属知识库：
1. 创建知识库
2. 添加知识文档 (病例/FAQ/指南/SOP)
3. 文档审核通过后自动索引
4. 问诊时自动检索相关知识

## 环境变量

后端 `.env` 配置：

```env
# 数据库
DATABASE_URL=sqlite:///./app.db

# JWT
JWT_SECRET_KEY=your-secret-key
ADMIN_JWT_SECRET=your-admin-secret

# LLM 配置
LLM_PROVIDER=qwen
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=your-api-key
LLM_TEMPERATURE=0.7
```

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **管理后台**: React + TypeScript + Ant Design + Vite
- **iOS 客户端**: SwiftUI
- **LLM**: 阿里云通义千问 (Qwen)

## 后续迭代

- [ ] 向量数据库集成 (pgvector/Milvus)
- [ ] CrewAI 多 Agent 支持
- [ ] 图片识别 (皮肤病、报告单)
- [ ] 医生自助接入平台
- [ ] 知识库众包

# CI/CD 测试 - 2026年 1月21日 星期三 12时01分36秒 CST

# CI/CD 重新测试 - 2026年 1月21日 星期三 12时03分09秒 CST
