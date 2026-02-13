# iOS 架构重构 - 执行计划

> **创建日期**: 2026-02-14
> **当前文件总数**: 256 个 Swift 文件

---

## 📊 当前项目结构分析

### 顶层目录 (16个)

| 目录 | 文件数 | 用途 |
|------|--------|------|
| Components/ | 51 | 通用组件 |
| Models/ | 6 | 数据模型 |
| Services/ | 14 | 服务层 |
| ViewModels/ | 7 | 视图模型 |
| Views/ | 36 | 视图 |
| Security/ | 3 | 安全相关 |
| Theme/ | 3 | 主题相关 |
| Network/ | 2 | 网络相关 |
| Utilities/ | 7 | 工具类 |
| Utils/ | 25 | 其他工具 |
| xinlingyisheng/ | 1 | 主目录（ContentView 等）|
| xinlingyishengApp.swift | 1 | 应用入口 |
| Assets.xcassets | 1 | 资源 |
| Info.plist | 1 | 配置 |
| LaunchScreen.storyboard | 1 | 故事板 |

**总计**: 256 个文件（不含 Assets.xcassets 内部资源）

---

## 🎯 目标结构

```
xinlingyisheng/
├── Core/                    # 新建：核心基础设施
│   ├── Theme/             # 颜色、字体、间距系统
│   ├── Config/            # 配置、常量
│   ├── Routing/            # 路由管理
│   ├── Error/              # 错误类型和处理
│   ├── Base/               # 基础类
│   └── Components/         # 共享组件
├── Features/               # 新建：按功能模块组织
│   ├── Auth/              # 认证模块
│   ├── Consultation/        # 问诊模块
│   ├── Knowledge/          # 知识库模块
│   │   ├── Disease/       # 疾病
│   │   └── Drug/          # 药品
│   ├── Medical/            # 医疗模块
│   │   ├── Dossier/      # 病历夹
│   │   └── Orders/       # 医嘱
│   └── Profile/            # 个人中心
├── Shared/                 # 新建：共享资源
│   ├── Components/         # 跨模块通用组件
│   └── Resources/         # 图片、颜色、字体等
└── Resources/               # 保留：根级资源
    ├── Assets.xcassets
    └── (其他现有文件保持不变)
```

---

## 📋 文件迁移详细计划

### 阶段 1: Core 层创建 (预计 2-3 天)

#### Core/Theme/ (新建 - 4 个文件)
- [ ] `AppColors.swift` - 统一颜色系统
- [ ] `AppFonts.swift` - 统一字体系统
- [ ] `AppSpacing.swift` - 统一间距系统
- [ ] `AppAssets.swift` - 图片资源管理

**来源**:
- `Theme/HealingColors.swift` → `AppColors.swift`
- `Theme/HealingColorTheme.swift` → 合并到 `AppColors.swift`
- 新建统一主题系统

#### Core/Config/ (新建 - 2 个文件)
- [ ] `AppConfig.swift` - 应用配置
- [ ] `AppConstants.swift` - 常量定义

**来源**:
- 检查现有配置相关代码
- 整合到一个配置模块

#### Core/Routing/ (新建 - 1 个文件)
- [ ] `AppRouter.swift` - 路由管理

**来源**:
- 可能需要新建，当前没有集中路由管理

#### Core/Error/ (新建 - 2 个文件)
- [ ] `AppError.swift` - 错误类型定义
- [ ] `ErrorHandler.swift` - 错误处理

**来源**:
- `Security/AppError.swift` → 迁移并扩展
- `Security/CertValidator.swift` → 错误验证相关

#### Core/Base/ (新建 - 3 个文件)
- [ ] `BaseViewController.swift` - 基础视图控制器
- [ ] `BaseViewModel.swift` - 基础视图模型
- [ ] `BaseView.swift` - 基础视图

**来源**:
- 提炼现有基类模式
- 统一基类命名

#### Core/Components/ (新建 - 6 个文件)
- [ ] `AppButton.swift` - 统一按钮
- [ ] `AppCard.swift` - 统一卡片
- [ ] `AppTextField.swift` - 统一输入框
- [ ] `AppLoadingView.swift` - 加载视图
- [ ] `AppSheet.swift` - 底部抽屉
- [ ] `AppEmptyView.swift` - 空状态视图

**来源**:
- `Components/` 下现有通用组件筛选整理
- 提炼可复用组件到 Core 层

---

### 阶段 2: Features 层重组 (预计 3-5 天)

#### Features/Auth/ (重组 - 7 个文件)

**新建目录结构**:
```
Features/Auth/
├── Views/
│   ├── LoginView.swift
│   ├── ProfileSetupView.swift
│   └── SplashView.swift
├── ViewModels/
│   ├── LoginViewModel.swift
│   └── ProfileSetupViewModel.swift
└── Services/
    ├── AuthService.swift
    └── KeychainManager.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/LoginView.swift` → `Features/Auth/Views/LoginView.swift` |
