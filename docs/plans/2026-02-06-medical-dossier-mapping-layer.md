# 病历资料夹映射层重构实施计划

**创建日期**: 2026-02-06
**设计文档**: `docs/病历页面逻辑分析报告.md` 第六章方案C
**预估总工时**: 约 7 小时

---

## 任务拆分清单

### P0 - 紧急修复（必须完成）

#### 任务 1: 创建 DepartmentMapping.swift
**文件**: `ios/xinlingyisheng/xinlingyisheng/Services/Mapping/DepartmentMapping.swift`
**工时**: 15 分钟

```swift
import Foundation

/// 科室类型前后端映射
public enum DepartmentMapping {

    /// 后端枚举值 → 前端枚举值 映射表
    private static let backendToFrontend: [String: DepartmentType] = [
        "derma": .dermatology,
        "cardio": .cardiology,
        "ortho": .orthopedics,
        "neuro": .neurology,
        "gastro": .gastroenterology,
        "general": .general,
        "respiratory": .respiratory,
        "endo": .endocrinology
    ]

    /// 前端枚举值 → 后端枚举值 映射表（用于API请求）
    private static let frontendToBackend: [DepartmentType: String] = [
        .dermatology: "derma",
        .cardiology: "cardio",
        .orthopedics: "ortho",
        .neurology: "neuro",
        .gastroenterology: "gastro",
        .general: "general",
        .respiratory: "respiratory",
        .endocrinology: "endo"
    ]

    /// 从后端值解析
    public static func fromBackend(_ rawValue: String) -> DepartmentType {
        backendToFrontend[rawValue] ?? .general
    }

    /// 转换为后端值
    public static func toBackend(_ type: DepartmentType) -> String {
        frontendToBackend[type] ?? "general"
    }
}
```

**验证步骤**:
1. 创建 `Services/Mapping/` 目录
2. 创建文件并粘贴代码
3. 编译无错误

---

#### 任务 2: 创建 EventStatusMapping.swift
**文件**: `ios/xinlingyisheng/xinlingyisheng/Services/Mapping/EventStatusMapping.swift`
**工时**: 10 分钟

```swift
import Foundation

/// 事件状态前后端映射
public enum EventStatusMapping {

    private static let backendToFrontend: [String: EventStatus] = [
        "active": .active,
        "in_progress": .inProgress,
        "completed": .completed,
        "exported": .exported,
        "archived": .archived
    ]

    private static let frontendToBackend: [EventStatus: String] = [
        .active: "active",
        .inProgress: "in_progress",
        .completed: "completed",
        .exported: "exported",
        .archived: "archived"
    ]

    public static func fromBackend(_ rawValue: String) -> EventStatus {
        backendToFrontend[rawValue] ?? .active
    }

    public static func toBackend(_ status: EventStatus) -> String {
        frontendToBackend[status] ?? "active"
    }
}
```

**验证步骤**:
1. 创建文件
2. 编译无错误

---

#### 任务 3: 添加 EventStatus.active 枚举值
**文件**: `ios/xinlingyisheng/xinlingyisheng/Models/MedicalDossierModels.swift`
**工时**: 10 分钟

修改 EventStatus 枚举（第 91-114 行）：

```swift
enum EventStatus: String, Codable, CaseIterable {
    case active = "active"           // ✅ 新增：匹配后端
    case inProgress = "in_progress"
    case completed = "completed"
    case exported = "exported"
    case archived = "archived"

    var displayName: String {
        switch self {
        case .active: return "活跃"      // 新增
        case .inProgress: return "进行中"
        case .completed: return "已完成"
        case .exported: return "已导出"
        case .archived: return "已归档"
        }
    }

    var color: Color {
        switch self {
        case .active: return Color.blue       // 新增
        case .inProgress: return DossierColors.statusInProgress
        case .completed: return DossierColors.statusCompleted
        case .exported: return DossierColors.statusExported
        case .archived: return DXYColors.textTertiary
        }
    }
}
```

**验证步骤**:
1. 修改枚举定义
2. 更新 displayName 和 color
3. 编译无错误

---

#### 任务 4: 修改 MedicalEventAPIService 使用 Mapper
**文件**: `ios/xinlingyisheng/xinlingyisheng/Services/MedicalEventAPIService.swift`
**工时**: 20 分钟

修改第 292-310 行的 `toMedicalEvent()` 方法：

