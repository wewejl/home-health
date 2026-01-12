# iOS 端皮肤科智能体集成指南

## 一、后端 API 概览

### 基础路由
- **Base URL**: `/derma`
- **认证**: 所有接口需要 Bearer Token

### 核心接口

#### 1. 开始皮肤科会话
```
POST /derma/start
Headers: Authorization: Bearer {token}, Accept: text/event-stream (可选)
Body: {
  "chief_complaint": "皮肤起红疹" (可选)
}
Response: DermaResponse (支持SSE流式)
```

#### 2. 继续对话
```
POST /derma/{session_id}/continue
Headers: Authorization: Bearer {token}, Accept: text/event-stream (可选)
Body: {
  "history": [
    {"role": "user", "message": "...", "timestamp": "..."},
    {"role": "assistant", "message": "...", "timestamp": "..."}
  ],
  "current_input": {"message": "我的手臂有红点"},
  "task_type": "conversation" // conversation | skin_analysis | report_interpret
}
Response: DermaResponse
```

#### 3. 皮肤影像分析
```
POST /derma/{session_id}/analyze-skin
Headers: Authorization: Bearer {token}, Accept: text/event-stream (可选)
Content-Type: multipart/form-data
Body:
  - image_url: String (可选)
  - image_base64: String (可选)
  - additional_info: String (可选)
Response: DermaResponse (含 skin_analysis 字段)
```

#### 4. 报告解读
```
POST /derma/{session_id}/interpret-report
Headers: Authorization: Bearer {token}, Accept: text/event-stream (可选)
Content-Type: multipart/form-data
Body:
  - image_url: String (可选)
  - image_base64: String (可选)
  - report_type: String (默认"皮肤科检查报告")
Response: DermaResponse (含 report_interpretation 字段)
```

#### 5. 图片上传辅助
```
POST /derma/{session_id}/upload-image
Headers: Authorization: Bearer {token}
Content-Type: multipart/form-data
Body:
  - file: UploadFile (JPG/PNG/WebP, 最大10MB)
Response: {
  "success": true,
  "image_url": "data:image/jpeg;base64,..."
}
```

#### 6. 会话管理
```
GET /derma/{session_id}              // 获取会话详情
GET /derma?limit=20&offset=0         // 会话列表
DELETE /derma/{session_id}           // 删除会话
```

---

## 二、智能体 Prompt（系统行为规范）

### 核心能力
1. **皮肤影像分析**：调用 Qwen-VL 多模态模型，返回结构化 JSON
2. **报告解读**：OCR + LLM 解析医学报告指标
3. **问诊对话**：收集症状、病史，给出护理建议

### 交互流程

#### 场景1：用户提到"皮肤检测/上传照片/拍照"
**智能体行为**:
1. 返回拍摄指引：
   ```
   📸 为了更准确地分析，请按以下要求拍摄：
   - 光线充足，避免阴影
   - 背景简洁，皮损居中
   - 距离适中，对焦清晰
   - 不使用滤镜
   - 可拍摄多个角度
   ```
2. 设置 `awaiting_image = true`
3. 提供快捷按钮：`["去拍照", "从相册选择"]`

#### 场景2：收到皮肤图片
**智能体行为**:
1. 调用 `analyze_skin_image(image_url/base64)`
2. 期望 JSON 输出：
   ```json
   {
     "lesion_description": "手臂内侧可见多处红色丘疹，直径约2-3mm...",
     "possible_conditions": [
       {"name": "湿疹", "confidence": 0.75, "description": "过敏性皮炎的一种..."},
       {"name": "荨麻疹", "confidence": 0.60, "description": "..."}
     ],
     "risk_level": "medium",  // low | medium | high | emergency
     "care_advice": "避免搔抓，保持皮肤清洁干燥...",
     "need_offline_visit": true,
     "visit_urgency": "建议3天内就诊",
     "additional_questions": ["是否伴有瘙痒？", "持续多久了？"]
   }
   ```
3. 转换为自然语言 + Markdown 展示：
   ```
   🔍 **分析结果**
   
   **皮损描述**：手臂内侧可见多处红色丘疹...
   
   **可能病症**：
   - 湿疹（可能性75%）：过敏性皮炎的一种...
   - 荨麻疹（可能性60%）：...
   
   **风险等级**：⚠️ 中度
   
   **护理建议**：
   - 避免搔抓，保持皮肤清洁干燥
   - ...
   
   **就医建议**：建议3天内就诊皮肤科
   
   ⚕️ AI仅供参考，如症状加重请及时线下就医。
   ```
