# P1 技术债务执行计划

**创建日期**: 2026-02-11
**状态**: 待执行
**优先级**: P1（重要）

---

## 概述

本文档定义了 12 个 P1 技术债务任务的详细执行计划。

**P1 任务**: 12 项
- 后端：3 项
- 前端：6 项
- iOS：3 项

---

## 后端 P1 任务（3 项）

### BE-P1-001: API V1/V2 并存

**问题**: `sessions.py` 和 `sessions_v2.py` 两套 API 并存

**差异分析**:
- V1: 单一智能体架构，使用 `agent_type` 参数
- V2: 多智能体架构，使用统一路由器

**执行方案**:
1. 标记 V1 为 `@deprecated` (2h)
2. 确认无外部调用方依赖 V1 (4h)
3. 更新前端全部使用 V2 (4h)
4. 删除 V1 代码和测试 (4h)
5. 端到端验证 (2h)

**回滚方案**: 保留 V1 代码在 Git 历史，可快速恢复

**验收标准**:
- [ ] 前端无 V1 API 调用
- [ ] 后端无 V1 路由定义
- [ ] 所有会话功能正常

**预估工时**: 20 小时（含缓冲）

---

### BE-P1-002: N+1 查询风险

**状态**: ✅ 已完成 (2026-02-11)

**问题**: 多处关系查询未使用 joinedload

**执行方案**:
1. 使用 Grep 搜索关系查询 (1h)
2. 添加 `joinedload()` 优化 (2h)
3. 验证 SQL 查询日志 (1h)

**验收标准**:
- [x] 无 N+1 查询警告
- [x] 查询性能无明显退化
- [x] 所有 API 测试通过

**实际工时**: 2 小时

**优化效果**:
- `doctor_workstation.py`: 7 处优化
  - `get_doctor_info`: 从 3+N 次查询减少到 2 次
  - `get_patient_stats`: 从 N+1 次查询减少到 4 次
  - `get_patients`: 从 3N+1 次查询减少到 4 次
  - `get_assignable_patients`: 从 N+1 次查询减少到 2 次
  - `get_patient_consultations`: 从 N+1 次查询减少到 2 次
  - `get_patient_tasks`: 添加 `selectinload` 预加载 order
- `admin_departments.py`: 4 处优化
  - 所有函数使用 `joinedload` 预加载 doctors，从 N+1 次查询减少到 1 次
- `medical_orders.py`: 4 处优化
  - `get_family_bonds`: 从 2N+2 次查询减少到 4 次
  - `get_daily_tasks`: 添加 `selectinload` 预加载 order
  - `get_family_member_tasks`: 添加 `selectinload` 预加载 order
  - `get_alerts`: 添加 `selectinload` 预加载 task_instance 和 order

---

### BE-P1-003: 硬编码配置

**状态**: ✅ 已完成 (2026-02-11)

**问题**: config.py 中有硬编码值

**硬编码配置清单**:
- `JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"`
- `ADMIN_JWT_SECRET: str = "admin-secret-key-change-in-production"`
- `DATABASE_URL: str = "postgresql://..."`

**执行方案**:
1. 识别硬编码值 (0.5h)
2. 移到环境变量 (0.5h)
3. 更新 docker-compose.yml (0.5h)
4. 更新 .env.example (0.5h)

**验收标准**:
- [x] 所有敏感配置可通过环境变量设置
- [x] .env.example 包含所有必需配置
- [x] 使用 `secrets.token_urlsafe(32)` 生成强随机密钥作为默认值

**实际工时**: 2 小时

---

## 前端 P1 任务（6 项）

### FE-P1-001/002: 前端权限系统问题

**问题**: 角色硬编码、无权限守卫组件

**执行方案**:
1. 创建 `constants/roles.ts` 定义角色常量
2. 创建 `components/auth/ProtectedRoute.tsx`
3. 更新路由使用权限守卫

**预估工时**: 6 小时

---

### FE-P1-003: Token 未使用

**状态**: ✅ 已验证 (2026-02-11) - 虚假问题

**原问题**: api/index.ts 中认证代码被注释

**验证结果**:
- 认证代码**未被注释**，已完整实现
- 请求拦截器：自动添加 `Authorization: Bearer {token}`
- 响应拦截器：401 时清除 token 并跳转登录页
- 支持测试模式 (`VITE_ADMIN_TEST_MODE=true`) 和生产模式切换

**影响范围**: `frontend/src/api/index.ts`

**执行方案**:
1. 检查所有 API 端点的认证状态 (0.5h)
2. 恢复 Authorization header (0.5h)
3. 恢复 401 跳转登录处理 (0.5h)
4. 测试认证流程 (0.5h)

**验收标准**:
- [ ] 所有 API 请求携带 Authorization header
- [ ] 401 响应正确跳转到登录页
- [ ] Token 过期时提示用户

**预估工时**: 2 小时

---

### FE-P1-004: 组件目录重复

**问题**: `/@/` 和 `/src/` 组件目录重复

**执行方案**:
1. 分析两目录差异
2. 合并到 `/src/components/ui/`
3. 更新所有导入