```swift
extension MedicalEventDTO {
    func toMedicalEvent() -> MedicalEvent {
        MedicalEvent(
            id: String(id),
            title: title,
            department: DepartmentMapping.fromBackend(agent_type),  // ✅ 使用 mapper
            status: EventStatusMapping.fromBackend(status),          // ✅ 使用 mapper
            createdAt: created_at,
            updatedAt: updated_at,
            summary: summary ?? "",
            riskLevel: DossierRiskLevel(rawValue: risk_level) ?? .low,
            sessions: [],
            attachments: [],
            aiAnalysis: nil,
            notes: nil,
            exportedAt: nil
        )
    }
}
```

同时修改 `MedicalEventDetailDTO` 扩展（第 312-369 行）：

```swift
extension MedicalEventDetailDTO {
    func toMedicalEvent() -> MedicalEvent {
        // ... 省略前面的代码

        return MedicalEvent(
            id: String(id),
            title: title,
            department: DepartmentMapping.fromBackend(agent_type),  // ✅ 使用 mapper
            status: EventStatusMapping.fromBackend(status),          // ✅ 使用 mapper
            // ... 其余代码不变
        )
    }
}
```

**验证步骤**:
1. 导入 Mapper（如果需要）
2. 替换两处 rawValue 解码为 mapper 调用
3. 编译无错误

---

#### 任务 5: 添加删除/归档 API 方法
**文件**: `ios/xinlingyisheng/xinlingyisheng/Services/MedicalEventAPIService.swift`
**工时**: 20 分钟

在 `MedicalEventAPIService` 类中添加（第 233 行后）：

```swift
// MARK: - Event Management

/// 删除病历事件
func deleteEvent(eventId: String) async throws {
    let endpoint = APIConfig.Endpoints.medicalEventDetail(eventId: eventId) + "?confirm=true"
    let _: EmptyResponse = try await makeRequest(
        endpoint: endpoint,
        method: "DELETE",
        requiresAuth: true
    )
}

/// 归档病历事件
func archiveEvent(eventId: String) async throws -> MedicalEventDTO {
    let endpoint = APIConfig.Endpoints.medicalEventDetail(eventId: eventId) + "/archive"
    return try await makeRequest(
        endpoint: endpoint,
        method: "POST",
        requiresAuth: true
    )
}
```

**验证步骤**:
1. 在 Note Management 代码块后添加新代码
2. 编译无错误

---

#### 任务 6: 修改 ViewModel 删除/归档方法
**文件**: `ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalDossierViewModel.swift`
**工时**: 15 分钟

替换第 117-131 行的方法：

```swift
/// 删除事件（异步，同步到后端）
func deleteEvent(_ event: MedicalEvent) async {
    do {
        try await MedicalEventAPIService.shared.deleteEvent(eventId: event.id)
        withAnimation {
            events.removeAll { $0.id == event.id }
            applyFilters(searchText: searchText, filter: selectedFilter)
        }
    } catch {
        self.errorMessage = "删除失败: \(error.localizedDescription)"
    }
}

/// 归档事件（异步，同步到后端）
func archiveEvent(_ event: MedicalEvent) async {
    do {
        let updated = try await MedicalEventAPIService.shared.archiveEvent(eventId: event.id)
        withAnimation {
            if let index = events.firstIndex(where: { $0.id == event.id }) {
                events[index] = updated.toMedicalEvent()
            }
            applyFilters(searchText: searchText, filter: selectedFilter)
        }
    } catch {
        self.errorMessage = "归档失败: \(error.localizedDescription)"
    }
}
```

**注意**: 调用这些方法的 UI 代码也需要更新为 async/await。

**验证步骤**:
1. 替换方法实现
2. 查找调用处并更新为 await
3. 编译无错误

---

### P1 - 近期修复

#### 任务 7: 修复 SmartAggregate 参数
**文件**: `ios/xinlingyisheng/xinlingyisheng/Services/AIService.swift`
**工时**: 15 分钟

修改第 105-119 行的 `smartAggregate` 方法：

```swift
func smartAggregate(
    sessionId: String,
    sessionType: String,
    department: String? = nil,
    chiefComplaint: String? = nil
) async throws -> SmartAggregateResponse {
    // department 改为必填，使用映射后的值
    let dept: String
    if let department = department {
        dept = department
    } else {
        // 默认值使用后端格式
        dept = "general"
    }

    let request = SmartAggregateRequest(
        session_id: sessionId,
        session_type: sessionType,
        department: dept,  // ✅ 确保传递后端格式的值
        chief_complaint: chiefComplaint
    )

    let data = try JSONEncoder().encode(request)
    return try await makeRequest(endpoint: "/ai/smart-aggregate", method: "POST", body: data)
}
```

**验证步骤**:
1. 修改方法添加默认值处理
2. 编译无错误
3. 运行时验证 API 调用成功

---

