# P3 废弃 API 警告修复实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 iOS 项目中的 282 个 P3 级别的废弃 API 警告（.caption、AppColor、ColorScheme、recordPermission）

**Architecture:** 批量全局替换 .caption → .caption1（267 处），逐文件替换 AppColor → DXYColors（7 处），添加 iOS 17 版本检查修复 recordPermission（4 处），评估是否删除 ColorSchemeSelector（4 处）

**Tech Stack:** Swift 5.9+, SwiftUI, Font API, AVFoundation

---

## 修复概览

| 类别 | 数量 | 策略 | 优先级 |
|------|------|------|--------|
| .caption → .caption1 | 267 | 全局批量替换 | P3.1 |
| AppColor → DXYColors | 7 | 逐文件替换（同名映射） | P3.2 |
| recordPermission | 4 | 添加 iOS 17 版本检查 | P3.3 |
| ColorScheme | 4 | 评估删除（已统一颜色） | P3.4 |

**总计**: 282 个警告

---

## P3.1: 批量替换 .caption → .caption1 (267 处)

**影响文件**: 30 个文件

**完整文件列表**:
```
Components/Diagnosis/DiagnosisSummaryCard.swift
Components/EventLinkBanner.swift
Components/MedicalDossier/AIAnalysisCardView.swift
Components/MedicalDossier/EventCardView.swift
Components/MedicalDossier/MergeEventsSheet.swift
Components/MedicalDossier/RelatedEventRow.swift
Components/MedicalDossier/RiskLevelBadge.swift
Components/MedicalDossier/TimelineItemView.swift
Components/PhotoCapture/ChatNavBarV2.swift
Components/PhotoCapture/EnhancedChatInputBar.swift
Components/PhotoCapture/PhotoActionSheet.swift
Components/StreamingStatusView.swift
Views/DepartmentDetailView.swift
Views/DiseaseDetailView.swift
Views/DiseaseListView.swift
Views/DrugDetailView.swift
Views/DrugListView.swift
Views/HomeView.swift
Views/LoginView.swift
Views/MedicalDossier/CreateRecordSheet.swift
Views/MedicalDossier/EventDetailView.swift
Views/MedicalOrderListView.swift
Views/MedLiveDiseaseDetailView.swift
Views/ModernConsultationView.swift
Views/MyQuestionsView.swift
Views/ProfileView.swift
Views/SessionHistoryView.swift
Views/TaskCheckInView.swift
Views/WeChatStyleInputBar.swift
```

### Task 1: 使用 sed 批量替换 .caption

**Files:**
- Modify: 以上 30 个文件

**Step 1: 备份当前状态**

```bash
cd ios/xinlingyisheng
git stash push -m "backup before caption replacement"
```

**Step 2: 执行批量替换**

```bash
cd xinlingyisheng
find . -name "*.swift" -type f -exec sed -i '' 's/\.caption/.caption1/g' {} \;
```

**Step 3: 验证替换结果**

```bash
cd ..
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -c "'caption' is deprecated"
```

Expected: `0`（无 .caption 废弃警告）

**Step 4: 检查构建成功**

```bash
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep "BUILD"
```

Expected: `** BUILD SUCCEEDED **`

**Step 5: 提交**

```bash
git add -A
git commit -m "fix(ui): replace deprecated .caption with .caption1 (267 occurrences)

- Font.caption is deprecated in favor of Font.caption1
- Updated 30 Swift files across Components and Views
- Verified build still succeeds after replacement

Resolves 267 P3 deprecation warnings."
```

---

## P3.2: 替换 AppColor → DXYColors (7 处)

**影响文件**:
- `Components/PhoneNumberTextField.swift` (4 处)
- `Components/VerificationCodeInput.swift` (3 处)

**AppColor → DXYColors 映射表**（同名直接映射）:

| AppColor 属性 | DXYColors 属性 |
|--------------|----------------|
| `AppColor.primaryText` | `DXYColors.textPrimary` |
| `AppColor.secondaryText` | `DXYColors.textSecondary` |
| `AppColor.background` | `DXYColors.background` |
| `AppColor.primaryPurple` | `DXYColors.primaryPurple` |
| `AppColor.teal` | `DXYColors.teal` |
| `AppColor.orange` | `DXYColors.orange` |
| `AppColor.errorRed` | `DXYColors.errorRed` |

