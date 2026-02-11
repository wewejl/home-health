# 迭代计划

> **最后更新**：2026-02-10

---

## 当前迭代 (Sprint 1)

### Sprint 信息
- **周期**：2026-02-01 ~ 2026-02-15
- **目标**：医生工作台开发与项目优化

### 进行中
暂无

### 待开始
- [ ] 患者搜索功能优化
- [ ] 医嘱创建功能完善
- [ ] 任务完成情况统计优化
- [ ] TASK-UI-006: iOS 对话页面输入框透明问题修复

### 已完成
- [x] **shadcn/ui 前端界面优化** - 2026-02-10
- [x] **前端布局美观度优化** - 2026-02-10
- [x] **医生工作台重构** - 2026-02-10
  - ✅ DW-001: 患者列表卡片化 (PatientCard 组件)
  - ✅ DW-002: 骨架屏组件 (PatientCardSkeleton, OrdersTableSkeleton 等)
  - ✅ DW-003: 对话界面响应式优化 (flex 布局)
  - ✅ DW-004: OrdersTab 组件拆分 (852行 → 212行)
  - ✅ 端到端测试通过 (8/8)
  - 📄 报告文档：
    - `docs/plans/doctor-workstation-code-review.md` - 代码审核报告
    - `docs/plans/doctor-workstation-refactor-e2e-report.md` - 测试报告
  - ✅ P0-P3 问题修复：组件统一、API 封装、Toast、防抖、类型安全
  - ✅ 代码评审：初评 83/100 → 最终 100/100 (卓越 A++)
  - ✅ 端到端测试通过
- [x] **前端布局美观度优化** - 2026-02-10
  - ✅ P0 问题：表头样式、表格边界、卡片间距
  - ✅ P1 问题：进度条样式、空状态、行高一致性
  - ✅ P2 问题：悬停效果增强
  - ✅ 验收通过：9/9 问题全部修复
- [x] **/patients 页面路由修复** - 2026-02-10
  - ✅ 测试用户角色从 admin 改为 doctor
- [x] **医生工作台开发** - 2026-02-09
  - ✅ 后端 API (`backend/app/routes/doctor_workstation.py`)
  - ✅ 前端页面 (`frontend/src/pages/doctor/`)
  - ✅ 路由配置和权限控制
- [x] **医生-患者关联功能** - 2026-02-09
  - ✅ 数据库表 `doctor_patient_relationships`
  - ✅ ORM 模型 `DoctorPatientRelationship`
  - ✅ 患者分配 API (`/api/doctor/patients/assign`)
  - ✅ 患者解除关联 API (`/api/doctor/patients/{id}/unassign`)
  - ✅ 可分配患者列表 API (`/api/doctor/patients/assignable`)
  - ✅ 权限验证逻辑（医生只能看到分配的患者）
- [x] 项目文档体系重建 - 2026-02-07
- [x] EventDetailView Caption 废弃警告修复 - 2026-02-06
- [x] 医嘱任务 UI 重构 - 2026-02-07
- [x] iOS Caption 废弃警告修复 - 2026-02-08

### 阻塞问题
暂无

---

## 下个迭代预览 (Sprint 2)

待规划...

---

## 历史迭代

暂无

---

## 迭代状态图例

| 状态 | 图例 | 说明 |
|------|------|------|
| 进行中 | 🔄 | 正在开发中 |
| 待开始 | 📋 | 已排期，未开始 |
| 已完成 | ✅ | 已完成并验证 |
| 阻塞 | ⚠️ | 有问题需要解决 |
