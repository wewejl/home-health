# 病历资料夹导出功能重构方案

**版本**: V1.0  
**日期**: 2026-01-18  
**作者**: 项目团队  
**状态**: 设计阶段

---

## 目录

1. [问题分析](#问题分析)
2. [解决方案概述](#解决方案概述)
3. [架构设计](#架构设计)
4. [数据模型设计](#数据模型设计)
5. [功能模块设计](#功能模块设计)
6. [实施计划](#实施计划)

---

## 问题分析

### 当前系统存在的核心问题

#### 1. 数据类型不一致
- 后端 `event_id` 使用 `Integer`，API 契约声明为 `String (UUID)`，iOS 定义为 `String`
- 导致多处类型转换，容易出错

#### 2. 枚举类型映射混乱
- 前端使用 `dermatology`，后端使用 `derma`
- 状态枚举：iOS 用 `in_progress`，后端用 `active`

#### 3. 会话聚合逻辑不合理
- 按"当天 + 同科室"自动聚合，缺乏语义判断
- 用户一天内多次咨询不同问题会被强制合并

#### 4. 功能定位不清晰
- 按钮叫"生成病历"，但实际只是数据聚合
- 没有真正的"导出"功能（PDF、分享链接）
- 用户期望：点击导出 → 获得可分享的文件

### 用户真实需求

1. **简单直接的导出功能** - 对话结束后，点击"导出"按钮，立即生成 PDF 文件
2. **历史记录管理** - 查看过往导出的对话记录，随时重新打开查看
3. **隐私和便捷性** - 数据存在本地，不强制上传服务器，离线可用

---

## 解决方案概述

### 核心思路

**从"复杂的病历事件系统"简化为"对话 PDF 档案管理器"**

### 方案选择

**第一阶段：纯前端生成 PDF（推荐）**

**优点：**
- ✅ 实现简单，1-2天可完成
- ✅ 响应快速，无需网络请求
- ✅ 用户隐私最好，数据不上传
- ✅ 离线可用
- ✅ 无需后端改动

**缺点：**
- ❌ PDF 样式定制能力有限
- ❌ 无法包含服务器端的 AI 分析数据

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────┐
│              iOS 应用层                      │
├─────────────────────────────────────────────┤
│  对话界面 → UnifiedChatViewModel            │
│      ↓                                      │
│  ConversationPDFGenerator (生成PDF)         │
│      ↓                                      │
│  ExportedConversationStore (保存记录)       │
│      ↓                                      │
│  病历资料夹 (查看/分享/删除)                 │
├─────────────────────────────────────────────┤
│  本地存储：UserDefaults + FileManager       │
└─────────────────────────────────────────────┘
```

### 数据流程

```
用户点击"导出对话"
    ↓
准备导出数据 (医生、科室、消息列表)
    ↓
生成 PDF 文件 (保存到 Documents/exports/)
    ↓
创建导出记录 (保存元数据到 UserDefaults)
    ↓
显示成功提示："已保存到病历资料夹"
```

---

## 数据模型设计

### 1. ExportedConversation（导出记录）

```swift
struct ExportedConversation: Identifiable, Codable {
    let id: String              // UUID
    let title: String           // "皮肤科咨询 - 2026-01-18"
    let department: String      // "皮肤科"
    let doctorName: String      // "AI皮肤科医生"
    let exportDate: Date        // 导出时间
    let pdfFileName: String     // "conversation_xxx.pdf"
    let messageCount: Int       // 对话消息数
    let fileSize: Int64         // 文件大小
    
    var pdfURL: URL {
        FileManager.default
            .urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("exports")
            .appendingPathComponent(pdfFileName)
    }
}
```

### 2. ConversationExportData（导出数据）

```swift
struct ConversationExportData {
    let doctorName: String
    let department: String
    let sessionDate: Date
    let messages: [UnifiedChatMessage]
    let userInfo: ExportUserInfo?
}

struct ExportUserInfo {
    let name: String?
    let age: Int?
    let gender: String?
}
```

### 3. 存储结构

**UserDefaults 存储：**
```json
{
  "exported_conversations": [
    {
      "id": "uuid-1",
      "title": "皮肤科咨询 - 2026-01-18",
      "department": "皮肤科",
      "exportDate": "2026-01-18T14:30:00Z",
      "pdfFileName": "conversation_2026-01-18_001.pdf",
      "messageCount": 12,
      "fileSize": 245760
    }
  ]
}
```

**文件系统：**
```
Documents/
└── exports/
    ├── conversation_2026-01-18_001.pdf
    ├── conversation_2026-01-18_002.pdf
    └── conversation_2026-01-19_001.pdf
```

---

## 功能模块设计

### 模块 1：PDF 生成器

**文件：** `ConversationPDFGenerator.swift`

**核心方法：**
```swift
class ConversationPDFGenerator {
    func generate(data: ConversationExportData) async throws -> URL
    private func formatMessages(_ messages: [UnifiedChatMessage]) -> [FormattedMessage]
    private func addTitlePage(data: ConversationExportData, pageSize: CGSize)
    private func addMessagesPages(messages: [FormattedMessage], pageSize: CGSize)
}
```

**PDF 布局：**
```
┌─────────────────────────────────┐
│    心灵医生 - 对话记录           │
│                                 │
│  科室：皮肤科                    │
│  医生：AI 皮肤科医生             │
│  日期：2026-01-18 14:30         │
├─────────────────────────────────┤
│  [用户] 14:30                   │
│  医生您好，我手臂上有红疹...     │
│                                 │
│  [医生] 14:31                   │
│  请问红疹出现多久了？...         │
├─────────────────────────────────┤
│  第 1 页 | 导出时间：2026-01-18 │
└─────────────────────────────────┘
```

### 模块 2：导出记录存储

**文件：** `ExportedConversationStore.swift`

**核心方法：**
```swift
class ExportedConversationStore: ObservableObject {
    @Published var exports: [ExportedConversation] = []
    
    func save(_ export: ExportedConversation)
    func delete(_ export: ExportedConversation)
    func search(keyword: String) -> [ExportedConversation]
    func cleanupOldExports(olderThan days: Int = 30)
}
```

### 模块 3：病历资料夹视图

**文件：** `MedicalDossierView.swift`

**功能：**
- 显示导出记录列表
- 支持搜索和筛选
- 支持删除操作
- 打开 PDF 查看器

**UI 结构：**
```swift
struct MedicalDossierView: View {
    var body: some View {
        NavigationView {
            VStack {
                searchBar
                if filteredExports.isEmpty {
                    emptyStateView
                } else {
                    exportsList
                }
            }
        }
    }
}
```

### 模块 4：PDF 查看器

**文件：** `PDFViewerSheet.swift`

**功能：**
- 使用 PDFKit 渲染 PDF
- 支持缩放、滚动
- 分享按钮
- 打印功能

### 模块 5：导出按钮集成

**修改文件：**
- `ChatNavBarV2.swift` - 添加导出按钮
- `ModernConsultationView.swift` - 集成导出逻辑
- `UnifiedChatViewModel.swift` - 实现导出方法

---

## 实施计划

### 阶段 1：核心功能开发（2-3天）

**优先级 P0：**

1. **创建 PDF 生成器**
   - 新建 `ConversationPDFGenerator.swift`
   - 实现基础 PDF 生成逻辑
   - 测试 PDF 格式和样式

2. **创建导出记录存储**
   - 新建 `ExportedConversationStore.swift`
   - 实现 UserDefaults 持久化
   - 实现文件管理逻辑

3. **集成导出按钮**
   - 修改 `ChatNavBarV2.swift`
   - 修改 `UnifiedChatViewModel.swift`
   - 添加导出成功提示

4. **重构病历资料夹页面**
   - 修改 `MedicalDossierView.swift`
   - 显示导出记录列表
   - 实现删除功能

5. **创建 PDF 查看器**
   - 新建 `PDFViewerSheet.swift`
   - 集成 PDFKit
   - 添加分享功能

### 阶段 2：体验优化（1-2天）

**优先级 P1：**

1. 导出成功动画和提示
2. 搜索和筛选功能
3. 批量删除
4. 文件清理策略

### 阶段 3：高级功能（未来）

**优先级 P2：**

1. 云端同步（需要后端）
2. 分享给医生（生成分享链接）
3. PDF 加密保护
4. 导出为其他格式

---

## 数据迁移策略

### 现有数据处理

**方案：保留现有数据，双轨运行**

1. 现有的病历事件数据保留在后端
2. 新的导出功能使用本地存储
3. 在病历资料夹页面显示两个标签：
   - "本地记录"（新导出的 PDF）
   - "历史病历"（旧的病历事件，只读）

### 后端接口调整

```python
# 保留查询接口，但标记为只读
@router.get("/medical-events")
def list_medical_events_readonly():
    """获取历史病历事件列表（只读）"""
    pass

# 废弃聚合接口
@router.post("/medical-events/aggregate")
def aggregate_session_deprecated():
    raise HTTPException(
        status_code=410,
        detail="此接口已废弃，请使用新的本地导出功能"
    )
```

---

## 文件清单

### 新增文件

```
ios/xinlingyisheng/xinlingyisheng/
├── Services/
│   ├── ConversationPDFGenerator.swift       (新增)
│   └── ExportedConversationStore.swift      (新增)
├── Views/
│   └── MedicalDossier/
│       ├── MedicalDossierView.swift         (重构)
│       ├── PDFViewerSheet.swift             (新增)
│       └── ExportedConversationRow.swift    (新增)
└── Models/
    └── ExportedConversation.swift           (新增)
```

### 修改文件

```
ios/xinlingyisheng/xinlingyisheng/
├── Components/PhotoCapture/
│   └── ChatNavBarV2.swift                   (修改)
├── Views/
│   └── ModernConsultationView.swift         (修改)
└── ViewModels/
    └── UnifiedChatViewModel.swift           (修改)
```

### 废弃代码

```
backend/app/routes/
└── medical_events.py                        (部分废弃)
    - aggregate_session()                    (废弃)
    - 复杂的聚合逻辑                          (废弃)
```

---

## 风险评估

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| PDF 生成性能问题 | 中 | 低 | 异步生成，添加进度提示 |
| 文件存储空间不足 | 中 | 中 | 定期清理，限制文件数量 |
| UserDefaults 数据丢失 | 高 | 低 | 添加备份机制 |

### 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 用户不理解新功能 | 中 | 中 | 添加引导提示 |
| 历史数据无法访问 | 高 | 低 | 保留旧接口只读访问 |

---

## 成功指标

1. **功能完整性**
   - ✅ 用户可以导出对话为 PDF
   - ✅ 用户可以查看历史导出记录
   - ✅ 用户可以分享 PDF 给他人

2. **性能指标**
   - 导出 PDF 时间 < 3秒（100条消息）
   - 列表加载时间 < 1秒

3. **用户体验**
   - 操作步骤 ≤ 2步（点击导出 → 完成）
   - 成功率 > 95%

---

## 总结

本方案将复杂的病历事件系统简化为简单直接的对话 PDF 导出功能，核心优势：

1. **简单易用** - 用户一看就懂，点击即导出
2. **快速实现** - 2-3天可完成核心功能
3. **隐私安全** - 数据存储在本地
4. **功能完整** - 导出、查看、分享、删除

**下一步行动：**
1. 评审本方案
2. 开始实施阶段 1
3. 完成后进行用户测试
