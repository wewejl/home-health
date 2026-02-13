//
//  Xcode项目文件更新指南.md
//  灵犀健康
//
//  创建日期: 2026-02-12
//  用途: 指导如何在 Xcode IDE 中添加新创建的 Core 和 Features 目录文件
//

---

## 📋 概述

本文档提供详细的步骤，指导如何在 **Xcode IDE** 中将新创建的 `Core/` 和 `Features/` 目录文件添加到 iOS 项目中。

---

## 🎯 目标

将以下新创建的工程化文件添加到 Xcode 项目，使项目能够正确编译和运行。

---

## 📁 新创建的目录结构

```
ios/xinlingyisheng/xinlingyisheng/
├── Core/              # 新增：核心基础设施
│   ├── Theme/         # 颜色、字体、间距、资源
│   ├── Config/         # 配置、常量
│   ├── Routing/        # 路由
│   ├── Error/          # 错误处理
│   ├── Base/           # 基础类
│   └── Components/    # 共享组件
└── Features/          # 新增：按功能模块重组
    ├── Auth/           # 认证
    ├── Chat/           # 聊天
    ├── Knowledge/       # 知识库
    ├── Medical/         # 医疗（病历夹、医嘱）
    └── Profile/        # 个人中心
```

---

## 🚀 添加步骤（在 Xcode IDE 中操作）

### 步骤 1: 打开项目

1. 打开 **Xcode**
2. 使用 `File → Open...` 打开项目：
   ```
   /Users/zhuxinye/Desktop/project/home-health/ios/xinlingyisheng/xinlingyisheng.xcodeproj
   ```

---

### 步骤 2: 添加 Core 目录

1. 在 **Project Navigator** 中，右键点击 `xinlingyisheng` 文件夹
2. 选择 **Add Files to "xinlingyisheng"**
3. 在弹出的文件选择器中：
   - 找到 `Core/` 目录
   - 全选所有 `.swift` 文件
   - 点击 **Add** 按钮

4. ✅ 确认在弹出的对话框中勾选：
   - ☑️ **Copy items if needed**
   - ☑️ **Create groups**

---

### 步骤 3: 添加 Features 目录

1. 重复步骤 2，为 `Features/` 目录：
   - 找到 `Features/` 目录
   - 全选所有子目录（`Auth/`, `Chat/`, `Knowledge/`, `Medical/`, `Profile/`）
   - 点击 **Add** 按钮

---

### 步骤 4: 验证添加结果

添加完成后，在 Xcode 中验证：

1. 检查 **Project Navigator** 中是否显示新目录
2. 展开 `Core/` 或 `Features/` 查看文件是否都在
3. 尝试打开某个新文件，确认 Xcode 能识别

---

## ⚠️ 注意事项

### 1. 目录大小问题

如果文件很多，Xcode 可能卡顿或超时。建议分批添加：

- 先添加 `Core/Theme/` (5 个文件)
- 再添加 `Core/Config/` (2 个文件)
-  逐步添加其他目录

### 2. 文件引用检查

某些文件可能需要添加到 **Target Membership**：
- 如果编译时提示 "file not found for architecture x86_64"
- 需要在 Xcode 中：
  1. 选中文件
  2. 右侧 **File Inspector** → **Target Membership**
  3. 勾选需要的目标 Target（如 "灵犀医生" 或 "xinlingyishengTests"）

### 3. 不要删除旧文件

**暂时保留原有目录结构**，待新文件添加验证通过后再删除：
- `Views/`、`ViewModels/`、`Services/`、`Models/`
- 避免破坏项目编译

---

## ✅ 验证清单

添加完成后，使用以下命令验证编译：

```bash
xcodebuild -scheme "灵犀医生" -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15' clean build

# 检查编译输出中是否有错误
# 如果编译成功，会显示 "BUILD SUCCEEDED"
```

---

## 📝 文件清单（需要添加到 Xcode）

### Core/Theme/ (5 个文件)

- `AppColors.swift`
- `AppFonts.swift`
- `AppSpacing.swift`
- `AppAssets.swift`

### Core/Config/ (2 个文件)

- `AppConfig.swift`
- `AppConstants.swift`

### Core/Routing (1 个文件)

- `AppRouter.swift`

### Core/Error (2 个文件)

- `AppError.swift`
- `ErrorHandler.swift`

### Core/Base (1 个文件)

- `BaseViewModel.swift`

### Core/Components (6 个文件)