### Task 2: 修复 PhoneNumberTextField

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Components/PhoneNumberTextField.swift`

**Step 1: 查看当前使用**

```bash
grep -n "AppColor" xinlingyisheng/xinlingyisheng/Components/PhoneNumberTextField.swift
```

Expected: 4 处使用

**Step 2: 替换 AppColor 为 DXYColors**

```bash
sed -i '' 's/AppColor\./DXYColors./g' xinlingyisheng/xinlingyisheng/Components/PhoneNumberTextField.swift
```

**Step 3: 验证修改**

```bash
grep -n "DXYColors\." xinlingyisheng/xinlingyisheng/Components/PhoneNumberTextField.swift
```

Expected: 4 处 DXYColors 使用

### Task 3: 修复 VerificationCodeInput

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Components/VerificationCodeInput.swift`

**Step 1: 替换 AppColor 为 DXYColors**

```bash
sed -i '' 's/AppColor\./DXYColors./g' xinlingyisheng/xinlingyisheng/Components/VerificationCodeInput.swift
```

**Step 2: 验证修改**

```bash
grep -n "DXYColors\." xinlingyisheng/xinlingyisheng/Components/VerificationCodeInput.swift
```

Expected: 3 处 DXYColors 使用

### Task 4: 验证 AppColor 修复

**Step 1: 构建检查**

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -c "'AppColor' is deprecated"
```

Expected: `0`

**Step 2: 提交**

```bash
git add xinlingyisheng/xinlingyisheng/Components/PhoneNumberTextField.swift xinlingyisheng/xinlingyisheng/Components/VerificationCodeInput.swift
git commit -m "fix(ui): replace deprecated AppColor with DXYColors (7 occurrences)

- PhoneNumberTextField: 4 replacements
- VerificationCodeInput: 3 replacements
- Direct property name mapping (AppColor.xxx → DXYColors.xxx)

Resolves 7 P3 deprecation warnings."
```

---

## P3.3: 修复 recordPermission 废弃 (4 处)

**影响文件**:
- `xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift` (4 处，去重后 2 处)

**警告内容**:
- `'recordPermission' was deprecated in iOS 17.0: Please use AVAudioApplication recordPermission`
- `'denied'` / `'undetermined'` 枚举值废弃

### Task 5: 查看 PressAndHoldVoiceService 中的使用

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift`

**Step 1: 查看当前代码**

```bash
grep -n -A5 -B5 "recordPermission" xinlingyisheng/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift | head -30
```

Expected: 看到第 226 和 246 行的使用

### Task 6: 添加 iOS 17 版本检查

**Step 1: 修改权限检查代码**

在第 226 行附近，添加 iOS 17 版本检查：

```swift
// 修改前
private func checkMicrophonePermission() -> Bool {
    let permission = AVAudioSession.sharedInstance().recordPermission
    return permission == .granted
}

// 修改后
private func checkMicrophonePermission() -> Bool {
    if #available(iOS 17.0, *) {
        let permission = AVAudioApplication.shared.recordPermission
        return permission == .granted
    } else {
        let permission = AVAudioSession.sharedInstance().recordPermission
        return permission == .granted
    }
}
```

**Step 2: 修改权限请求代码**

类似地更新权限请求方法，使用 iOS 17 版本检查。

**Step 3: 验证修复**

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -c "'recordPermission' was deprecated"
```

Expected: `0`

**Step 4: 提交**

```bash
git add xinlingyisheng/xinlingyisheng/xinlingyisheng/Services/Voice/PressAndHoldVoiceService.swift
git commit -m "fix(ios): use AVAudioApplication for recordPermission on iOS 17+

- Added @available(iOS 17.0, *) version checks
- Use AVAudioApplication.shared.recordPermission on iOS 17+
- Fall back to AVAudioSession for older iOS versions
- Fixes deprecated recordPermission, denied, undetermined warnings