4. 继续追问 `additional_questions` 中的问题

#### 场景3：用户提到"报告解读/检验单/体检报告"
**智能体行为**:
1. 提示上传要求：
   ```
   📄 请上传您的检查报告：
   - 支持图片格式（JPG/PNG）或PDF
   - 确保文字清晰可读
   - 可上传多页报告
   ```
2. 设置 `awaiting_image = true`，`current_task = "report_interpret"`

#### 场景4：收到报告图片
**智能体行为**:
1. 调用 `interpret_medical_report(image_url/base64)`
2. 期望 JSON 输出：
   ```json
   {
     "report_type": "皮肤真菌检查报告",
     "report_date": "2026-01-01",
     "indicators": [
       {
         "name": "真菌镜检",
         "value": "阳性(+)",
         "reference_range": "阴性",
         "status": "abnormal",
         "explanation": "检出真菌孢子，提示真菌感染"
       }
     ],
     "summary": "检查显示真菌感染阳性...",
     "abnormal_findings": ["真菌镜检阳性"],
     "health_advice": ["需抗真菌治疗", "保持患处干燥", "避免共用毛巾"],
     "need_follow_up": true,
     "follow_up_suggestion": "治疗2周后复查"
   }
   ```
3. 展示为卡片形式（见 UI 设计）

#### 场景5：普通问诊对话
**智能体行为**:
1. 一次只问一个问题，重点追问：
   - 皮损部位（具体位置）
   - 持续时间（何时开始）
   - 症状特点（瘙痒/疼痛/渗液）
   - 伴随症状（发热/肿胀）
   - 过敏史（食物/药物/接触物）
   - 诱因（日晒/饮食/压力）
2. 缺少图片时提醒："如果方便，建议上传患处照片以便更准确分析"
3. 每次回复结尾加：`⚕️ AI仅供参考，如症状加重请及时线下就医。`

### 约束条件
- **JSON 严格性**：字段名必须与 Swift Model 一致（见 `DermaResponse`）
- **异常处理**：图像模糊/无法识别时明确提示并提供重试选项
- **高风险警告**：`risk_level = high/emergency` 时必须强调立即就医
- **置信度阈值**：`confidence < 0.4` 时坦诚说明不确定，建议面诊
- **免责声明**：所有输出必须包含免责声明

---

## 三、iOS 端实现方案

### 架构设计

```
DermaView (SwiftUI)
    ↓
DermaViewModel (@MainActor)
    ↓
APIService (网络层)
    ↓
Backend /derma/* (FastAPI)
```

### 1. 数据模型层 (Models)

#### 创建 `DermaModels.swift`

