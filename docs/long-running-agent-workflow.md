# 长期 Agent 工作流指南

> **基于**: [Anthropic Engineering - Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> **创建日期**: 2026-02-13
> **适用项目**: 灵犀健康 AI 分身医疗健康管理平台

---

## 概述

本指南描述了一套让 Claude Agent 在长期、多会话场景下高效工作的工具和方法。

### 核心原则

1. **增量式开发** - 每次会话只完成一个功能或修复
2. **结构化进度跟踪** - 使用 JSON 文件跟踪所有功能状态
3. **Git 原子提交** - 每个功能完成后立即提交
4. **自验证优先** - 完成后必须验证才能标记为通过

---

## 工具文件

### 1. feature-list.json

**位置**: `/feature-list.json`（项目根目录）

**用途**: 结构化的功能清单，跟踪所有功能的实现状态

**结构**:
```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-02-13",
    "total_features": 247,
    "passing": 185,
    "failing": 2,
    "pending": 60
  },
  "features": {
    "backend": { ... },
    "frontend": { ... },
    "ios": { ... },
    "pending": { ... }
  }
}
```

**状态值**:
- `passing` - 功能已实现并验证通过
- `failing` - 功能存在但有问题
- `pending` - 待实现

### 2. claude-progress.txt

**位置**: `/claude-progress.txt`（项目根目录）

**用途**: 会话级别的进度日志，记录每次会话的工作内容

**结构**:
```markdown
## 会话记录

### YYYY-MM-DD Session: [标题]
- **状态**: ✅ 完成 / 🔄 进行中 / ❌ 失败
- **任务**: [描述]
- **完成内容**: [列表]
- **验证**: [验证结果]
- **提交**: [commit SHA]

## 工作规范
## 快捷命令
## 待办事项
```

### 3. init.sh

**位置**: `/init.sh`（项目根目录）

**用途**: 一键启动所有开发服务

**用法**:
```bash
# 启动所有服务
./init.sh

# 仅启动后端
./init.sh --backend-only

# 启动后端 + iOS 模拟器
./init.sh --no-frontend --ios

# 查看帮助
./init.sh --help
```

---

## 每次会话的工作流程

### 1. 会话开始（Getting Up to Speed）

Agent 每次新会话开始时，按以下顺序执行：

```
1. pwd                           # 确认工作目录
2. cat claude-progress.txt       # 阅读上次会话记录
3. cat feature-list.json         # 了解功能状态
4. git log --oneline -5          # 查看最近提交
5. git status                    # 检查当前状态
6. [可选] ./init.sh              # 启动开发服务
```

**预计耗时**: 1-2 分钟

### 2. 选择任务

从 `feature-list.json` 中选择一个状态为 `failing` 或 `pending` 的功能：

- **优先修复 `failing`** - 这些是已实现但有问题的功能
- **然后实现 `pending`** - 按优先级（P0 > P1 > P2）

**原则**: 一次只做一件事

### 3. 执行任务

```
1. 阅读相关文档（docs/ 目录）
2. 查看现有代码实现
3. 编写代码
4. 自测验证
5. 更新 feature-list.json
6. git commit
```

### 4. 会话结束

更新 `claude-progress.txt`：

```markdown
### YYYY-MM-DD Session: [任务名称]
- **状态**: ✅ 完成
- **任务**: [描述]
- **完成内容**:
  - ✅ [具体完成项]
- **验证**: [验证方法和结果]
- **提交**: [commit SHA]
```

---

## Git 提交规范

### 提交消息格式

```
<type>: <subject>

<details>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加医生工作台患者搜索` |
| `fix` | 修复问题 | `fix: 修复 API 类型不一致问题` |
| `refactor` | 重构 | `refactor: 统一前后端类型定义` |
| `docs` | 文档 | `docs: 更新 API 文档` |
| `test` | 测试 | `test: 添加会话 API 测试` |
| `security` | 安全修复 | `security: 移除硬编码 Token` |

### 提交时机

- ✅ **每次功能完成后立即提交**
- ✅ **每次修复后立即提交**
- ❌ **不要累积多个功能再提交**
- ❌ **不要在功能未完成时提交**

---

## 验证规范

### 后端验证

```bash
# API 测试
docker exec home_health-backend pytest backend/tests/routes/test_xxx.py -v

# 手动测试
curl -X POST http://localhost:8100/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","code":"123456"}'
```

### 前端验证

```bash
# 构建测试
cd frontend && npm run build

# 启动开发服务器手动测试
npm run dev
# 访问 http://localhost:5173
```

### iOS 验证

```bash
# 编译测试
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -destination 'platform=iOS Simulator,name=iPhone 15' build

# 安全验证
bash scripts/ios/verify-security.sh
```

### 验证要求

| 状态 | 要求 |
|------|------|
| `passing` | 功能完整 + 测试通过 + 手动验证 OK |
| `failing` | 功能存在但有已知问题 |
| `pending` | 未实现 |

---

## 常见问题

### Q: 会话中断怎么办？

A: 查看以下文件恢复上下文：
1. `claude-progress.txt` - 上次会话在做什么
2. `feature-list.json` - 哪些功能已完成
3. `git log --oneline -10` - 最近提交记录

### Q: 如何处理复杂功能？

A: 拆分为多个小功能，每个会话只做一个：
- 第1次会话: 基础实现
- 第2次会话: 添加验证
- 第3次会话: 优化性能

### Q: feature-list.json 太大怎么办？

A: 只关注相关部分：
- 后端开发 → 只看 `backend` 节点
- 前端开发 → 只看 `frontend` 节点
- iOS 开发 → 只看 `ios` 节点

### Q: 如何添加新功能？

A: 在 `pending` 节点添加：

```json
"pending": {
  "backend": {
    "new_feature_name": {
      "name": "新功能名称",
      "status": "pending",
      "description": "功能描述"
    }
  }
}
```

---

## 成功指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 功能通过率 | >95% | 75% (185/247) |
| 平均会话完成数 | 1-2个功能 | - |
| Git 提交频率 | 每功能1次 | - |
| 验证通过率 | 100% | - |

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-02-13 | 创建工作流指南，初始化工具文件 |
