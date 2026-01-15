---
trigger: always_on
priority: critical
---

# 项目开发规范

**版本**: V1.0  
**更新日期**: 2026-01-15  
**适用范围**: 全项目（后端、前端、iOS）

> ⚠️ **重要提示**: 所有开发者（包括 AI）在开始任何开发任务前，必须先阅读本文档以及对应模块的专用指南。

---

## 目录

1. [项目概述](#项目概述)
2. [通用开发原则](#通用开发原则)
3. [代码规范](#代码规范)
4. [Git 工作流](#git-工作流)
5. [测试要求](#测试要求)
6. [文档要求](#文档要求)
7. [安全规范](#安全规范)
8. [性能优化](#性能优化)

---

## 项目概述

### 系统架构

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
```

### 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite + CrewAI
- **管理后台**: React + TypeScript + Ant Design + Vite
- **iOS 客户端**: SwiftUI + Combine
- **LLM**: 阿里云通义千问 (Qwen)

---

## 通用开发原则

### 1. 单一信息源 (Single Source of Truth)

所有接口定义、数据类型、业务规则必须有唯一的权威来源：

- **API 契约**: 参考 `docs/API_CONTRACT.md`
- **数据模型**: 后端 `app/schemas/` 为准
- **iOS 规范**: 参考 `docs/IOS_DEVELOPMENT_GUIDE.md`

### 2. 类型安全优先

- **后端**: 使用 Pydantic 严格定义所有 Schema
- **iOS**: 使用 Swift 强类型系统，避免 `Any` 和强制解包
- **前端**: 使用 TypeScript，避免 `any` 类型

### 3. 错误处理

所有代码必须包含完善的错误处理：

```python
# 后端示例
try:
    result = await some_operation()
    logger.info(f"Operation succeeded: {result}")
    return result
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

```swift
// iOS 示例
do {
    let result = try await apiService.fetchData()
    print("[Service] Data fetched successfully")
    return result
} catch {
    print("[Service] Error: \(error.localizedDescription)")
    throw APIError.serverError(error.localizedDescription)
}
```

### 4. 日志规范

统一使用以下日志格式：

```
[ModuleName] 日志级别: 具体信息
```

示例：
- `[DermaAgent] 处理对话前的状态: chief_complaint=皮肤瘙痒`
- `[UnifiedChatVM] 已创建新会话: session-uuid`

---

## 代码规范

### 命名规范

#### Python (后端)

- **文件名**: 小写下划线 `medical_events.py`
- **类名**: 大驼峰 `MedicalEvent`
- **函数/变量**: 小写下划线 `get_event_with_permission`
- **常量**: 大写下划线 `MAX_FILE_SIZE`

#### Swift (iOS)

- **文件名**: 大驼峰 `UnifiedChatViewModel.swift`
- **类/结构体**: 大驼峰 `MedicalEventDTO`
- **函数/变量**: 小驼峰 `fetchEventDetail`
- **常量**: 小驼峰 `primaryPurple`

#### TypeScript (前端)

- **文件名**: 小驼峰或短横线 `apiService.ts` 或 `api-service.ts`
- **类/接口**: 大驼峰 `ApiService`
- **函数/变量**: 小驼峰 `fetchData`
- **常量**: 大写下划线 `API_BASE_URL`

### 注释规范

- **必须注释**: 复杂业务逻辑、算法、临时解决方案
- **禁止注释**: 显而易见的代码、已废弃的代码（直接删除）
- **TODO 标记**: 使用 `// TODO: 描述` 标记待完成工作

---

## Git 工作流

### 分支命名

- `main` - 主分支，生产环境代码
- `develop` - 开发分支
- `feature/功能名` - 新功能开发
- `fix/问题描述` - Bug 修复
- `refactor/模块名` - 代码重构

### Commit 规范

使用语义化提交信息：

```
<type>(<scope>): <subject>

<body>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例**:
```
feat(ios): 修复病历生成接口的数据类型不匹配问题

- 将 event_id 从 Int 改为 String 以匹配后端 UUID 格式
- 更新所有相关 DTO 和 ViewModel
- 移除不必要的类型转换代码
```

---

## 测试要求

### 单元测试

- **后端**: 使用 pytest，覆盖率 > 70%
- **iOS**: 使用 XCTest，关键业务逻辑必须测试
- **前端**: 使用 Vitest，组件测试覆盖核心功能

### 集成测试

- API 接口测试：使用 `backend/test/` 中的测试脚本
- 端到端测试：关键用户流程必须有 E2E 测试

### 测试数据

- 使用 mock 数据，不依赖生产环境
- 测试数据必须可重复、可预测

---

## 文档要求

### 必须维护的文档

1. **README.md** - 项目概述、快速开始
2. **API_CONTRACT.md** - API 接口契约（本次新增）
3. **DEVELOPMENT_GUIDELINES.md** - 本文档
4. **IOS_DEVELOPMENT_GUIDE.md** - iOS 开发指南（本次新增）
5. **CHANGELOG.md** - 版本变更记录

### 代码文档

- 公共 API 必须有文档注释
- 复杂算法必须有说明文档
- 配置文件必须有注释说明

---

## 安全规范

### 敏感信息

- **禁止硬编码**: API Key、密码、Token
- **使用环境变量**: 所有敏感配置放在 `.env` 文件
- **不提交到 Git**: `.env` 文件必须在 `.gitignore` 中

### 权限控制

- 所有 API 接口必须验证用户权限
- 用户只能访问自己的数据
- 管理员接口单独鉴权

### 数据验证

- 前端验证 + 后端验证（双重验证）
- 使用 Pydantic 进行数据校验
- 防止 SQL 注入、XSS 攻击

---

## 性能优化

### 后端

- 数据库查询使用索引
- 大数据量使用分页
- 合理使用缓存（Redis）
- 异步处理耗时操作

### iOS

- 图片压缩后上传（最大 5MB）
- 列表使用 LazyVStack 懒加载
- 避免主线程阻塞
- 合理使用 @State 和 @Published

### 前端

- 组件懒加载
- 图片懒加载
- 防抖/节流处理
- 合理使用 memo 和 useMemo

---

## 开发流程

### 开始新任务前

1. ✅ 阅读本文档
2. ✅ 阅读对应模块的专用指南（iOS/后端/前端）
3. ✅ 查看 `docs/API_CONTRACT.md` 确认接口定义
4. ✅ 检查是否有相关的 TODO 或已知问题
5. ✅ 创建功能分支

### 开发过程中

1. 遵循代码规范
2. 编写必要的测试
3. 及时提交代码（小步提交）
4. 更新相关文档

### 完成任务后

1. 运行所有测试
2. 更新 CHANGELOG.md
3. 提交 Pull Request
4. Code Review 通过后合并

---

## 常见问题

### Q: 接口字段类型不确定怎么办？

**A**: 查看 `docs/API_CONTRACT.md`，以后端 Schema 定义为准。

### Q: iOS 和后端数据类型不匹配？

**A**: 必须修改 iOS 端以匹配后端定义，后端的数据类型是权威来源。

### Q: 新增 API 接口的流程？

**A**: 
1. 在后端定义 Schema
2. 更新 `docs/API_CONTRACT.md`
3. 实现后端接口
4. 更新 iOS/前端的 DTO
5. 编写测试

---

## 相关文档

- [API 契约文档](./API_CONTRACT.md) - 接口定义的单一真相源
- [iOS 开发指南](./IOS_DEVELOPMENT_GUIDE.md) - iOS 专用开发规范
- [后端 API 文档](../backend/docs/AI_API_DOCUMENTATION.md) - 详细的 API 说明

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-15