```swift
import Foundation

// MARK: - 皮肤病情况
struct SkinCondition: Codable, Identifiable {
    let id = UUID()
    let name: String
    let confidence: Double
    let description: String
    
    enum CodingKeys: String, CodingKey {
        case name, confidence, description
    }
}

// MARK: - 皮肤分析结果
struct SkinAnalysisResult: Codable {
    let lesionDescription: String
    let possibleConditions: [SkinCondition]
    let riskLevel: String  // low, medium, high, emergency
    let careAdvice: String
    let needOfflineVisit: Bool
    let visitUrgency: String?
    let additionalQuestions: [String]?
    
    enum CodingKeys: String, CodingKey {
        case lesionDescription = "lesion_description"
        case possibleConditions = "possible_conditions"
        case riskLevel = "risk_level"
        case careAdvice = "care_advice"
        case needOfflineVisit = "need_offline_visit"
        case visitUrgency = "visit_urgency"
        case additionalQuestions = "additional_questions"
    }
}

// MARK: - 报告指标
struct ReportIndicator: Codable, Identifiable {
    let id = UUID()
    let name: String
    let value: String
    let referenceRange: String?
    let status: String  // normal, high, low, abnormal
    let explanation: String?
    
    enum CodingKeys: String, CodingKey {
        case name, value, status, explanation
        case referenceRange = "reference_range"
    }
}

// MARK: - 报告解读结果
struct ReportInterpretation: Codable {
    let reportType: String
    let reportDate: String?
    let indicators: [ReportIndicator]
    let summary: String
    let abnormalFindings: [String]
    let healthAdvice: [String]
    let needFollowUp: Bool
    let followUpSuggestion: String?
    
    enum CodingKeys: String, CodingKey {
        case reportType = "report_type"
        case reportDate = "report_date"
        case indicators, summary
        case abnormalFindings = "abnormal_findings"
        case healthAdvice = "health_advice"
        case needFollowUp = "need_follow_up"
        case followUpSuggestion = "follow_up_suggestion"
    }
}

// MARK: - 快捷选项
struct DermaQuickOption: Codable, Identifiable {
    let id = UUID()
    let text: String
    let value: String
    let category: String
    
    enum CodingKeys: String, CodingKey {
        case text, value, category
    }
}

// MARK: - 皮肤科消息
struct DermaMessage: Identifiable {
    let id: UUID
    let role: MessageRole
    let content: String
    let timestamp: Date
    let quickOptions: [DermaQuickOption]?
    let skinAnalysis: SkinAnalysisResult?
    let reportInterpretation: ReportInterpretation?
    
    enum MessageRole: String {
        case user
        case assistant
    }
    
    var isFromUser: Bool { role == .user }
}

// MARK: - API 响应
struct DermaResponse: Codable {
    let type: String  // conversation, skin_analysis, report_interpret
    let sessionId: String
    let message: String
    let quickOptions: [DermaQuickOption]?
    let progress: Int
    let stage: String
    let awaitingImage: Bool
    let skinAnalysis: SkinAnalysisResult?
    let reportInterpretation: ReportInterpretation?
    let riskLevel: String?
    let needOfflineVisit: Bool?
    let careAdvice: String?
    
    enum CodingKeys: String, CodingKey {
        case type, message, progress, stage
        case sessionId = "session_id"
        case quickOptions = "quick_options"
        case awaitingImage = "awaiting_image"
        case skinAnalysis = "skin_analysis"
        case reportInterpretation = "report_interpretation"
        case riskLevel = "risk_level"
        case needOfflineVisit = "need_offline_visit"
        case careAdvice = "care_advice"
    }
}

// MARK: - 请求模型
struct StartDermaRequest: Encodable {
    let chiefComplaint: String?
    
    enum CodingKeys: String, CodingKey {
        case chiefComplaint = "chief_complaint"
    }
}

struct DermaMessageRequest: Encodable {
    let role: String
    let message: String
    let timestamp: String
}

struct ContinueDermaRequest: Encodable {
    let history: [DermaMessageRequest]
    let currentInput: CurrentInput
    let taskType: String?
    
    struct CurrentInput: Encodable {
        let message: String?
    }
    
    enum CodingKeys: String, CodingKey {
        case history
        case currentInput = "current_input"
        case taskType = "task_type"
    }
}

struct ImageUploadResponse: Codable {
    let success: Bool
    let imageUrl: String?
    let error: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case imageUrl = "image_url"
        case error
    }
}
```

### 2. 网络层 (APIService 扩展)

#### 在 `APIService.swift` 中添加

