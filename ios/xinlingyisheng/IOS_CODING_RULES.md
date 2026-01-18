# iOS 编码规范

**版本**: V1.0  
**更新日期**: 2026-01-15  
**适用范围**: xinlingyisheng iOS 项目

> ⚠️ **强制要求**: 所有 iOS 代码修改必须严格遵守本规范。违反规范的代码不予合并。

---

## 目录

1. [强制性代码规范](#强制性代码规范)
2. [框架导入规范](#框架导入规范)
3. [数据模型使用规范](#数据模型使用规范)
4. [Preview 规范](#preview-规范)
5. [组件组织规范](#组件组织规范)
6. [编译验证规范](#编译验证规范)
7. [设计系统规范](#设计系统规范)
8. [命名规范](#命名规范)

---

## 强制性代码规范

### ✅ 必须遵守的检查清单

在编写任何 SwiftUI/Swift 代码前，必须逐项核对以下内容：

- [ ] 确认所需框架已正确导入
- [ ] 使用项目内结构体/枚举/类前，已通过工具查阅真实定义
- [ ] Preview 中使用的数据模型与真实结构完全一致
- [ ] 新增组件已放入既有目录结构
- [ ] 使用了项目既定的颜色/字体/间距/圆角系统
- [ ] 代码修改后已执行编译验证

---

## 框架导入规范

### 常用框架清单

```swift
// UI 框架
import SwiftUI
import UIKit  // 仅在需要 UIKit 桥接时使用

// 响应式编程
import Combine

// 多媒体
import AVFoundation  // 相机、音视频
import Photos        // 照片库访问
import PhotosUI      // 照片选择器

// 网络
import Foundation    // URLSession

// 其他
import CoreData      // 本地数据持久化
import CoreLocation  // 位置服务
```

### 导入规则

1. **先确认再使用**: 使用任何框架 API 前，必须确认该框架已导入
2. **按功能分组**: 导入语句按功能分组，用空行分隔
3. **避免冗余**: 不要导入未使用的框架

```swift
// ✅ 正确示例
import SwiftUI
import Combine

import AVFoundation
import Photos

// ❌ 错误示例 - 未导入就使用
struct CameraView: View {
    @StateObject var camera = CameraManager()  // ❌ 未导入 AVFoundation
}
```

---

## 数据模型使用规范

### 查阅真实定义

使用项目内已有的结构体/枚举/类之前，**必须**通过以下方式查阅真实定义：

1. 使用 `grep_search` 搜索类型定义
2. 使用 `read_file` 查看完整定义
3. **禁止凭记忆编写初始化参数或字段**

### 示例

```swift
// ❌ 错误 - 凭记忆编写
let message = ChatMessage(
    content: "Hello",
    sender: "user"  // 错误的字段名
)

// ✅ 正确 - 查阅真实定义后
// 先执行: grep_search "struct ChatMessage"
// 确认定义后再使用
let message = ChatMessage(
    id: UUID().uuidString,
    content: "Hello",
    role: .user,
    timestamp: Date()
)
```

---

## Preview 规范

### 数据一致性要求

Preview 中使用的数据模型**必须与真实结构完全一致**：

- 严禁伪造字段
- 严禁缺少必填属性
- 使用 `.preview` 或 `.mock` 静态属性提供测试数据

### 示例

```swift
// ✅ 正确 - 使用完整的模型定义
#Preview {
    MessageBubble(message: ChatMessage.preview)
}

// 在模型中定义 preview 数据
extension ChatMessage {
    static var preview: ChatMessage {
        ChatMessage(
            id: "preview-1",
            content: "这是预览消息",
            role: .assistant,
            timestamp: Date()
        )
    }
}

// ❌ 错误 - 伪造不存在的字段
#Preview {
    MessageBubble(message: ChatMessage(
        text: "Hello",  // 字段名错误
        type: "user"    // 字段不存在
    ))
}
```

---

## 组件组织规范

### 目录结构

```
xinlingyisheng/
├── Components/          # 可复用 UI 组件
│   ├── Chat/           # 聊天相关组件
│   ├── PhotoCapture/   # 拍照相关组件
│   ├── Common/         # 通用组件
│   └── ...
├── Models/             # 数据模型
├── Services/           # 网络和业务服务
├── ViewModels/         # 视图模型
├── Views/              # 页面视图
├── Theme/              # 主题和样式
└── Utilities/          # 工具类
```

### 新增组件规则

1. 新增组件必须放入既有目录结构
2. 组件文件名与组件名一致
3. 每个组件一个文件（除非是紧密相关的子组件）

---

## 编译验证规范

### 强制要求

**每次修改完 iOS 代码后必须立即编译**：

- 使用 `⌘+B` 或 `xcodebuild` 执行编译
- 确保改动可通过编译后再提交

### 编译失败处理流程

当编译失败时，按以下步骤处理：

1. **阅读 Xcode 报错信息**
   - 定位具体文件、行号和符号
   - 理解错误类型

2. **查阅真实代码定义**
   - 使用 `read_file` / `grep_search` 等工具
   - **禁止凭记忆修改**

3. **评估改动影响**
   - 结合全局架构（ViewModel、Service、Model、API 契约）
   - 确保修复不会引入新问题

4. **修复后再次编译**
   - 直至无错误和警告
   - 验证功能正常

---

## 设计系统规范

### 颜色系统 - DXYColors

```swift
// 使用项目定义的颜色
Text("标题")
    .foregroundColor(DXYColors.textPrimary)
    
Button("按钮") { }
    .background(DXYColors.primaryBlue)

// ❌ 禁止直接使用硬编码颜色
Text("标题")
    .foregroundColor(Color(hex: "#333333"))  // 错误
```

### 字体系统 - AdaptiveFont

```swift
// 使用自适应字体
Text("标题")
    .font(AdaptiveFont.title)

Text("正文")
    .font(AdaptiveFont.body)

// ❌ 禁止直接使用系统字体
Text("标题")
    .font(.system(size: 18))  // 错误
```

### 间距系统 - AdaptiveSize

```swift
// 使用自适应间距
VStack(spacing: AdaptiveSize.spacing.medium) {
    // ...
}

.padding(AdaptiveSize.padding.standard)

// ❌ 禁止硬编码间距
.padding(16)  // 错误
```

### 圆角系统 - ScaleFactor

```swift
// 使用自适应圆角
.cornerRadius(ScaleFactor.cornerRadius.medium)

// ❌ 禁止硬编码圆角
.cornerRadius(12)  // 错误
```

---

## 命名规范

### 文件命名

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| View | `功能名View.swift` | `DoctorChatView.swift` |
| ViewModel | `功能名ViewModel.swift` | `ChatViewModel.swift` |
| Model | `模型名.swift` | `ChatMessage.swift` |
| Service | `功能名Service.swift` | `APIService.swift` |
| Component | `组件名.swift` | `MessageBubble.swift` |

### 变量命名

```swift
// ✅ 正确 - 驼峰命名
let messageList: [ChatMessage]
var isLoading: Bool
@State private var showSheet: Bool

// ❌ 错误
let message_list: [ChatMessage]  // 下划线
var IsLoading: Bool              // 首字母大写
```

### 函数命名

```swift
// ✅ 正确 - 动词开头，描述行为
func sendMessage(_ content: String) async throws
func loadChatHistory() async
func handleUserInput(_ input: String)

// ❌ 错误
func message(_ content: String)  // 不清晰
func doStuff()                   // 不具描述性
```

---

## 常见错误示例

### 1. 未导入框架

```swift
// ❌ 错误 - 使用 @StateObject 但未确认 Combine 导入
struct MyView: View {
    @StateObject var viewModel = MyViewModel()
}

// ✅ 正确
import SwiftUI
import Combine

struct MyView: View {
    @StateObject var viewModel = MyViewModel()
}
```

### 2. 错误的初始化参数

```swift
// ❌ 错误 - 凭记忆编写参数
let session = Session(
    sessionId: "123",  // 实际字段名是 id
    userId: 1          // 实际是 user_id
)

// ✅ 正确 - 先查阅定义
// grep_search "struct Session" 确认字段后
let session = Session(
    id: "123",
    user_id: 1,
    agent_type: .dermatology
)
```

### 3. Preview 数据不完整

```swift
// ❌ 错误 - 缺少必填字段
#Preview {
    ChatBubble(message: ChatMessage(content: "Hi"))
}

// ✅ 正确 - 完整数据
#Preview {
    ChatBubble(message: ChatMessage(
        id: "1",
        content: "Hi",
        role: .user,
        timestamp: Date()
    ))
}
```

---

## 检查清单模板

在提交代码前，请确认以下事项：

```markdown
## 代码检查清单

### 框架导入
- [ ] 所有使用的框架已正确导入
- [ ] 没有冗余的导入

### 数据模型
- [ ] 已查阅所有使用的类型定义
- [ ] 初始化参数与定义一致

### UI 组件
- [ ] 使用项目颜色系统 (DXYColors)
- [ ] 使用自适应字体 (AdaptiveFont)
- [ ] 使用自适应间距 (AdaptiveSize)
- [ ] 使用自适应圆角 (ScaleFactor)

### Preview
- [ ] Preview 数据完整
- [ ] Preview 可正常渲染

### 编译
- [ ] 代码已通过编译
- [ ] 无警告信息
```

---

**文档维护人**: iOS 开发团队  
**最后更新**: 2026-01-15