#### 任务 8: 添加错误 UI 组件
**文件**: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalDossierView.swift`
**工时**: 30 分钟

1. 添加 ErrorBannerView 组件：

```swift
struct ErrorBannerView: View {
    let message: String
    let onDismiss: () -> Void

    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.white)
            Text(message)
                .font(.subheadline)
                .foregroundColor(.white)
            Spacer()
            Button(action: onDismiss) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.white.opacity(0.8))
            }
        }
        .padding()
        .background(Color.red.gradient)
        .cornerRadius(12)
        .shadow(radius: 4)
        .padding(.horizontal)
    }
}
```

2. 修改 `contentSection` 显示错误：

```swift
@ViewBuilder
private func contentSection(layout: AdaptiveLayout) -> some View {
    // 先显示错误（如果有）
    if let errorMessage = viewModel.errorMessage {
        ErrorBannerView(message: errorMessage) {
            viewModel.clearError()
        }
        .transition(.move(edge: .top).combined(with: .opacity()))
    }

    // 然后显示内容
    Group {
        if viewModel.isLoading {
            HealingDossierLoadingView(layout: layout)
        } else if viewModel.events.isEmpty {
            HealingDossierEmptyStateView(layout: layout)
        } else if viewModel.filteredEvents.isEmpty {
            HealingDossierSearchEmptyView(...)
        } else {
            eventListView(layout: layout)
        }
    }
}
```

3. 在 ViewModel 添加 `clearError()` 方法。

**验证步骤**:
1. 添加组件代码
2. 修改 contentSection
3. 运行时验证错误横幅显示

---

### P2 - 长期改进

#### 任务 9: 编写单元测试
**文件**: `ios/xinlingyisheng/xinlingyishengTests/MappingTests.swift`
**工时**: 1 小时

```swift
import XCTest
@testable import xinlingyisheng

class DepartmentMappingTests: XCTestCase {

    func testBackendToFrontendMapping() {
        XCTAssertEqual(DepartmentMapping.fromBackend("derma"), .dermatology)
        XCTAssertEqual(DepartmentMapping.fromBackend("cardio"), .cardiology)
        XCTAssertEqual(DepartmentMapping.fromBackend("general"), .general)
        XCTAssertEqual(DepartmentMapping.fromBackend("unknown"), .general)  // fallback
    }

    func testFrontendToBackendMapping() {
        XCTAssertEqual(DepartmentMapping.toBackend(.dermatology), "derma")
        XCTAssertEqual(DepartmentMapping.toBackend(.cardiology), "cardio")
        XCTAssertEqual(DepartmentMapping.toBackend(.general), "general")
    }
}

class EventStatusMappingTests: XCTestCase {

    func testBackendToFrontendMapping() {
        XCTAssertEqual(EventStatusMapping.fromBackend("active"), .active)
        XCTAssertEqual(EventStatusMapping.fromBackend("completed"), .completed)
        XCTAssertEqual(EventStatusMapping.fromBackend("unknown"), .active)  // fallback
    }
}
```

**验证步骤**:
1. 创建测试文件
2. 运行测试通过

---

#### 任务 10: 时间线按需加载（可选）
**文件**: `ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalDossierViewModel.swift`
**工时**: 2 小时

此任务需要后端配合，暂不实施。

---

## 实施顺序建议

```
第 1 天（P0 任务，约 1.5 小时）
├── 任务 1: 创建 DepartmentMapping.swift (15min)
├── 任务 2: 创建 EventStatusMapping.swift (10min)
├── 任务 3: 添加 EventStatus.active (10min)
├── 任务 4: 修改 API Service 使用 Mapper (20min)
├── 任务 5: 添加删除/归档 API (20min)
└── 任务 6: 修改 ViewModel (15min)

第 2 天（P1 任务，约 1 小时）
├── 任务 7: 修复 SmartAggregate (15min)
└── 任务 8: 添加错误 UI (30min)

第 3 天（P2 任务，可选）
└── 任务 9: 单元测试 (1 小时)
```

---

## 验收标准

完成 P0 任务后，应满足：

1. ✅ 后端返回 `derma` 时，前端正确显示为皮肤科
2. ✅ 后端返回 `active` 状态时，前端正确解析
3. ✅ 删除事件后，刷新页面数据确实被删除
4. ✅ 归档事件后，状态正确更新
5. ✅ 编译无警告
6. ✅ 运行时无崩溃

---

## 风险与注意事项

1. **UI 调用更新**: 任务 6 修改 ViewModel 方法为 async 后，所有调用处需要更新
2. **数据迁移**: 现有本地数据可能有旧的枚举值，需考虑兼容
3. **测试覆盖**: 修改核心映射逻辑后建议充分测试