```swift
// MARK: - 皮肤科AI智能体

/// 开始皮肤科会话（支持SSE流式）
func startDermaSession(
    chiefComplaint: String = "",
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) async {
    let endpoint = "/derma/start"
    guard let url = URL(string: APIConfig.baseURL + endpoint) else {
        onError(APIError.invalidURL)
        return
    }
    
    guard let token = AuthManager.shared.token else {
        onError(APIError.unauthorized)
        return
    }
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    
    let body = StartDermaRequest(chiefComplaint: chiefComplaint.isEmpty ? nil : chiefComplaint)
    
    do {
        request.httpBody = try JSONEncoder().encode(body)
    } catch {
        onError(APIError.networkError(error))
        return
    }
    
    await processSSEStream(request: request, onChunk: onChunk, onComplete: onComplete, onError: onError)
}

/// 继续皮肤科对话（支持SSE流式）
func continueDermaSession(
    sessionId: String,
    history: [DermaMessageRequest],
    currentMessage: String?,
    taskType: String? = nil,
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) async {
    let endpoint = "/derma/\(sessionId)/continue"
    guard let url = URL(string: APIConfig.baseURL + endpoint) else {
        onError(APIError.invalidURL)
        return
    }
    
    guard let token = AuthManager.shared.token else {
        onError(APIError.unauthorized)
        return
    }
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    
    let body = ContinueDermaRequest(
        history: history,
        currentInput: ContinueDermaRequest.CurrentInput(message: currentMessage),
        taskType: taskType
    )
    
    do {
        request.httpBody = try JSONEncoder().encode(body)
    } catch {
        onError(APIError.networkError(error))
        return
    }
    
    await processSSEStream(request: request, onChunk: onChunk, onComplete: onComplete, onError: onError)
}

/// 上传并分析皮肤图片
func analyzeSkinImage(
    sessionId: String,
    imageData: Data,
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) async {
    // 1. 先上传图片获取Base64
    let uploadEndpoint = "/derma/\(sessionId)/upload-image"
    guard let uploadUrl = URL(string: APIConfig.baseURL + uploadEndpoint) else {
        onError(APIError.invalidURL)
        return
    }
    
    guard let token = AuthManager.shared.token else {
        onError(APIError.unauthorized)
        return
    }
    
    // 构造 multipart/form-data
    let boundary = UUID().uuidString
    var uploadRequest = URLRequest(url: uploadUrl)
    uploadRequest.httpMethod = "POST"
    uploadRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    uploadRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"skin.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    uploadRequest.httpBody = body
    
    do {
        let (data, _) = try await URLSession.shared.data(for: uploadRequest)
        let uploadResponse = try JSONDecoder().decode(ImageUploadResponse.self, from: data)
        
        guard uploadResponse.success, let imageUrl = uploadResponse.imageUrl else {
            onError(APIError.serverError(uploadResponse.error ?? "上传失败"))
            return
        }
        
        // 2. 调用分析接口
        let analyzeEndpoint = "/derma/\(sessionId)/analyze-skin"
        guard let analyzeUrl = URL(string: APIConfig.baseURL + analyzeEndpoint) else {
            onError(APIError.invalidURL)
            return
        }
        
        var analyzeRequest = URLRequest(url: analyzeUrl)
        analyzeRequest.httpMethod = "POST"
        analyzeRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        analyzeRequest.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        analyzeRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var analyzeBody = Data()
        analyzeBody.append("--\(boundary)\r\n".data(using: .utf8)!)
        analyzeBody.append("Content-Disposition: form-data; name=\"image_url\"\r\n\r\n".data(using: .utf8)!)
        analyzeBody.append(imageUrl.data(using: .utf8)!)
        analyzeBody.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        analyzeRequest.httpBody = analyzeBody
        
        await processSSEStream(request: analyzeRequest, onChunk: onChunk, onComplete: onComplete, onError: onError)
        
    } catch {
        onError(APIError.networkError(error))
    }
}

/// 解读医学报告
func interpretReport(
    sessionId: String,
    imageData: Data,
    reportType: String = "皮肤科检查报告",
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) async {
    // 实现类似 analyzeSkinImage，调用 /derma/{session_id}/interpret-report
    // 省略重复代码...
}

/// 通用SSE流处理
private func processSSEStream(
    request: URLRequest,
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) async {
    do {
        let (bytes, response) = try await URLSession.shared.bytes(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            onError(APIError.serverError("无效的响应"))
            return
        }
        
        if httpResponse.statusCode == 401 {
            DispatchQueue.main.async {
                NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
            }
            onError(APIError.unauthorized)
            return
        }
        
        if httpResponse.statusCode >= 400 {
            onError(APIError.serverError("请求失败: \(httpResponse.statusCode)"))
            return
        }
        
        var currentEvent = ""
        var currentData = ""
        
        for try await line in bytes.lines {
            if line.hasPrefix("event: ") {
                currentEvent = String(line.dropFirst(7))
            } else if line.hasPrefix("data: ") {
                currentData = String(line.dropFirst(6))
                
                await MainActor.run {
                    processDermaSSEEvent(
                        event: currentEvent,
                        data: currentData,
                        onChunk: onChunk,
                        onComplete: onComplete,
                        onError: onError
                    )
                }
                
                currentEvent = ""
                currentData = ""
            }
        }
    } catch {
        onError(APIError.networkError(error))
    }
}

private func processDermaSSEEvent(
    event: String,
    data: String,
    onChunk: @escaping (String) -> Void,
    onComplete: @escaping (DermaResponse) -> Void,
    onError: @escaping (Error) -> Void
) {
    switch event {
    case "chunk":
        if let jsonData = data.data(using: .utf8),
           let chunkObj = try? JSONDecoder().decode(SSEChunkData.self, from: jsonData) {
            onChunk(chunkObj.text)
        }
    case "complete":
        if let jsonData = data.data(using: .utf8) {
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                let response = try decoder.decode(DermaResponse.self, from: jsonData)
                onComplete(response)
            } catch {
                onError(APIError.decodingError(error))
            }
        }
    case "error":
        if let jsonData = data.data(using: .utf8),
           let errorObj = try? JSONDecoder().decode(SSEErrorData.self, from: jsonData) {
            onError(APIError.serverError(errorObj.error))
        }
    default:
        break
    }
}
```

