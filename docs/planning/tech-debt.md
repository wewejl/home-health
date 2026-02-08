# 技术债务清单

> 最后更新：2026-02-08

---

## 🔴 高优先级（尽快处理）

暂无

---

## 🟡 中优先级（有空就做）

### iOS 变量声明警告
- **状态**: ❌ 已检查，不存在此问题（可能已修复）
- **位置**: `ios/xinlingyisheng/ViewModels/MedicalFolderViewModel.swift:383`
- **问题**: `var chunk` 应改为 `let chunk`
- **影响**: 代码质量
- **预估工作量**: 1 分钟

---

## 🟢 低优先级（暂缓）

### API 版本冗余
- **位置**: 后端 `backend/app/routes/sessions.py` vs `sessions_v2.py`
- **问题**: 存在 V1 和 V2 两套 API，需要统一
- **影响**: 维护成本
- **预估工作量**: 4-6 周
- **参考文档**: `tmp/completed/API版本统一重构方案.md`

### AppIcon 图标缺失
- **位置**: `ios/xinlingyisheng/Assets.xcassets/AppIcon.appiconset/`
- **问题**: 13 个尺寸的图标未分配
- **影响**: 应用图标显示不完整
- **预估工作量**: 30 分钟

---

## 已还清

| 问题 | 解决版本 | 解决日期 |
|------|----------|----------|
| EventDetailView Caption 废弃警告 | v1.0 | 2026-02-06 |
| iOS 并发安全警告 (@MainActor) | v1.0 | 2026-02-06 |
| iOS 编译错误 (uploadFile) | v1.0 | 2026-02-06 |
| Python 虚拟环境路径警告 | v1.0 | 2026-02-06 |
| **iOS Caption 废弃警告（SpecialtyDataView + LogoView）** | **v1.0** | **2026-02-08** |

### 说明
- **未使用的依赖（Starscream）**: 经检查，Starscream 正在被 `PressAndHoldVoiceService.swift` 使用，用于 WebSocket 连接，不是未使用的依赖。
- **Python 虚拟环境路径警告**: 经检查，项目配置中不存在相关警告。

---

## 优先级说明

| 优先级 | 处理时机 |
|--------|----------|
| 🔴 高 | 尽快处理，影响构建或核心功能 |
| 🟡 中 | 有空就做，不影响主功能 |
| 🟢 低 | 暂缓，时间允许时处理 |
