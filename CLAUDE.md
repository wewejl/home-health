# Claude 配置文件 - 灵犀健康项目

> **基于**: [Anthropic - Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> **更新日期**: 2026-02-13
> **模式**: 长期单个 Agent，多会话增量开发

---

## 核心原则

### 🎯 我的工作模式

我是**单个长期 Agent**，通过多次会话逐步完成项目功能：

```
┌─────────────────────────────────────────────────────────────────┐
│                    长期 Agent 工作模式                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Session 1      Session 2      Session 3      Session 4       │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │
│  │ 功能 A │ →  │ 功能 B │ →  │ 功能 C │ →  │ 功能 D │ → ...  │
│  └────────┘    └────────┘    └────────┘    └────────┘         │
│      ↓            ↓            ↓            ↓                 │
│   commit       commit       commit       commit              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 关键规则

| 规则 | 说明 |
|------|------|
| **一次只做一个功能** | 每次会话只完成一个功能或修复 |
| **完成后立即提交** | 不要累积多个功能再提交 |
| **必须验证** | 完成后必须测试验证才能标记为通过 |
| **记录进度** | 更新 `claude-progress.txt` 和 `feature-list.json` |

---

## 每次会话开始（Getting Up to Speed）

### 第一步：标准启动流程

```bash
# 1. 确认工作目录
pwd

# 2. 阅读项目状态
cat STATUS.md

# 3. 查看功能状态
cat feature-list.json | jq '.metadata'

# 4. 查看最近提交
git log --oneline -5

# 5. 检查工作区状态
git status

# 6. 阅读上次会话记录
cat claude-progress.txt
```

### 第二步：选择任务

从 `feature-list.json` 中选择任务：

- **优先修复 `failing`** - 已实现但有问题的功能
- **然后实现 `pending`** - 按 P0 → P1 → P2 顺序

**一次只选一个任务！**

### 第三步：启动服务（如需要）

```bash
./init.sh              # 启动所有服务
./init.sh --backend-only     # 仅后端
```

---

## 工作流程

### 1. 理解任务

```
┌─────────────────┐
│  阅读任务描述    │
└────────┬────────┘
         ↓
┌─────────────────┐
│  查看相关文档    │ ← docs/
└────────┬────────┘
         ↓
┌─────────────────┐
│  查看现有代码    │
└────────┬────────┘
         ↓
┌─────────────────┐
│  明确实现方案    │
└─────────────────┘
```

### 2. 实现功能

```
┌─────────────────┐
│  编写代码        │
└────────┬────────┘
         ↓
┌─────────────────┐
│  自测验证        │ ← 必须测试！
└────────┬────────┘
         ↓
┌─────────────────┐
│  修复问题        │ ← 如有失败
└─────────────────┘
```

### 3. 完成任务

```
┌─────────────────┐
│  更新功能状态    │ → feature-list.json
└────────┬────────┘
         ↓
┌─────────────────┐
│  Git 提交        │ ← 原子提交
└────────┬────────┘
         ↓
┌─────────────────┐
│  更新会话日志    │ → claude-progress.txt
└─────────────────┘
```

---

## 项目结构

```
project/
├── backend/          # Python FastAPI 后端
├── frontend/         # React + TypeScript 前端
├── ios/              # Swift + SwiftUI iOS 应用
├── docs/             # 文档
├── scripts/          # 工具脚本
├── feature-list.json # ⭐ 功能清单（247项）
├── STATUS.md         # ⭐ 项目状态
├── claude-progress.txt # 会话日志
└── init.sh           # 启动脚本
```

---

## 技术栈

| 模块 | 技术 | 端口 |
|------|------|------|
| 后端 | Python + FastAPI + SQLAlchemy | 8100 |
| 前端 | React + TypeScript + Vite | 5173 |
| iOS | Swift + SwiftUI | - |
| 数据库 | PostgreSQL (Docker) | 5432 |

---

## 快捷命令

```bash
# 启动服务
./init.sh                    # 所有服务
./init.sh --backend-only     # 仅后端
./init.sh --frontend-only    # 仅前端

# 后端
docker-compose logs -f backend
docker exec home_health-backend pytest

# 前端
cd frontend && npm run dev
cd frontend && npm run build

# iOS
bash scripts/ios/verify-security.sh
cd ios/xinlingyisheng && xcodebuild build
```

---

## Git 提交规范

### 格式

```
<type>: <subject>

<details>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加医生工作台患者搜索` |
| `fix` | 修复问题 | `fix: 修复 API 类型不一致` |
| `refactor` | 重构 | `refactor: 统一前后端类型` |
| `docs` | 文档 | `docs: 更新 API 文档` |
| `security` | 安全修复 | `security: 移除硬编码 Token` |

### 提交时机

- ✅ **每个功能完成后立即提交**
- ❌ **不要累积多个功能再提交**

---

## 验证规范

### 后端

```bash
# API 测试
docker exec home_health-backend pytest backend/tests/routes/test_xxx.py -v

# 手动测试
curl -X POST http://localhost:8100/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","code":"123456"}'
```

### 前端

```bash
cd frontend && npm run build
# 访问 http://localhost:5173 手动测试
```

### iOS

```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng build
bash scripts/ios/verify-security.sh
```

---

## 常见问题

### Q: 会话中断怎么办？

A: 查看以下文件恢复上下文：
1. `claude-progress.txt` - 上次会话在做什么
2. `feature-list.json` - 哪些功能已完成
3. `git log --oneline -10` - 最近提交记录

### Q: 如何处理复杂功能？

A: 拆分为多个小功能，每次会话只做一部分：
- 第1次: 基础实现
- 第2次: 添加验证
- 第3次: 优化性能

### Q: 功能清单太大怎么办？

A: 只关注相关部分：
- 后端开发 → 只看 `backend` 节点
- 前端开发 → 只看 `frontend` 节点
- iOS 开发 → 只看 `ios` 节点

---

## 参考文档

| 文档 | 位置 | 用途 |
|------|------|------|
| 项目状态 | `STATUS.md` | 快速了解当前状态 |
| 功能清单 | `feature-list.json` | 所有功能状态 |
| 会话日志 | `claude-progress.txt` | 上次会话记录 |
| 启动指南 | `docs/启动指南.md` | 详细启动步骤 |
| 架构设计 | `docs/架构设计.md` | 系统架构 |
| API文档 | `docs/API文档.md` | API 接口 |
| 工作流指南 | `docs/long-running-agent-workflow.md` | 详细工作流说明 |

---

## 重要原则总结

1. **每次会话只完成一个功能**
2. **完成后立即验证和提交**
3. **更新 feature-list.json 状态**
4. **更新 claude-progress.txt 记录**
5. **不要跳过验证步骤**

---

## ⚠️ 必须遵守的规范（2026-02-14 更新）

### feature-list.json 是唯一的真相来源

- **所有可追踪的任务都必须在 feature-list.json 中**
- ❌ **不要创建独立的问题文件**（如 `ios-code-issues.md`）
- ✅ 代码质量问题也应作为任务添加到 feature-list.json
- ✅ 示例：`"code_quality": { "force_unwrap_fix": "pending", ... }`

### 每个功能完成后立即提交

- ✅ 编译成功后立即 `git commit`
- ✅ 不要累积多个修改再提交
- ✅ 提交后立即更新 feature-list.json 和 claude-progress.txt
- ❌ 不要"更新了但没提交"

### 验证要求

- ✅ 后端：pytest 测试通过 + curl 手动测试
- ✅ 前端：npm run build 成功 + 浏览器手动测试
- ✅ iOS：xcodebuild 成功 + **模拟器运行测试**
- ❌ 不要只验证编译，不运行应用

### 禁止的行为

- ❌ 创建独立的跟踪文件（违背"唯一真相来源"原则）
- ❌ 一次修复多个问题再提交（违背"原子提交"原则）
- ❌ 只编译不运行（违背"端到端验证"原则）
- ❌ 更新文件但不提交（违背"清晰状态"原则）