### 3. ViewModel 层

#### 创建 `DermaViewModel.swift`

```swift
import Foundation
import SwiftUI

@MainActor
class DermaViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var messages: [DermaMessage] = []
    @Published var quickOptions: [DermaQuickOption] = []
    @Published var sessionId: String?
    @Published var stage: String = "greeting"
    @Published var progress: Int = 0
    @Published var awaitingImage: Bool = false
    
    // 分析结果
    @Published var latestSkinAnalysis: SkinAnalysisResult?
    @Published var latestReportInterpretation: ReportInterpretation?
    
    // UI状态
    @Published var isLoading: Bool = false
    @Published var isSending: Bool = false
    @Published var showError: Bool = false
    @Published var errorMessage: String = ""
    @Published var showImagePicker: Bool = false
    @Published var imagePickerSourceType: UIImagePickerController.SourceType = .camera
    
    // 流式消息
    @Published var streamingMessageId: UUID?
    @Published var streamingContent: String = ""
    
    // MARK: - Public Methods
    
    func startSession(chiefComplaint: String = "") async {
        isLoading = true
        isSending = true
        
        let tempMessageId = UUID()
        streamingMessageId = tempMessageId
        streamingContent = ""
        
        let tempMessage = DermaMessage(
            id: tempMessageId,
            role: .assistant,
            content: "",
            timestamp: Date(),
            quickOptions: nil,
            skinAnalysis: nil,
            reportInterpretation: nil
        )
        messages.append(tempMessage)
        
        await APIService.shared.startDermaSession(
            chiefComplaint: chiefComplaint,
            onChunk: { [weak self] chunk in
                Task { @MainActor in
                    self?.handleStreamingChunk(chunk)
                }
            },
            onComplete: { [weak self] response in
                Task { @MainActor in
                    self?.handleStreamingComplete(response)
                    self?.isLoading = false
                }
            },
            onError: { [weak self] error in
                Task { @MainActor in
                    self?.handleStreamingError(error)
                    self?.isLoading = false
                }
            }
        )
    }
    
    func sendMessage(_ content: String) async {
        guard let sessionId = sessionId else {
            showError("会话不存在")
            return
        }
        
        isSending = true
        
        // 添加用户消息
        let userMessage = DermaMessage(
            id: UUID(),
            role: .user,
            content: content,
            timestamp: Date(),
            quickOptions: nil,
            skinAnalysis: nil,
            reportInterpretation: nil
        )
        messages.append(userMessage)
        quickOptions = []
        
        // 创建临时AI消息
        let tempMessageId = UUID()
        streamingMessageId = tempMessageId
        streamingContent = ""
        
        let tempMessage = DermaMessage(
            id: tempMessageId,
            role: .assistant,
            content: "",
            timestamp: Date(),
            quickOptions: nil,
            skinAnalysis: nil,
            reportInterpretation: nil
        )
        messages.append(tempMessage)
        
        let history = buildHistoryMessages()
        
        await APIService.shared.continueDermaSession(
            sessionId: sessionId,
            history: history,
            currentMessage: content,
            onChunk: { [weak self] chunk in
                Task { @MainActor in
                    self?.handleStreamingChunk(chunk)
                }
            },
            onComplete: { [weak self] response in
                Task { @MainActor in
                    self?.handleStreamingComplete(response)
                }
            },
            onError: { [weak self] error in
                Task { @MainActor in
                    self?.handleStreamingError(error)
                }
            }
        )
    }
    
    func uploadSkinPhoto(_ image: UIImage) async {
        guard let sessionId = sessionId else {
            showError("会话不存在")
            return
        }
        
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            showError("图片处理失败")
            return
        }
        
        isSending = true
        
        // 创建临时消息
        let tempMessageId = UUID()
        streamingMessageId = tempMessageId
        streamingContent = ""
        
        let tempMessage = DermaMessage(
            id: tempMessageId,
            role: .assistant,
            content: "正在分析图片...",
            timestamp: Date(),
            quickOptions: nil,
            skinAnalysis: nil,
            reportInterpretation: nil
        )
        messages.append(tempMessage)
        
        await APIService.shared.analyzeSkinImage(
            sessionId: sessionId,
            imageData: imageData,
            onChunk: { [weak self] chunk in
                Task { @MainActor in
                    self?.handleStreamingChunk(chunk)
                }
            },
            onComplete: { [weak self] response in
                Task { @MainActor in
                    self?.handleStreamingComplete(response)
                }
            },
            onError: { [weak self] error in
                Task { @MainActor in
                    self?.handleStreamingError(error)
                }
            }
        )
    }
    
    func selectQuickOption(_ option: DermaQuickOption) async {
        await sendMessage(option.value)
    }
    
    func reset() {
        messages = []
        quickOptions = []
        sessionId = nil
        stage = "greeting"
        progress = 0
        awaitingImage = false
        latestSkinAnalysis = nil
        latestReportInterpretation = nil
        streamingMessageId = nil
        streamingContent = ""
    }
    
    // MARK: - Private Methods
    
    private func buildHistoryMessages() -> [DermaMessageRequest] {
        let recentMessages = messages.suffix(10)
        return recentMessages.map { msg in
            DermaMessageRequest(
                role: msg.role.rawValue,
                message: msg.content,
                timestamp: ISO8601DateFormatter().string(from: msg.timestamp)
            )
        }
    }
    
    private func handleStreamingChunk(_ chunk: String) {
        streamingContent += chunk
        
        if let messageId = streamingMessageId,
           let index = messages.firstIndex(where: { $0.id == messageId }) {
            messages[index] = DermaMessage(
                id: messageId,
                role: .assistant,
                content: streamingContent,
                timestamp: messages[index].timestamp,
                quickOptions: nil,
                skinAnalysis: nil,
                reportInterpretation: nil
            )
        }
    }
    
    private func handleStreamingComplete(_ response: DermaResponse) {
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }
        
        streamingMessageId = nil
        streamingContent = ""
        isSending = false
        
        handleResponse(response)
    }
    
    private func handleStreamingError(_ error: Error) {
        if let messageId = streamingMessageId {
            messages.removeAll { $0.id == messageId }
        }
        
        streamingMessageId = nil
        streamingContent = ""
        isSending = false
        
        if let apiError = error as? APIError {
            showError(apiError.errorDescription ?? "发送消息失败")
        } else {
            showError("网络错误，请稍后重试")
        }
    }
    
    private func handleResponse(_ response: DermaResponse) {
        sessionId = response.sessionId
        stage = response.stage
        progress = response.progress
        awaitingImage = response.awaitingImage
        
        if let analysis = response.skinAnalysis {
            latestSkinAnalysis = analysis
        }
        
        if let interpretation = response.reportInterpretation {
            latestReportInterpretation = interpretation
        }
        
        let aiMessage = DermaMessage(
            id: UUID(),
            role: .assistant,
            content: response.message,
            timestamp: Date(),
            quickOptions: response.quickOptions,
            skinAnalysis: response.skinAnalysis,
            reportInterpretation: response.reportInterpretation
        )
        messages.append(aiMessage)
        
        quickOptions = response.quickOptions ?? []
    }
    
    private func showError(_ message: String) {
        errorMessage = message
        showError = true
    }
}
```

