---
trigger: always_on
priority: critical
---

# iOS 开发指南

**版本**: V1.0  
**更新日期**: 2026-01-15  
**适用范围**: iOS 客户端开发

> ⚠️ **重要提示**: 所有 iOS 开发者（包括 AI）在编写任何 Swift/SwiftUI 代码前，必须先阅读本文档。

---

## 目录

1. [项目结构](#项目结构)
2. [设计系统](#设计系统)
3. [编码规范](#编码规范)
4. [API 集成](#api-集成)
5. [状态管理](#状态管理)
6. [性能优化](#性能优化)
7. [常见问题](#常见问题)

---

## 项目结构

### 目录组织

```
xinlingyisheng/
├── Components/          # 可复用组件
│   ├── PhotoCapture/   # 相机/照片相关组件
│   ├── MedicalDossier/ # 病历模块组件
│   └── ...
├── Models/             # 数据模型
│   ├── AIModels.swift
│   ├── APIModels.swift
│   ├── MedicalDossierModels.swift
│   └── UnifiedChatModels.swift
├── Services/           # 服务层
│   ├── APIService.swift
│   ├── AIService.swift
│   ├── MedicalEventAPIService.swift
│   └── APIConfig.swift
├── ViewModels/         # 视图模型
│   ├── UnifiedChatViewModel.swift
│   ├── MedicalDossierViewModel.swift
│   └── ...
├── Views/              # 视图
│   ├── ModernConsultationView.swift
│   ├── MedicalDossier/
│   └── ...
├── Theme/              # 设计系统
│   ├── ColorSchemes.swift
│   ├── DossierColors.swift
│   ├── LayoutConstants.swift
│   └── ModernDesignSystem.swift
└── Utilities/          # 工具类
```

### 文件命名规范

- **视图**: `ModernConsultationView.swift`
- **视图模型**: `UnifiedChatViewModel.swift`
- **模型**: `MedicalDossierModels.swift`
- **服务**: `APIService.swift`
- **组件**: `ChatNavBarV2.swift`

---

## 设计系统

### 颜色系统

#### 主色调 (DXYColors)

```swift
// 主色
DXYColors.primaryPurple      // 主紫色 #855CF8
DXYColors.teal               // 青绿色 #4DB8A3

// 背景色
DXYColors.background         // 主背景
DXYColors.cardBackground     // 卡片背景

// 文字色
DXYColors.textPrimary        // 主文字
DXYColors.textSecondary      // 次要文字
DXYColors.textTertiary       // 三级文字
```

#### 病历模块专用颜色 (DossierColors)

```swift
// 风险等级
DossierColors.riskLow        // 低风险 - 绿色
DossierColors.riskMedium     // 中风险 - 橙色
DossierColors.riskHigh       // 高风险 - 红色
DossierColors.riskEmergency  // 紧急 - 深红

// 事件状态
DossierColors.statusInProgress  // 进行中
DossierColors.statusCompleted   // 已完成
DossierColors.statusExported    // 已导出
```

**⚠️ 禁止事项**:
- 禁止硬编码颜色值（如 `Color.red`）
- 必须使用设计系统定义的颜色
- 新增颜色必须添加到对应的颜色文件

### 响应式布局系统

#### ScaleFactor - 基于比例的缩放

以 iPhone 14 Pro Max (430pt) 为基准，自动适配所有设备：

```swift
// 字体
.font(.system(size: AdaptiveFont.body))        // 16pt (自动缩放)
.font(.system(size: AdaptiveFont.title2))      // 20pt (自动缩放)

// 间距
.padding(ScaleFactor.padding(16))              // 自动缩放
.spacing(ScaleFactor.spacing(12))              // 自动缩放

// 尺寸
.frame(width: ScaleFactor.size(44))            // 自动缩放
.cornerRadius(ScaleFactor.size(12))            // 自动缩放
```

#### 预定义间距

```swift
AdaptiveSpacing.section     // 24pt (大区块间距)
AdaptiveSpacing.item        // 16pt (列表项间距)
AdaptiveSpacing.card        // 20pt (卡片内边距)
AdaptiveSpacing.compact     // 8pt (紧凑间距)
```

#### 预定义字体

```swift
AdaptiveFont.largeTitle     // 28pt
AdaptiveFont.title1         // 24pt
AdaptiveFont.title2         // 20pt
AdaptiveFont.title3         // 18pt
AdaptiveFont.body           // 16pt
AdaptiveFont.subheadline    // 14pt
AdaptiveFont.footnote       // 12pt
AdaptiveFont.caption        // 11pt
```

**⚠️ 强制规范**:
- **禁止硬编码尺寸**: 如 `.padding(16)` 应改为 `.padding(ScaleFactor.padding(16))`
- **禁止硬编码字体**: 如 `.font(.system(size: 16))` 应改为 `.font(.system(size: AdaptiveFont.body))`
- 所有新组件必须使用响应式系统

---

## 编码规范

### 命名规范

```swift
// 类/结构体 - 大驼峰
struct MedicalEventDTO { }
class UnifiedChatViewModel { }

// 函数/变量 - 小驼峰
func fetchEventDetail() { }
var sessionId: String?

// 常量 - 小驼峰
let primaryPurple = Color(...)
let maxFileSize = 5 * 1024 * 1024

// 枚举 - 大驼峰，case 小驼峰
enum EventStatus {
    case active
    case completed
    case archived
}
```

### 代码组织

使用 `// MARK:` 分隔代码块：

```swift
// MARK: - Properties
@Published var messages: [Message] = []
@Published var isLoading = false

// MARK: - Initialization
init() { }

// MARK: - Public Methods
func sendMessage() { }

// MARK: - Private Methods
private func handleError() { }
```

### 错误处理

```swift
// ✅ 正确：完整的错误处理
do {
    let result = try await apiService.fetchData()
    print("[Service] Data fetched successfully")
    return result
} catch let error as APIError {
    print("[Service] API Error: \(error.errorDescription)")
    throw error
} catch {
    print("[Service] Unexpected error: \(error)")
    throw APIError.serverError(error.localizedDescription)
}

// ❌ 错误：忽略错误
let result = try? await apiService.fetchData()
```

### 日志规范

统一格式：`[ModuleName] 描述信息`

```swift
print("[UnifiedChatVM] 📸 handleSelectedImage 被调用")
print("[UnifiedChatVM] ✅ 开始处理图片, action: \(action.rawValue)")
print("[UnifiedChatVM] ❌ sessionId 为 nil, 无法处理图片")
```

---

## API 集成

### ⚠️ 数据类型约定（必须严格遵守）

参考 `docs/API_CONTRACT.md`，关键字段类型：

```swift
// ✅ 正确
struct AggregateSessionResponse: Decodable {
    let event_id: String  // UUID 格式
    let message: String
    let is_new_event: Bool
}

// ❌ 错误
struct AggregateSessionResponse: Decodable {
    let event_id: Int  // 错误！后端返回 String
}
```

### API 调用模板

```swift
func fetchData() async throws -> ResponseType {
    guard let url = URL(string: APIConfig.baseURL + endpoint) else {
        throw APIError.invalidURL
    }
    
    var request = URLRequest(url: url)
    request.httpMethod = "GET"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    // 认证
    if let token = AuthManager.shared.token {
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
    
    print("[APIService] 📤 GET \(endpoint)")
    
    let (data, response) = try await URLSession.shared.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse else {
        throw APIError.invalidResponse
    }
    
    print("[APIService] 📥 Status: \(httpResponse.statusCode)")
    
    if httpResponse.statusCode == 401 {
        NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
        throw APIError.unauthorized
    }
    
    if httpResponse.statusCode >= 400 {
        if let errorString = String(data: data, encoding: .utf8) {
            print("[APIService] ❌ Error: \(errorString)")
        }
        throw APIError.serverError("请求失败: \(httpResponse.statusCode)")
    }
    
    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601
    return try decoder.decode(ResponseType.self, from: data)
}
```

### DTO 转换

```swift
extension MedicalEventDTO {
    func toMedicalEvent() -> MedicalEvent {
        MedicalEvent(
            id: String(id),  // 确保类型转换正确
            title: title,
            department: DepartmentType(rawValue: agent_type) ?? .general,
            status: EventStatus(rawValue: status) ?? .inProgress,
            // ...
        )
    }
}
```

---

## 状态管理

### ViewModel 模式

```swift
@MainActor
class UnifiedChatViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var messages: [Message] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    // MARK: - Private Properties
    private let apiService = APIService.shared
    
    // MARK: - Public Methods
    func sendMessage(content: String) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await apiService.sendMessage(content)
            messages.append(response)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

### 视图绑定

```swift
struct ChatView: View {
    @StateObject private var viewModel = UnifiedChatViewModel()
    
    var body: some View {
        VStack {
            // 消息列表
            ScrollView {
                ForEach(viewModel.messages) { message in
                    MessageBubble(message: message)
                }
            }
            
            // 输入框
            TextField("输入消息", text: $messageText)
                .onSubmit {
                    Task {
                        await viewModel.sendMessage(content: messageText)
                    }
                }
        }
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }
}
```

---

## 性能优化

### 图片处理

```swift
// ✅ 压缩后上传
func processImage(_ image: UIImage) -> UIImage {
    let maxDimension: CGFloat = 2048
    let size = image.size
    
    if size.width <= maxDimension && size.height <= maxDimension {
        return image
    }
    
    let ratio = min(maxDimension / size.width, maxDimension / size.height)
    let newSize = CGSize(width: size.width * ratio, height: size.height * ratio)
    
    UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
    image.draw(in: CGRect(origin: .zero, size: newSize))
    let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
    UIGraphicsEndImageContext()
    
    return resizedImage ?? image
}

// 检查文件大小
guard let imageData = image.jpegData(compressionQuality: 0.9) else {
    throw APIError.serverError("图片处理失败")
}

let maxSize = 5 * 1024 * 1024  // 5MB
if imageData.count > maxSize {
    throw APIError.serverError("图片过大，请选择小于5MB的图片")
}
```

### 列表优化

```swift
// ✅ 使用 LazyVStack 懒加载
ScrollView {
    LazyVStack(spacing: 12) {
        ForEach(viewModel.messages) { message in
            MessageBubble(message: message)
                .id(message.id)
        }
    }
}

// ❌ 避免使用 VStack（会一次性加载所有）
ScrollView {
    VStack {
        ForEach(viewModel.messages) { message in
            MessageBubble(message: message)
        }
    }
}
```

### 异步操作

```swift
// ✅ 在后台线程处理耗时操作
Task {
    let processedData = await withCheckedContinuation { continuation in
        DispatchQueue.global(qos: .userInitiated).async {
            let result = heavyComputation()
            continuation.resume(returning: result)
        }
    }
    
    await MainActor.run {
        self.data = processedData
    }
}
```

---

## 常见问题

### Q1: 数据类型不匹配错误

**问题**: iOS 解析 API 响应时报错 "Expected Int but found String"

**原因**: iOS DTO 定义与后端不一致

**解决方案**:
1. 查看 `docs/API_CONTRACT.md` 确认字段类型
2. 修改 iOS DTO 以匹配后端定义
3. 后端的数据类型是权威来源

```swift
// ✅ 正确
struct Response: Decodable {
    let event_id: String  // 匹配后端 UUID
}

// ❌ 错误
struct Response: Decodable {
    let event_id: Int  // 与后端不匹配
}
```

### Q2: 如何添加新的 API 接口？

**步骤**:
1. 查看 `docs/API_CONTRACT.md` 确认接口定义
2. 在 `APIConfig.swift` 添加 endpoint
3. 在对应的 Service 中实现调用方法
4. 定义 DTO（确保类型匹配）
5. 在 ViewModel 中调用
6. 编写测试

### Q3: 颜色/字体不统一怎么办？

**解决方案**:
- 使用 `DXYColors` 或 `DossierColors` 中定义的颜色
- 使用 `AdaptiveFont` 中定义的字体大小
- 禁止硬编码颜色和字体

### Q4: 如何适配不同设备？

**解决方案**:
- 使用 `ScaleFactor` 系统自动缩放
- 使用 `AdaptiveFont`、`AdaptiveSpacing`、`AdaptiveSize`
- 测试 iPhone SE、iPhone 14、iPhone 14 Pro Max

### Q5: Preview 报错怎么办？

**常见原因**:
1. 数据模型字段不完整
2. 缺少必要的依赖注入
3. 使用了真实的网络请求

**解决方案**:
```swift
#Preview {
    // 使用 mock 数据
    let mockEvent = MedicalEvent(
        id: "test-id",
        title: "测试事件",
        department: .dermatology,
        status: .active,
        // 确保所有必填字段都有值
        createdAt: Date(),
        updatedAt: Date(),
        summary: "测试摘要",
        riskLevel: .low,
        sessions: [],
        attachments: [],
        aiAnalysis: nil,
        notes: nil,
        exportedAt: nil
    )
    
    return EventDetailView(event: mockEvent)
}
```

---

## 开发检查清单

### 开始编码前 ✅

- [ ] 阅读 `docs/DEVELOPMENT_GUIDELINES.md`
- [ ] 阅读 `docs/API_CONTRACT.md`
- [ ] 阅读本文档
- [ ] 确认 API 接口定义和数据类型
- [ ] 检查是否有现有组件可复用

### 编码过程中 ✅

- [ ] 使用设计系统（颜色、字体、间距）
- [ ] 使用响应式布局系统
- [ ] 添加错误处理
- [ ] 添加日志输出
- [ ] 遵循命名规范
- [ ] 使用 MARK 组织代码

### 提交代码前 ✅

- [ ] 在真机或模拟器测试
- [ ] 测试不同设备尺寸（SE、14、Pro Max）
- [ ] 检查 Preview 是否正常
- [ ] 检查是否有编译警告
- [ ] 更新相关文档

---

## 相关文档

- [全局开发规范](./DEVELOPMENT_GUIDELINES.md)
- [API 契约文档](./API_CONTRACT.md)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)

---

## 附录：常用代码片段

### 网络请求模板

```swift
func apiCall() async throws -> ResponseType {
    let endpoint = APIConfig.baseURL + "/path"
    // ... (参考 API 调用模板)
}
```

### 错误处理模板

```swift
do {
    let result = try await operation()
    print("[Module] ✅ Success")
    return result
} catch {
    print("[Module] ❌ Error: \(error)")
    throw error
}
```

### 响应式组件模板

```swift
struct CustomComponent: View {
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            Text("标题")
                .font(.system(size: AdaptiveFont.title2, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            Text("内容")
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(DXYColors.textSecondary)
        }
        .padding(ScaleFactor.padding(16))
        .background(DXYColors.cardBackground)
        .cornerRadius(ScaleFactor.size(12))
    }
}
```

---

**文档维护者**: iOS 开发团队  
**最后更新**: 2026-01-15
