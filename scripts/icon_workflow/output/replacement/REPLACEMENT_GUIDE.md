# iOS 图标替换指南

## 概述

本文档说明如何将 iOS 项目中的 SF Symbol 替换为自定义图标。

## 统计信息

- 需要修改的文件: 23 个
- 唯一图标数: 49 个
- 图标使用总数: 115 次

## 步骤

### 1. 批量生成所有图标

```bash
cd /Users/zhuxinye/Desktop/project/home-health
python scripts/icon_workflow/batch_generator.py batch
```

### 2. 处理图标（转透明、裁剪）

```bash
python scripts/icon_workflow/image_processor.py
```

### 3. 创建 Asset Catalog

```bash
bash scripts/icon_workflow/output/replacement/create_assets.sh
```

### 4. 复制图标到 Asset Catalog

```bash
# 将处理后的图标复制到对应的 .imageset 目录
python scripts/icon_workflow/copy_assets.py
```

### 5. 添加图标扩展代码

将 `IconExtension.swift` 添加到 Xcode 项目中。

### 6. 替换代码中的图标引用

查找并替换：
- `Image(systemName: "chevron.right")` → `Image(icon: "chevronRight")`

## 使用方式

```swift
// 使用自定义图标
Image(icon: "chevronRight")
    .foregroundColor(.purple)

// 或使用枚举
Image(icon: IconName.chevronRight.rawValue)
```

## 文件清单

需要修改的文件:
- `ios/xinlingyisheng/xinlingyisheng/Views/FullScreenVoiceModeView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/ProfileView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/LoginView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/HomeView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/AskDoctorView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/SessionHistoryView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/ProfileSetupView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/DiseaseDetailView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/ColorSchemeSelector.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/DepartmentDetailView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/DrugListView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MyQuestionsView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/DrugDetailView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/DiseaseListView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/EventDetailWrapperView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/VoiceRecorderView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/ExportedConversationRow.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalDossierView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/PDFViewerSheet.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/PDFPreviewView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/ExportConfigView.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/EventDetailView.swift`