### 4. UI 层

#### 创建 `DermaView.swift`

```swift
import SwiftUI

struct DermaView: View {
    @StateObject private var viewModel = DermaViewModel()
    @Environment(\.dismiss) private var dismiss
    @State private var inputText: String = ""
    
    var body: some View {
        VStack(spacing: 0) {
            // 顶部导航
            navigationBar
            
            // 进度指示
            if viewModel.progress > 0 {
                ProgressView(value: Double(viewModel.progress), total: 100)
                    .padding(.horizontal)
            }
            
            // 消息列表
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            DermaMessageBubble(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) { _ in
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            // 快捷选项
            if !viewModel.quickOptions.isEmpty {
                quickOptionsView
            }
            
            // 输入区域
            inputArea
        }
        .navigationBarHidden(true)
        .task {
            await viewModel.startSession()
        }
        .sheet(isPresented: $viewModel.showImagePicker) {
            ImagePicker(
                sourceType: viewModel.imagePickerSourceType,
                onImagePicked: { image in
                    Task {
                        await viewModel.uploadSkinPhoto(image)
                    }
                }
            )
        }
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage)
        }
    }
    
    private var navigationBar: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .foregroundColor(.primary)
            }
            
            Text("皮肤科AI智能体")
                .font(.headline)
            
            Spacer()
            
            Button(action: {
                viewModel.reset()
                Task {
                    await viewModel.startSession()
                }
            }) {
                Image(systemName: "arrow.clockwise")
                    .foregroundColor(.primary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
    }
    
    private var quickOptionsView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(viewModel.quickOptions) { option in
                    Button(action: {
                        Task {
                            await viewModel.selectQuickOption(option)
                        }
                    }) {
                        Text(option.text)
                            .font(.subheadline)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(16)
                    }
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 8)
    }
    
    private var inputArea: some View {
        HStack(spacing: 12) {
            // 拍照按钮
            if viewModel.awaitingImage {
                Button(action: {
                    viewModel.imagePickerSourceType = .camera
                    viewModel.showImagePicker = true
                }) {
                    Image(systemName: "camera.fill")
                        .foregroundColor(.blue)
                        .frame(width: 40, height: 40)
                }
                
                Button(action: {
                    viewModel.imagePickerSourceType = .photoLibrary
                    viewModel.showImagePicker = true
                }) {
                    Image(systemName: "photo.fill")
                        .foregroundColor(.blue)
                        .frame(width: 40, height: 40)
                }
            }
            
            // 文本输入
            TextField("输入消息...", text: $inputText)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .disabled(viewModel.isSending)
            
            // 发送按钮
            Button(action: {
                guard !inputText.isEmpty else { return }
                let message = inputText
                inputText = ""
                Task {
                    await viewModel.sendMessage(message)
                }
            }) {
                Image(systemName: "paperplane.fill")
                    .foregroundColor(inputText.isEmpty ? .gray : .blue)
            }
            .disabled(inputText.isEmpty || viewModel.isSending)
        }
        .padding()
        .background(Color(.systemBackground))
    }
}

// MARK: - 消息气泡
struct DermaMessageBubble: View {
    let message: DermaMessage
    
    var body: some View {
        HStack {
            if message.isFromUser {
                Spacer()
            }
            
            VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 8) {
                Text(message.content)
                    .padding(12)
                    .background(message.isFromUser ? Color.blue : Color(.systemGray5))
                    .foregroundColor(message.isFromUser ? .white : .primary)
                    .cornerRadius(16)
                
                // 皮肤分析卡片
                if let analysis = message.skinAnalysis {
                    SkinAnalysisCard(analysis: analysis)
                }
                
                // 报告解读卡片
                if let interpretation = message.reportInterpretation {
                    ReportInterpretationCard(interpretation: interpretation)
                }
            }
            .frame(maxWidth: UIScreen.main.bounds.width * 0.75, alignment: message.isFromUser ? .trailing : .leading)
            
            if !message.isFromUser {
                Spacer()
            }
        }
    }
}

// MARK: - 皮肤分析卡片
struct SkinAnalysisCard: View {
    let analysis: SkinAnalysisResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("🔍 分析结果")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("**皮损描述**")
                    .font(.subheadline)
                Text(analysis.lesionDescription)
                    .font(.body)
                    .foregroundColor(.secondary)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("**可能病症**")
                    .font(.subheadline)
                ForEach(analysis.possibleConditions) { condition in
                    HStack {
                        Text(condition.name)
                            .font(.body)
                        Spacer()
                        Text("\(Int(condition.confidence * 100))%")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                    Text(condition.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            HStack {
                Text("**风险等级**")
                    .font(.subheadline)
                Spacer()
                Text(riskLevelText)
                    .font(.body)
                    .foregroundColor(riskLevelColor)
            }
            
            if analysis.needOfflineVisit {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                    Text(analysis.visitUrgency ?? "建议线下就诊")
                        .font(.subheadline)
                        .foregroundColor(.orange)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
    
    private var riskLevelText: String {
        switch analysis.riskLevel {
        case "low": return "低风险"
        case "medium": return "中度风险"
        case "high": return "高风险"
        case "emergency": return "紧急"
        default: return analysis.riskLevel
        }
    }
    
    private var riskLevelColor: Color {
        switch analysis.riskLevel {
        case "low": return .green
        case "medium": return .orange
        case "high", "emergency": return .red
        default: return .gray
        }
    }
}

// MARK: - 报告解读卡片
struct ReportInterpretationCard: View {
    let interpretation: ReportInterpretation
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("📄 报告解读")
                .font(.headline)
            
            Text(interpretation.reportType)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if !interpretation.indicators.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("**检查指标**")
                        .font(.subheadline)
                    ForEach(interpretation.indicators) { indicator in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(indicator.name)
                                    .font(.body)
                                if let explanation = indicator.explanation {
                                    Text(explanation)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            Spacer()
                            Text(indicator.value)
                                .font(.body)
                                .foregroundColor(indicatorColor(indicator.status))
                        }
                    }
                }
            }
            
            if !interpretation.abnormalFindings.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("**异常发现**")
                        .font(.subheadline)
                    ForEach(interpretation.abnormalFindings, id: \.self) { finding in
                        Text("• \(finding)")
                            .font(.body)
                            .foregroundColor(.orange)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
    
    private func indicatorColor(_ status: String) -> Color {
        switch status {
        case "normal": return .green
        case "high", "low", "abnormal": return .red
        default: return .gray
        }
    }
}

// MARK: - ImagePicker (UIKit wrapper)
struct ImagePicker: UIViewControllerRepresentable {
    let sourceType: UIImagePickerController.SourceType
    let onImagePicked: (UIImage) -> Void
    @Environment(\.dismiss) private var dismiss
    
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = sourceType
        picker.delegate = context.coordinator
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        
        init(_ parent: ImagePicker) {
            self.parent = parent
        }
        
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let image = info[.originalImage] as? UIImage {
                parent.onImagePicked(image)
            }
            parent.dismiss()
        }
        
        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}
```

