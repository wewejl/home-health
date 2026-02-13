# iOS 架构优化项目

> **项目类型**: 可选架构优化
> **创建日期**: 2026-02-14
> **状态**: 计划中
> **优先级**: P3 (可选，不影响现有功能)

---

## 📋 项目概述

这是一个**可选的 iOS 项目架构重构优化**，旨在将当前扁平化目录结构重构为符合 Apple 官方推荐的模块化分层结构。

### ⚠️ 重要说明

1. **不影响现有功能** - 当前代码已完整实现并可正常工作
2. **这是一个独立项目** - 与主项目功能开发分离
3. **可以随时暂停** - 作为长期优化工作，不阻塞新功能开发
4. **风险可控** - 重构过程中保持现有代码可用

---

## 🎯 目标结构

### 当前结构（扁平化）

```
ios/xinlingyisheng/xinlingyisheng/
├── Components/          # 通用组件
├── Models/             # 数据模型
├── Services/           # 服务层
├── ViewModels/        # 视图模型
├── Views/             # 视图
├── Security/           # 安全相关
├── Theme/             # 主题相关
├── Network/           # 网络相关
├── Utilities/         # 工具类
└── ... (100+ 个文件分散各处)
```

### 目标结构（模块化）

```
ios/xinlingyisheng/xinlingyisheng/
├── Core/                    # 核心基础设施（不依赖业务）
│   ├── Theme/             # 统一颜色、字体、间距系统
│   ├── Config/            # 统一配置、常量定义
│   ├── Routing/            # 统一路由管理
│   ├── Error/              # 统一错误类型和处理
│   ├── Base/               # 基础类（Controller, ViewModel, View）
│   └── Components/         # 共享可复用组件
├── Features/               # 按功能模块组织（业务相关）
│   ├── Auth/               # 认证模块
│   │   ├── Views/
│   │   ├── ViewModels/
│   │   ├── Services/
│   │   └── Models/
│   ├── Chat/               # 聊天模块
│   ├── Consultation/        # 问诊模块
│   ├── Knowledge/          # 知识库模块
│   │   ├── Disease/
│   │   └── Drug/
│   ├── Medical/            # 医疗模块
│   │   ├── Dossier/
│   │   └── Orders/
│   └── Profile/            # 个人中心模块
├── Shared/                 # 共享资源
│   ├── Components/         # 跨模块通用组件
│   └── Resources/         # 图片、颜色、字体等
└── Resources/               # 根级资源
    ├── Assets.xcassets
    └── Localization/
```

---

## 📊 工作量估算

| 分类 | 文件数 | 工作量 |
|------|---------|--------|
| Core 层创建 | ~22 个文件 | 2-3 天 |
| Features 层重组 | ~40+ 个文件 | 3-5 天 |
| Shared 层整理 | ~25 个文件 | 1-2 天 |
| Xcode 项目更新 | - | 0.5 天 |
| **总计** | **~90 个文件** | **6-10 天** |

---

## 🚀 实施计划

### 阶段 1: 准备工作 (1-2 天)

- [ ] 详细文件清单
- [ ] 制定迁移顺序
- [ ] 准备新目录结构模板
- [ ] 备份当前项目

### 阶段 2: Core 层创建 (2-3 天)

- [ ] Core/Theme/ - 颜色、字体、间距系统
- [ ] Core/Config/ - 应用配置、常量
- [ ] Core/Routing/ - 路由管理
- [ ] Core/Error/ - 错误类型和处理
- [ ] Core/Base/ - 基础类
- [ ] Core/Components/ - 共享组件

### 阶段 3: Features 层重组 (3-5 天)

- [ ] Features/Auth/ - 认证模块
- [ ] Features/Chat/ - 聊天模块
- [ ] Features/Consultation/ - 问诊模块
- [ ] Features/Knowledge/ - 知识库模块
- [ ] Features/Medical/ - 医疗模块
- [ ] Features/Profile/ - 个人中心模块

### 阶段 4: Shared 层整理 (1-2 天)

- [ ] 共享组件整理
- [ ] 资源文件整理

### 阶段 5: Xcode 项目更新 (0.5 天)

- [ ] 添加新目录到 Xcode 项目
- [ ] 移除旧目录引用
- [ ] 编译验证

---

## ✅ 验证标准

重构完成后需要满足：

1. **编译通过** - 项目可以正常编译，无错误
2. **测试通过** - 现有功能测试全部通过
3. **代码规范** - 符合命名规范，文件组织清晰
4. **无重复代码** - 消除重复的类和函数
5. **导入正确** - 所有 import 路径正确

---

## 📝 备注

- 此项目完全**可选**，不影响主项目功能开发
- 可以**分阶段实施**，每次完成一个模块
- 建议在**新功能开发较少时**进行
- 实施过程中需要**持续测试**确保功能不受影响

---

## 参考文档

- `docs/iOS代码优化方案v3-工程化版.md` - 完整技术方案
- `docs/iOS/Xcode项目文件更新指南.md` - Xcode 操作指南
- Apple 官方文档: https://developer.apple.com/documentation/swiftui/app-structure
