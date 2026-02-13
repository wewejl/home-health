# iOS 编译错误修复计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 修复 iOS 项目编译错误，使项目能够成功编译

**当前状态:** 项目在移除 Core/ 和 Features/ 后有约 15 个编译错误

**架构策略:** 不创建新的目录结构，而是在现有代码基础上修复问题

---

## 错误分类

### 1. DXYColors 缺失 (约 8 个错误)
- `DiagnosisSummaryCard.swift:328` - cannot find 'DXYColors'
- `AIAnalysisCardView.swift:311` - cannot find 'DXYColors'
- `EmptyStateView.swift:79` - cannot find 'DXYColors'
- `EventCardView.swift:199` - cannot find 'DXYColors'
- `LazyLoadModifier.swift:155` - cannot find 'DXYColors'
- `TimelineItemView.swift:359` - cannot find 'DXYColors'
- `UnifiedEmptyStateView.swift:104,109,114` - cannot find 'DXYColors'

**修复方式:** 检查 DXYColors 的定义位置，修复引用

### 2. MedicalDossierViewModel 缺失 (约 4 个错误)
- `MergeEventsSheet.swift:257,6` - cannot find 'MedicalDossierViewModel'
- `NoteEditorView.swift:267,13` - cannot find 'MedicalDossierViewModel'

**修复方式:** 恢复缺失的 ViewModel 或修复引用

### 3. ViewBuilder return 语法错误 (约 3 个错误)
- `AIAnalysisCardView.swift:307` - cannot use explicit 'return'
- `EventCardView.swift:194` - cannot use explicit 'return'
- `MergeEventsSheet.swift:254` - cannot use explicit 'return'
- `NoteEditorView.swift:264` - cannot use explicit 'return'

**修复方式:** 移除 ViewBuilder 中的 return 语句或使用正确的语法

### 4. 类型转换错误 (1 个错误)
- `DiagnosisSummaryCard.swift:309` - cannot convert 'DiagnosisCard' to 'AgentDiagnosisCard'

**修复方式:** 修复类型转换或更改参数类型

### 5. API 参数错误 (2 个错误)
- `EnhancedChatInputBar.swift:318` - extra argument 'uiComponents'
- `EnhancedChatInputBar.swift:316` - missing argument 'displayName'

**修复方式:** 修复 API 调用参数

---

## 任务列表

### Task 1: 修复 DXYColors 引用问题

**Files:**
- Check: `xinlingyisheng/Theme/*.swift` - 查找 DXYColors 定义
- Modify: 所有引用 DXYColors 但编译失败的文件

**Step 1: 查找 DXYColors 定义**

```bash
grep -r "DXYColors" xinlingyisheng/Theme/ --include="*.swift"
```

**Step 2: 根据定义位置修复引用**

如果 DXYColors 定义在某个文件中，确保引用它的文件正确导入

**Step 3: 编译验证**

```bash
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build 2>&1 | grep -c "cannot find 'DXYColors'"
```

Expected: 错误数量从 8 减少到 0

**Step 4: Commit**

```bash
git add xinlingyisheng/Theme/ xinlingyisheng/Components/
git commit -m "fix: restore DXYColors references"
```

---

### Task 2: 恢复缺失的 MedicalDossierViewModel

**Files:**
- Create: `xinlingyisheng/ViewModels/MedicalDossierViewModel.swift`

**Step 1: 检查 git 历史中的 MedicalDossierViewModel**

```bash
git log --all --full-history --source -- "*MedicalDossierViewModel.swift" | head -20
```

**Step 2: 从 git 恢复文件**

```bash
git checkout HEAD~1 -- xinlingyisheng/ViewModels/MedicalDossierViewModel.swift
```

**Step 3: 编译验证**

```bash
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build 2>&1 | grep -c "cannot find 'MedicalDossierViewModel'"
```

Expected: 错误数量从 4 减少到 0

**Step 4: Commit**

```bash
git add xinlingyisheng/ViewModels/MedicalDossierViewModel.swift
git commit -m "fix: restore MedicalDossierViewModel"
```

---

### Task 3: 修复 ViewBuilder return 语法错误

**Files:**
- Modify: `xinlingyisheng/Components/MedicalDossier/AIAnalysisCardView.swift:307`
- Modify: `xinlingyisheng/Components/MedicalDossier/EventCardView.swift:194`
- Modify: `xinlingyisheng/Components/MedicalDossier/MergeEventsSheet.swift:254`
- Modify: `xinlingyisheng/Components/MedicalDossier/NoteEditorView.swift:264`

**Step 1: 读取 AIAnalysisCardView.swift 第 300-315 行**

**Step 2: 修复 ViewBuilder 中的 return 语句**

ViewBuilder 中不能使用显式 return，需要移除或改用其他语法

**Step 3: 逐个修复其他三个文件的相同问题**

**Step 4: 编译验证**

```bash
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build 2>&1 | grep -c "cannot use explicit 'return'"
```

Expected: 错误数量从 3 减少到 0

**Step 5: Commit**

```bash
git add xinlingyisheng/Components/MedicalDossier/
git commit -m "fix: remove explicit return from ViewBuilder"
```

---

### Task 4: 修复 DiagnosisCard 类型转换错误

**Files:**
- Modify: `xinlingyisheng/Components/Diagnosis/DiagnosisSummaryCard.swift:309`

**Step 1: 读取错误上下文**

查看第 309 行及其周围的代码

**Step 2: 修复类型转换**

将 `DiagnosisCard` 正确转换为 `AgentDiagnosisCard` 或更改参数类型

**Step 3: 编译验证**

**Step 4: Commit**

---

### Task 5: 修复 API 参数错误

**Files:**
- Modify: `xinlingyisheng/Components/PhotoCapture/EnhancedChatInputBar.swift:316,318`

**Step 1: 检查 SF Symbols API 文档**

确认正确的 API 调用方式

**Step 2: 修复参数**

移除额外参数或添加缺失参数

**Step 3: 编译验证**

**Step 4: Commit**

---

### Task 6: 最终编译验证

**Step 1: 完整清理后编译**

```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/xinlingyisheng-*
xcodebuild -project xinlingyisheng.xcodeproj -scheme "灵犀医生" -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' clean build
```

**Step 2: 验证编译成功**

Expected: **BUILD SUCCEEDED**

**Step 3: 如有错误，记录并继续修复**

---

## 注意事项

1. **每次修改后立即编译验证** - 不积累多个错误
2. **使用 git 频繁提交** - 每个任务一提交
3. **不创建新目录结构** - 在现有基础上修复
4. **保留所有现有功能** - 只修复编译问题

---

## 执行顺序

按以下顺序执行任务：
1. Task 1 (DXYColors) - 最基础，影响最多文件
2. Task 2 (MedicalDossierViewModel) - 恢复缺失类
3. Task 3 (ViewBuilder return) - 语法修复
4. Task 4 (类型转换) - 单独修复
5. Task 5 (API 参数) - 单独修复
6. Task 6 (最终验证) - 确保全部通过