### 5. 入口集成

#### 在 `DoctorChatView.swift` 中添加入口

```swift
// 在导航栏或顶部添加按钮
NavigationLink(destination: DermaView()) {
    HStack {
        Image(systemName: "cross.case.fill")
        Text("皮肤检测")
    }
    .padding()
    .background(Color.blue.opacity(0.1))
    .cornerRadius(12)
}
```

---

## 四、前面提示词完整性评估

### ✅ 已覆盖
1. **核心能力定义**：皮肤分析、报告解读、问诊对话
2. **交互流程**：拍摄指引、图片上传、结果展示
3. **JSON 结构**：与后端 Schema 严格对应
4. **异常处理**：模糊图片、低置信度、高风险警告
5. **免责声明**：每次输出结尾强制添加

### ⚠️ 需补充
1. **拍摄指引文案**：已在 Prompt 中给出，需在 UI 常量中定义
2. **报告上传指引**：同上
3. **多图上传**：当前仅支持单图，可扩展为数组
4. **离线缓存**：会话历史本地持久化（可选）
5. **语音输入**：集成现有语音转文字（可选）

### 📝 建议优化
1. **错误重试机制**：网络失败时自动重试 3 次
2. **图片压缩策略**：根据网络状况动态调整质量
3. **敏感词过滤**：医疗相关敏感词检测
4. **埋点统计**：分析成功率、用户行为