| `Views/ProfileSetupView.swift` → `Features/Auth/Views/ProfileSetupView.swift` |
| `Views/SplashView.swift` → `Features/Auth/Views/SplashView.swift` |
| `ViewModels/LoginViewModel.swift` → `Features/Auth/ViewModels/LoginViewModel.swift` |
| `ViewModels/ProfileSetupViewModel.swift` → `Features/Auth/ViewModels/ProfileSetupViewModel.swift` |
| `Services/AuthService.swift` → `Features/Auth/Services/AuthService.swift` |
| `Services/KeychainManager.swift` → `Features/Auth/Services/KeychainManager.swift` |
| `Security/AppError.swift` → `Features/Auth/Services/AppError.swift` (共享) |
| `Security/CertValidator.swift` → `Features/Auth/Services/CertValidator.swift` (共享) |

#### Features/Consultation/ (重组 - 7 个文件)

**新建目录结构**:
```
Features/Consultation/
├── Views/
│   ├── AskDoctorView.swift
│   ├── ModernConsultationView.swift
│   └── SessionHistoryView.swift
├── ViewModels/
│   ├── ChatSessionViewModel.swift
│   ├── ChatMessageViewModel.swift
│   ├── VoiceInputViewModel.swift
│   └── UnifiedChatViewModel.swift
└── Services/
    ├── ChatSessionService.swift
    ├── ChatMessageService.swift
    ├── ChatVoiceInputService.swift
    └── UnifiedChatAPIService.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/AskDoctorView.swift` → `Features/Consultation/Views/AskDoctorView.swift` |
| `Views/ModernConsultationView.swift` → `Features/Consultation/Views/ModernConsultationView.swift` |
| `Views/SessionHistoryView.swift` → `Features/Consultation/Views/SessionHistoryView.swift` |
| `Views/HomeView.swift` → `Features/Consultation/Views/HomeView.swift` |
| `ViewModels/ChatSessionViewModel.swift` → `Features/Consultation/ViewModels/ChatSessionViewModel.swift` |
| `ViewModels/ChatMessageViewModel.swift` → `Features/Consultation/ViewModels/ChatMessageViewModel.swift` |
| `ViewModels/VoiceInputViewModel.swift` → `Features/Consultation/ViewModels/VoiceInputViewModel.swift` |
| `ViewModels/UnifiedChatViewModel.swift` → `Features/Consultation/ViewModels/UnifiedChatViewModel.swift` |
| `Services/ChatSessionService.swift` → `Features/Consultation/Services/ChatSessionService.swift` |
| `Services/ChatMessageService.swift` → `Features/Consultation/Services/ChatMessageService.swift` |
| `Services/ChatVoiceInputService.swift` → `Features/Consultation/Services/ChatVoiceInputService.swift` |
| `Services/UnifiedChatAPIService.swift` → `Features/Consultation/Services/UnifiedChatAPIService.swift` |
| `Services/SessionStateManager.swift` → `Features/Consultation/Services/SessionStateManager.swift` |

#### Features/Knowledge/Disease/ (重组 - 4 个文件)

**新建目录结构**:
```
Features/Knowledge/Disease/
└── Views/
    ├── DepartmentDetailView.swift
    ├── DiseaseDetailView.swift
    ├── DiseaseListView.swift
    └── MedLiveDiseaseDetailView.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/DepartmentDetailView.swift` → `Features/Knowledge/Disease/Views/DepartmentDetailView.swift` |
| `Views/DiseaseDetailView.swift` → `Features/Knowledge/Disease/Views/DiseaseDetailView.swift` |
| `Views/DiseaseListView.swift` → `Features/Knowledge/Disease/Views/DiseaseListView.swift` |
| `Views/MedLiveDiseaseDetailView.swift` → `Features/Knowledge/Disease/Views/MedLiveDiseaseDetailView.swift` |

#### Features/Knowledge/Drug/ (重组 - 2 个文件)

**新建目录结构**:
```
Features/Knowledge/Drug/
└── Views/
    ├── DrugListView.swift
    └── DrugDetailView.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/DrugListView.swift` → `Features/Knowledge/Drug/Views/DrugListView.swift` |
| `Views/DrugDetailView.swift` → `Features/Knowledge/Drug/Views/DrugDetailView.swift` |

#### Features/Medical/Dossier/ (重组 - 10 个文件)

**新建目录结构**:
```
Features/Medical/Dossier/
├── Views/
│   ├── MedicalDossierView.swift
│   ├── MedicalFoldersView.swift
│   ├── EventDetailView.swift
│   ├── EventDetailWrapperView.swift
│   ├── PDFViewerSheet.swift
│   ├── PDFPreviewView.swift
│   ├── RecordDetailView.swift
│   ├── VoiceRecorderView.swift
│   ├── ExportedConversationRow.swift
│   ├── CreateRecordSheet.swift
│   └── MedicalFoldersView.swift
├── ViewModels/
│   ├── MedicalDossierViewModel.swift
│   ├── MedicalFolderViewModel.swift
│   └── VoiceTranscriptionViewModel.swift
└── Services/
    ├── MedicalEventAPIService.swift
    └── PDFGenerator.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/MedicalDossierView.swift` → `Features/Medical/Dossier/Views/MedicalDossierView.swift` |
