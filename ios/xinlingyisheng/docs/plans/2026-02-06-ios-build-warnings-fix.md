# iOS 构建警告和错误修复计划

创建时间: 2026-02-06
状态: 待实施

---

## 概述

本文档记录了 iOS 项目构建过程中发现的所有警告和错误，并按优先级提供了修复方案。

---

## 问题清单

### P0 - 编译错误（阻塞构建）

#### 1. uploadFile 方法歧义错误

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/Views/MedicalDossier/RecordDetailView.swift` |
| 行号 | 210 |
| 错误类型 | `ambiguous use of 'uploadFile'` |
| 影响 | **编译失败** |

**根本原因**：

`MedicalFolderViewModel.swift` 中存在两个 `uploadFile` 方法，参数签名几乎相同：

| 行号 | 方法签名 | 返回类型 |
|------|----------|----------|
| 316 | `uploadFile(recordId: String, fileURL: URL, progressHandler: ((Double) -> Void)? = nil)` | `async throws -> MedicalFile` |
| 443 | `uploadFile(recordId: String, fileURL: URL, progress: ((Double) -> Void)? = nil)` | `async -> MedicalFile?` |

调用代码：
```swift
// RecordDetailView.swift:210
_ = await viewModel.uploadFile(recordId: detailRecord.id, fileURL: url)
```

由于两个方法的 `progressHandler` 和 `progress` 参数都有默认值 `nil`，编译器无法确定使用哪个方法。

**修复方案**：

```swift
// 方案 A: 明确使用 throws 版本（推荐）
_ = try? await viewModel.uploadFile(recordId: detailRecord.id, fileURL: url, progressHandler: nil)

// 方案 B: 明确使用可选返回版本
_ = await viewModel.uploadFile(recordId: detailRecord.id, fileURL: url, progress: nil)
```

建议使用方案 A，因为错误处理更加明确。

---

### P1 - 并发警告（潜在运行时问题）

#### 2. MainActor 隔离警告

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/ViewModels/MedicalFolderViewModel.swift` |
| 行号 | 23, 34 |
| 警告 | `main actor-isolated static property 'shared' can not be referenced from a nonisolated context` |

**问题代码**：
```swift
// MedicalFolderViewModel.swift:23
init(apiService: APIService = .shared) {
    self.apiService = apiService
}

// 第 34 行在 makeRequest 方法中
guard let token = AuthManager.shared.token else {
    throw APIError.unauthorized
}
```

**根本原因**：`AuthManager.shared` 是 `@MainActor` 隔离的，但在非隔离的上下文中访问。

**修复方案**：

```swift
// 方案 A: 标记 init 为 @MainActor
@MainActor
init(apiService: APIService = .shared) {
    self.apiService = apiService
}

// 方案 B: 在 makeRequest 中异步获取 token
private func makeRequest<T: Decodable>(
    endpoint: String,
    method: String = "GET",
    body: Data? = nil
) async throws -> T {
    guard let token = await AuthManager.shared.token else {
        throw APIError.unauthorized
    }
    // ...
}
```

---

### P2 - 代码逻辑警告

#### 3. Color(hex:) 非可选类型使用 `??` 操作符

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/Views/MedicalDossier/MedicalFoldersView.swift` |
| 行号 | 225, 282 |
| 警告 | `left side of nil coalescing operator '??' has non-optional type 'Color'` |

**问题代码**：
```swift
// MedicalFoldersView.swift:225
.fill(Color(hex: folder.color) ?? HealingColors.forestMist)

// MedicalFoldersView.swift:282
.fill(Color(hex: folder.color) ?? HealingColors.forestMist)
```

**根本原因**：`Color.init(hex:)` 返回的是非可选的 `Color` 类型，而不是 `Color?`。

定义于 `ModernDesignSystem.swift:107`：
```swift
extension Color {
    init(hex: String) {  // 返回 Color，不是 Color?
        // ...
    }
}
```

**修复方案**：
```swift
// 删除 ?? 后的冗余默认值
.fill(Color(hex: folder.color))
```

---

### P3 - 废弃 API 警告（批量替换）

#### 4. .caption 字体大小废弃

| 属性 | 值 |
|------|-----|
| 影响文件 | 约 20+ 个文件 |
| 警告 | `'caption' is deprecated: 使用 caption1 替代` |

**修复方案**：全局替换 `.caption` → `.caption1`

```bash
# 查找所有使用 .caption 的地方
grep -r "\.caption)" --include="*.swift" .

# 批量替换（使用编辑器全局替换或 sed）
```

#### 5. AVAudioSession.recordPermission 废弃 (iOS 17+)

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/Services/Voice/SimpleSpeechInputService.swift` |
| 行号 | 64, 66, 69 |
| 警告 | `'recordPermission' was deprecated in iOS 17.0` |

**问题代码**：
```swift
// SimpleSpeechInputService.swift:62-69
func requestAuthorization() async -> Bool {
    let audioSession = AVAudioSession.sharedInstance()
    let micStatus = audioSession.recordPermission  // 废弃

    if micStatus == .denied {  // 废弃
        errorMessage = "麦克风权限被拒绝，请在设置中开启"
        return false
    } else if micStatus == .undetermined {  // 废弃
        // ...
    }
}
```

**修复方案**：
```swift
func requestAuthorization() async -> Bool {
    if #available(iOS 17.0, *) {
        let micStatus = AVAudioApplication.shared.recordPermission
        if micStatus == .denied {
            errorMessage = "麦克风权限被拒绝，请在设置中开启"
            return false
        }
        // ...
    } else {
        // 旧版本代码
        let audioSession = AVAudioSession.sharedInstance()
        let micStatus = audioSession.recordPermission
        // ...
    }
}
```

#### 6. AppColor 废弃

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/Components/VerificationCodeInput.swift` |
| 行号 | 183 |
| 警告 | `'AppColor' is deprecated: 使用 DXYColors 替代` |

**问题代码**：
```swift
// VerificationCodeInput.swift:183
emptyBorder: AppColor.borderLight,
```

**修复方案**：
```swift
emptyBorder: DXYColors.borderLight,  // 或 HealingColorTheme.borderLight
```

---

### P4 - 低优先级警告

#### 7. App Icon 未分配子项

| 属性 | 值 |
|------|-----|
| 文件 | `Assets.xcassets/AppIcon.appiconset` |
| 警告 | `The app icon set "AppIcon" has 13 unassigned children` |

**说明**：iPad 图标未配置，不影响 iPhone 应用运行。如果需要支持 iPad，在 Xcode 中配置相应的 iPad 图标尺寸。

#### 8. ColorScheme 废弃

| 属性 | 值 |
|------|-----|
| 文件 | `xinlingyisheng/Views/ColorSchemeSelector.swift` |
| 行号 | 4, 54 |
| 警告 | `'ColorScheme' is deprecated: 使用 DXYColors 替代` |

**说明**：已有注释说明统一使用治愈系颜色，该页面可能已废弃或用于内部测试。

---

## 修复顺序建议

1. **P0** - 修复 uploadFile 歧义（阻塞编译）
2. **P1** - 修复并发警告（运行时安全性）
3. **P2** - 修复 Color?? 冗余（代码清理）
4. **P3** - 批量修复废弃 API（未来兼容性）
5. **P4** - 低优先级（可选）

---

## 验收标准

修复完成后应满足：
- [ ] 构建成功，无编译错误
- [ ] 并发警告清除
- [ ] 代码逻辑警告清除
- [ ] 废弃 API 警告清除（除明确标记为兼容保留的）
- [ ] 功能测试通过（文件上传、语音输入等）