- `AppButton.swift`
- `AppCard.swift`
- `AppEmptyView.swift`
- `AppLoadingView.swift`
- `AppSheet.swift`
- `AppTextField.swift`

### Features/Auth/ (7 个文件)

**Views/**: 3 个
- `LoginView.swift`
- `ProfileSetupView.swift`
- `SplashView.swift`

**ViewModels/**: 2 个
- `LoginViewModel.swift`
- `ProfileSetupViewModel.swift`

**Services/**: 2 个
- `AuthManager.swift`
- `KeychainManager.swift`

### Features/Chat/ (14 个文件)

**Views/**: 6 个
- `ModernConsultationView.swift` (已迁移)
- `SessionHistoryView.swift` (已迁移)
- `HomeView.swift` (已迁移)
- `MyQuestionsView.swift` (已迁移)
- `AskDoctorView.swift` (已迁移)
- `WeChatStyleInputBar.swift` (已迁移)

**ViewModels/**: 4 个
- `ChatSessionViewModel.swift` (已迁移)
- `ChatMessageViewModel.swift` (已迁移)
- `VoiceInputViewModel.swift` (已迁移)
- `UnifiedChatViewModel.swift` (已迁移)

**Services/**: 4 个
- `AIService.swift` (已迁移)
- `UnifiedChatAPIService.swift` (已迁移)
- `ConversationPDFGenerator.swift` (已迁移)
- `SessionStateManager.swift` (已迁移)

### Features/Knowledge/Disease/ (4 个文件)

**Views/**: 4 个
- `DiseaseListView.swift` (已迁移)
- `DiseaseDetailView.swift` (已迁移)
- `MedLiveDiseaseDetailView.swift` (已迁移)
- `DepartmentDetailView.swift` (已迁移)

### Features/Knowledge/Drug/ (2 个文件)

**Views/**: 2 个
- `DrugListView.swift` (已迁移)
- `DrugDetailView.swift` (已迁移)

### Features/Medical/Dossier/ (12 个文件)

**Views/**: 9+ 个
- `EventDetailView.swift` (已迁移)
- `EventDetailWrapperView.swift` (已迁移)
- `PDFViewerSheet.swift` (已迁移)
- `PDFPreviewView.swift` (已迁移)
- `RecordDetailView.swift` (已迁移)
- `VoiceRecorderView.swift` (已迁移)
- `ExportedConversationRow.swift` (已迁移)
- `MedicalDossierView.swift` (已迁移)
- `CreateRecordSheet.swift` (已迁移)
- `MedicalFoldersView.swift` (已迁移)
- `LazyLoadModifier.swift` (已迁移)
- `NoteEditorView.swift` (已迁移)
- `RelatedEventRow.swift` (已迁移)
- `RiskLevelBadge.swift` (已迁移)
- `MergeEventsSheet.swift` (已迁移)
- `TimelineItemView.swift` (已迁移)
- `AIAnalysisCardView.swift` (已迁移)
- `EmptyStateView.swift` (已迁移)

**ViewModels/**: 2 个
- `MedicalDossierViewModel.swift` (已迁移)
- `MedicalFolderViewModel.swift` (已迁移)
- `VoiceTranscriptionViewModel.swift` (已迁移)

**Services/**: 2 个
- `MedicalEventAPIService.swift` (已迁移)
- `PDFGenerator.swift` (已迁移)

### Features/Medical/Orders (6 个文件)

**Views/**: 2 个
- `MedicalOrderListView.swift` (已迁移)
- `TaskCheckInView.swift` (已迁移)

**ViewModels/**: 1 个
- `MedicalOrderViewModel.swift` (已迁移)

**Services/**: 3 个
- `ImageCacheManager.swift` (已迁移)
- `LocalImageManager.swift` (已迁移)
- `ExportedConversationStore.swift` (已迁移)

### Features/Profile (1 个文件)

**Views/**: 1 个
- `ProfileView.swift` (已迁移)

---

## 📊 总计

- **Core/**: 22 个 Swift 文件
- **Features/**: 40+ 个 Swift 文件（已迁移）
- **总计**: 约 **62+ 个文件** 需要添加到 Xcode

---

## 🔗 相关文档

- `docs/iOS代码优化方案v3-工程化版.md` - 完整的工程化方案
- `docs/planning/tech-debt.md` - 技术债务清单

---

*生成日期: 2026-02-12*
*适用版本: Xcode 15.x+