Resolves 4 P3 deprecation warnings."
```

---

## P3.4: 处理 ColorScheme 废弃 (4 处)

**影响文件**:
- `Views/ColorSchemeSelector.swift` (4 处)

**警告内容**: `'ColorScheme' is deprecated: 使用 DXYColors 替代 - 已统一使用治愈系颜色`

### Task 7: 评估 ColorSchemeSelector 使用情况

**Step 1: 检查是否有其他地方使用**

```bash
grep -r "ColorSchemeSelector" --include="*.swift" xinlingyisheng/ | grep -v "ColorSchemeSelector.swift"
```

Expected: 仅在 Preview 中使用（行 94）

**Step 2: 检查 ColorScheme 的定义**

```bash
grep -n -A10 "enum ColorScheme\|struct ColorScheme" xinlingyisheng/xinlingyisheng/Theme/HealingColorTheme.swift | head -20
```

### Task 8: 决定处理方案

**选项 A**: 删除 ColorSchemeSelector（推荐）
- 已统一使用治愈系颜色
- 仅在 Preview 中使用
- 不影响实际功能

**选项 B**: 更新为使用 DXYColors
- 保留视图但更新实现
- 添加 @available deprecated 注解

### Task 9: 执行删除方案

**Step 1: 删除 ColorSchemeSelector.swift 文件**

```bash
rm xinlingyisheng/xinlingyisheng/Views/ColorSchemeSelector.swift
```

**Step 2: 更新 HomeView.swift 移除相关引用（如果有）**

**Step 3: 验证构建**

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator build 2>&1 | grep -c "'ColorScheme' is deprecated"
```

Expected: `0`

**Step 4: 提交**

```bash
git add xinlingyisheng/xinlingyisheng/Views/ColorSchemeSelector.swift
git commit -m "refactor(ui): remove unused ColorSchemeSelector

- Color system has been unified to use DXYColors
- Selector was only used in Preview
- No functional impact on the application

Resolves 4 P3 deprecation warnings."
```

---

## 验证步骤

**所有任务完成后执行：**

### Final Step 1: 完整构建

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator clean build 2>&1 | tee /tmp/final_build.log
```

### Final Step 2: 统计剩余 P3 警告

```bash
echo "=== P3 废弃警告统计 ===" && \
echo "caption: $(grep -c "'caption' is deprecated" /tmp/final_build.log || echo 0)" && \
echo "AppColor: $(grep -c "'AppColor' is deprecated" /tmp/final_build.log || echo 0)" && \
echo "ColorScheme: $(grep -c "'ColorScheme' is deprecated" /tmp/final_build.log || echo 0)" && \
echo "recordPermission: $(grep -c "'recordPermission' was deprecated" /tmp/final_build.log || echo 0)"
```

Expected: 全部为 `0`

### Final Step 3: 运行应用测试

1. 在模拟器中启动应用
2. 验证字体显示正常（.caption1 替换后）
3. 验证颜色显示正常（DXYColors 替换后）
4. 测试语音权限请求（iOS 17 适配后）
5. 检查所有主要 UI 页面无视觉异常

---

## 最终提交

```bash
git commit --amend -m "fix(ios): resolve all P3 deprecation warnings (282 total)

P3.1: .caption → .caption1 (267 occurrences)
- Replaced Font.caption with Font.caption1 across 30 files
- Font.caption is deprecated in favor of caption1

P3.2: AppColor → DXYColors (7 occurrences)
- Updated PhoneNumberTextField (4 replacements)
- Updated VerificationCodeInput (3 replacements)
- Direct property name mapping

P3.3: recordPermission iOS 17+ adaptation (4 occurrences)
- Use AVAudioApplication.shared.recordPermission on iOS 17+
- Fall back to AVAudioSession for older versions
- Added @available(iOS 17.0, *) version checks

P3.4: ColorScheme removal (4 occurrences)
- Removed unused ColorSchemeSelector view
- Color system unified to DXYColors

Total deprecation warnings resolved: 282
Remaining warnings: P2 (code logic), P4 (resources/config)"
```

---

## 文档更新

修改 `docs/plans/2026-02-06-ios-build-warnings-fix.md`：

```markdown
## P3: 废弃 API 警告 ✅ 已修复

| 类别 | 数量 | 状态 |
|------|------|------|
| .caption → .caption1 | 267 | ✅ 已修复 |
| AppColor → DXYColors | 7 | ✅ 已修复 |
| ColorScheme 删除 | 4 | ✅ 已修复 |
| recordPermission | 4 | ✅ 已修复 |
| **总计** | **282** | **✅ 已完成** |
```