| `Views/MedicalFoldersView.swift` → `Features/Medical/Dossier/Views/MedicalFoldersView.swift` |
| `Views/EventDetailView.swift` → `Features/Medical/Dossier/Views/EventDetailView.swift` |
| `Views/EventDetailWrapperView.swift` → `Features/Medical/Dossier/Views/EventDetailWrapperView.swift` |
| `Views/PDFViewerSheet.swift` → `Features/Medical/Dossier/Views/PDFViewerSheet.swift` |
| `Views/PDFPreviewView.swift` → `Features/Medical/Dossier/Views/PDFPreviewView.swift` |
| `Views/RecordDetailView.swift` → `Features/Medical/Dossier/Views/RecordDetailView.swift` |
| `Views/VoiceRecorderView.swift` → `Features/Medical/Dossier/Views/VoiceRecorderView.swift` |
| `Views/ExportedConversationRow.swift` → `Features/Medical/Dossier/Views/ExportedConversationRow.swift` |
| `Views/CreateRecordSheet.swift` → `Features/Medical/Dossier/Views/CreateRecordSheet.swift` |
| `ViewModels/MedicalDossierViewModel.swift` → `Features/Medical/Dossier/ViewModels/MedicalDossierViewModel.swift` |
| `ViewModels/MedicalFolderViewModel.swift` → `Features/Medical/Dossier/ViewModels/MedicalFolderViewModel.swift` |
| `ViewModels/VoiceTranscriptionViewModel.swift` → `Features/Medical/Dossier/ViewModels/VoiceTranscriptionViewModel.swift` |
| `Services/MedicalEventAPIService.swift` → `Features/Medical/Dossier/Services/MedicalEventAPIService.swift` |
| `Services/PDFGenerator.swift` → `Features/Medical/Dossier/Services/PDFGenerator.swift` |

#### Features/Medical/Orders/ (重组 - 2 个文件)

**新建目录结构**:
```
Features/Medical/Orders/
├── Views/
│   ├── MedicalOrderListView.swift
│   └── TaskCheckInView.swift
└── ViewModels/
    └── MedicalOrderViewModel.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/MedicalOrderListView.swift` → `Features/Medical/Orders/Views/MedicalOrderListView.swift` |
| `Views/TaskCheckInView.swift` → `Features/Medical/Orders/Views/TaskCheckInView.swift` |
| `ViewModels/MedicalOrderViewModel.swift` → `Features/Medical/Orders/ViewModels/MedicalOrderViewModel.swift` |

#### Features/Profile/ (重组 - 1 个文件)

**新建目录结构**:
```
Features/Profile/
└── Views/
    └── ProfileView.swift
```

**迁移映射**:
| 源文件 | 目标位置 |
|--------|----------|
| `Views/ProfileView.swift` → `Features/Profile/Views/ProfileView.swift` |

---

### 阶段 3: Components 层整理 (预计 1-2 天)

#### 共享组件筛选

从 `Components/` (51 个文件) 中筛选出真正的共享组件：

**保留在 Components/ 的通用组件**:
- 通用按钮类
- 通用输入类
- 通用卡片类
- 加载状态视图
- 空状态视图

**迁移到 Shared/Components/ 的专用组件**：
- 照片相关组件 (7 个文件)
- 录音相关组件 (6 个文件)
- 聊天相关组件 (15 个文件)
- 其他专用组件

---

### 阶段 4: 清理工作 (预计 1 天)

- [ ] 删除空的测试文件
- [ ] 统一命名规范
- [ ] 清理重复代码
- [ ] 移除未使用的导入

---

### 阶段 5: Xcode 项目更新 (预计 0.5 天)

- [ ] 添加新目录到项目
- [ ] 验证所有文件引用
- [ ] 编译测试
- [ ] 运行测试

---

## ⚠️ 执行注意事项

1. **分阶段进行** - 每完成一个阶段再进行下一阶段
2. **保持旧代码可用** - 新旧结构创建完成前，删除旧代码
3. **更新 import 路径** - 文件移动后更新所有引用
4. **持续测试** - 每个阶段完成后进行功能测试
5. **可以随时暂停** - 作为可选项目，不强制完成

---

## 📊 进度跟踪

| 阶段 | 预计天数 | 状态 | 完成度 |
|------|----------|--------|----------|
| Core 层创建 | 2-3 天 | ⏸️ 待开始 | 0% |
| Features 层重组 | 3-5 天 | ⏸️ 待开始 | 0% |
| Components 整理 | 1-2 天 | ⏸️ 待开始 | 0% |
| 清理工作 | 1 天 | ⏸️ 待开始 | 0% |
| Xcode 更新 | 0.5 天 | ⏸️ 待开始 | 0% |
| **总计** | **6-10 天** | - | **0%** |

---

## 下一步

从 **阶段 1: Core 层创建** 开始实施。

建议优先级：
1. **颜色系统** - 影响最大，建议先做
2. **配置常量** - 相对简单
3. **基础类** - 其他组件依赖