---

## 五、实施步骤

### Phase 1: 基础集成（1-2天）
1. 创建 `DermaModels.swift`
2. 扩展 `APIService.swift` 添加皮肤科接口
3. 创建 `DermaViewModel.swift` 实现基础逻辑
4. 创建简单的 `DermaView.swift` 测试流程

### Phase 2: UI 完善（2-3天）
1. 实现消息气泡样式
2. 实现皮肤分析卡片
3. 实现报告解读卡片
4. 添加图片选择器
5. 优化流式输出动画

### Phase 3: 功能增强（1-2天）
1. 添加会话历史列表
2. 实现离线缓存
3. 添加分享功能
4. 集成语音输入（可选）

### Phase 4: 测试与优化（1-2天）
1. 单元测试
2. UI 测试
3. 性能优化
4. 异常场景覆盖

---

## 六、注意事项

1. **隐私合规**：
   - 图片上传前需用户授权
   - 敏感数据加密传输
   - 符合 HIPAA/GDPR 要求

2. **性能优化**：
   - 图片压缩至 500KB 以内
   - 使用 LazyVStack 优化长列表
   - SSE 连接超时处理

3. **用户体验**：
   - 加载状态明确提示
   - 错误信息友好展示
   - 支持暗黑模式

4. **医疗免责**：
   - 每次输出必须包含免责声明
   - 高风险情况强制提示就医
   - 不做确定性诊断

---

## 七、API 测试示例

### 使用 curl 测试

```bash
# 1. 开始会话
curl -X POST http://xinling.natapp1.cc/derma/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"chief_complaint": "手臂起红疹"}'

# 2. 上传图片
curl -X POST http://xinling.natapp1.cc/derma/{session_id}/upload-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@skin.jpg"

# 3. 分析皮肤
curl -X POST http://xinling.natapp1.cc/derma/{session_id}/analyze-skin \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: text/event-stream" \
  -F "image_url=data:image/jpeg;base64,..."
```

---

**文档版本**: v1.0  
**更新日期**: 2026-01-03  
**维护者**: 开发团队