**预估工时**: 2 小时

---

### FE-P1-005: 添加患者功能缺失

**问题**: 按钮存在但无点击事件

**执行方案**:
1. 创建 `AssignPatientDialog.tsx`
2. 实现患者选择逻辑
3. 调用分配 API

**预估工时**: 6 小时

---

### FE-P1-006: 图表库不统一

**问题**: 使用 @ant-design/charts

**执行方案**:
1. 决策：保留或迁移到 Recharts
2. 如迁移：重写图表组件
3. 更新所有图表页面

**预估工时**: 8 小时

---

## iOS P1 任务（3 项）

### IOS-P1-001: 弃用 API 未清理

**问题**: 多处 `@available(*, deprecated)`

**弃用 API 清单**（预扫描）:
- `Font.caption` → 使用 `UnifiedFont.caption1`
- `Color.UIImage` → 使用新颜色系统
- 其他待扫描确认

**执行方案**:
1. 扫描所有弃用标记 (2h)
2. 确认每个替代方案 (2h)
3. 更新代码 (3h)
4. 测试不同 iOS 版本兼容性 (1h)

**验收标准**:
- [ ] 无编译警告
- [ ] 最低支持版本 iOS 15.0+ 正常运行

**预估工时**: 8 小时

---

### IOS-P1-002: AppIcon 图标缺失

**问题**: 13 个尺寸图标未分配

**执行方案**:
1. 准备图标资源
2. 分配到各个尺寸
3. 验证显示效果

**预估工时**: 2 小时

---

### IOS-P1-003: 组件功能重叠

**状态**: ✅ 分析完成 (2026-02-11)

**问题**: 多处组件重复

**执行方案**:
1. ✅ 识别重复组件
2. ✅ 分析重叠情况
3. ✅ 提供清理建议

**分析结果**:
- **真实重叠**: EmptyStateView（`DossierEmptyStateView` vs `UnifiedEmptyStateView`）
- **虚假重叠**: API 服务、PDF 生成器、Card 组件各有不同用途
- **已清理**: `SimpleSpeechInputService` 不存在

**详细报告**: [2026-02-11-ios-component-overlap-analysis.md](2026-02-11-ios-component-overlap-analysis.md)

**预估工时**: 1 小时（如需迁移 EmptyStateView）

---

## 执行顺序建议（已优化）

### 第一批（安全认证修复）
1. FE-P1-003: Token 未使用 (2h)
2. FE-P1-004: 组件目录重复 (2h)
3. BE-P1-003: 硬编码配置 (2h)
**小计**: 6h

### 第二批（权限系统 + 资源）
4. FE-P1-001/002: 前端权限系统 (6h)
5. IOS-P1-002: AppIcon 图标 (2h)
**小计**: 8h

### 第三批（功能完善）
6. FE-P1-005: 添加患者功能 (6h)
**小计**: 6h

### 第四批（架构优化）
7. BE-P1-001: API V1/V2 统一 (20h)
8. IOS-P1-001: 弃用 API 清理 (8h)
9. BE-P1-002: N+1 查询优化 (4h)
10. FE-P1-006: 图表库统一 (8h)
11. IOS-P1-003: 组件重叠清理 (分析完成，1h可选执行)
**小计**: 41h + 1h(可选)

---

## 总工时

| 批次 | 工时 | 说明 |
|------|------|------|
| 第一批 | 6h | 安全认证修复 |
| 第二批 | 8h | 权限系统 + 资源 |
| 第三批 | 6h | 功能完善 |
| 第四批 | 37h + 1h(可选) | 架构优化（BE-P1-002 已完成） |
| **合计** | **57h + 1h(可选)** | 含 20% 缓冲 |

---

## 依赖关系图

```
┌─────────────────────────────────────────────────────────┐
│                    P1 任务依赖图                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  第一批: 安全认证修复 (无依赖)                           │
│       ├─ FE-P1-003: Token 恢复                          │
│       ├─ FE-P1-004: 组件目录合并                        │
│       └─ BE-P1-003: 硬编码配置                          │
│                  ↓                                      │
│  第二批: 权限系统 (依赖第一批 Token 恢复)                │
│       ├─ FE-P1-001/002: 权限守卫                        │
│       └─ IOS-P1-002: AppIcon (独立)                     │
│                  ↓                                      │
│  第三批: 功能完善 (无依赖)                              │
│       └─ FE-P1-005: 添加患者功能                        │
│                  ↓                                      │
│  第四批: 架构优化 (依赖前面所有)                        │
│       ├─ BE-P1-001: API 统一                            │
│       ├─ IOS-P1-001: 弃用 API 清理                      │
│       ├─ BE-P1-002: N+1 查询                            │
│       ├─ FE-P1-006: 图表库统一                          │
│       └─ IOS-P1-003: 组件重叠清理                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 相关文档

- [技术债务清理计划](/docs/plans/2026-02-11-tech-debt-cleanup-plan.md)
- [技术债务清单](/docs/planning/tech-debt.md)
