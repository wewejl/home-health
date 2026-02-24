import Foundation
import UIKit

// MARK: - 智能体类型
enum AgentType: String, Codable, CaseIterable {
    case general = "general"
    case dermatology = "dermatology"
    case cardiology = "cardiology"
    case orthopedics = "orthopedics"

    var displayName: String {
        switch self {
        case .general: return "通用问诊"
        case .dermatology: return "皮肤科"
        case .cardiology: return "心内科"
        case .orthopedics: return "骨科"
        }
    }
}

// MARK: - 智能体动作
enum AgentAction: String, Codable {
    case conversation = "conversation"
    case analyzeSkin = "analyze_skin"
    case interpretReport = "interpret_report"
    case interpretECG = "interpret_ecg"

    var displayName: String {
        switch self {
        case .conversation: return "对话问诊"
        case .analyzeSkin: return "皮肤分析"
        case .interpretReport: return "报告解读"
        case .interpretECG: return "心电图解读"
        }
    }
}

// MARK: - 智能体能力配置
// 类型别名：使用 UnifiedChatAPIService 中定义的 SessionAgentCapabilities
typealias AgentCapabilities = SessionAgentCapabilities

// MARK: - 附件
struct MessageAttachment: Codable {
    let type: String
    let url: String?
    let base64: String?
    let metadata: [String: AnyCodable]?

    init(type: String, url: String? = nil, base64: String? = nil, metadata: [String: AnyCodable]? = nil) {
        self.type = type
        self.url = url
        self.base64 = base64
        self.metadata = metadata
    }

    static func imageAttachment(base64: String) -> MessageAttachment {
        return MessageAttachment(type: "image", base64: base64)
    }

    static func imageAttachment(url: String) -> MessageAttachment {
        return MessageAttachment(type: "image", url: url)
    }
}

// MARK: - AnyCodable for flexible JSON
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let string = value as? String {
            try container.encode(string)
        } else if let int = value as? Int {
            try container.encode(int)
        } else if let double = value as? Double {
            try container.encode(double)
        } else if let bool = value as? Bool {
            try container.encode(bool)
        } else {
            try container.encodeNil()
        }
    }

    /// 转换为 Data 用于 JSON 解码
    var jsonData: Data {
        return (try? JSONEncoder().encode(self)) ?? Data()
    }
}

// MARK: - 快捷选项
struct QuickOption: Identifiable, Equatable {
    let id: String
    let text: String
    let value: String

    init(text: String, value: String) {
        self.id = UUID().uuidString
        self.text = text
        self.value = value
    }
}

// MARK: - 思考条目
struct ThoughtEntry: Identifiable, Codable, Equatable {
    let id: String
    let step: Int
    let timestamp: Date
    let thought: String
    let intentAnalysis: String?
    let stateAssessment: String?
    let decision: String?
    let action: String
    let toolUsed: String?

    init(
        id: String = UUID().uuidString,
        step: Int,
        timestamp: Date = Date(),
        thought: String,
        intentAnalysis: String? = nil,
        stateAssessment: String? = nil,
        decision: String? = nil,
        action: String,
        toolUsed: String? = nil
    ) {
        self.id = id
        self.step = step
        self.timestamp = timestamp
        self.thought = thought
        self.intentAnalysis = intentAnalysis
        self.stateAssessment = stateAssessment
        self.decision = decision
        self.action = action
        self.toolUsed = toolUsed
    }

    enum CodingKeys: String, CodingKey {
        case id
        case step
        case timestamp
        case thought
        case intentAnalysis = "intent_analysis"
        case stateAssessment = "state_assessment"
        case decision
        case action
        case toolUsed = "tool_used"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(String.self, forKey: .id) ?? UUID().uuidString
        step = try container.decode(Int.self, forKey: .step)

        // 🆕 自定义日期解码 - 支持多种 ISO8601 格式
        if let dateString = try container.decodeIfPresent(String.self, forKey: .timestamp) {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

            // 尝试标准格式
            if let date = formatter.date(from: dateString) {
                timestamp = date
            } else {
                // 尝试不带时区的格式
                let fallbackFormatter = DateFormatter()
                fallbackFormatter.locale = Locale(identifier: "en_US_POSIX")
                fallbackFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                if let date = fallbackFormatter.date(from: dateString) {
                    timestamp = date
                } else {
                    // 如果都失败，使用当前时间
                    timestamp = Date()
                }
            }
        } else {
            timestamp = Date()
        }

        thought = try container.decode(String.self, forKey: .thought)
        intentAnalysis = try container.decodeIfPresent(String.self, forKey: .intentAnalysis)
        stateAssessment = try container.decodeIfPresent(String.self, forKey: .stateAssessment)
        decision = try container.decodeIfPresent(String.self, forKey: .decision)
        action = try container.decode(String.self, forKey: .action)
        toolUsed = try container.decodeIfPresent(String.self, forKey: .toolUsed)
    }
}

// MARK: - 思考状态
enum ThinkingState: Equatable {
    case idle                // 无思考
    case thinking            // 正在思考中
    case completed([ThoughtEntry])  // 思考完成

    static func == (lhs: ThinkingState, rhs: ThinkingState) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.thinking, .thinking):
            return true
        case (.completed(let l1), .completed(let l2)):
            return l1.count == l2.count && zip(l1, l2).allSatisfy { $0.id == $1.id }
        default:
            return false
        }
    }
}

// MARK: - 统一消息类型
enum UnifiedMessageType: Equatable {
    case text
    case image(UIImage)
    case structuredResult(StructuredData)
    case loading
    case thinking(ThinkingState)  // 🆕 思考类型

    static func == (lhs: UnifiedMessageType, rhs: UnifiedMessageType) -> Bool {
        switch (lhs, rhs) {
        case (.text, .text), (.loading, .loading):
            return true
        case (.image(let i1), .image(let i2)):
            return i1 === i2
        case (.structuredResult(let d1), .structuredResult(let d2)):
            return d1.type == d2.type
        case (.thinking(let s1), .thinking(let s2)):
            return s1 == s2
        default:
            return false
        }
    }
}

// MARK: - 统一消息模型
struct UnifiedChatMessage: Identifiable {
    let id: UUID
    let content: String
    let isFromUser: Bool
    let timestamp: Date
    var messageType: UnifiedMessageType
    var attachments: [MessageAttachment]
    var quickOptions: [QuickOption]

    // 🆕 思考相关字段
    var thinkingState: ThinkingState
    var isThinkingExpanded: Bool  // 控制思考区域展开/收起

    // 持久化相关字段
    var localImageId: String?       // 本地图片ID (用于从本地加载图片)
    var serverMessageId: Int?       // 后端消息ID (用于同步)

    init(
        id: UUID = UUID(),
        content: String,
        isFromUser: Bool,
        timestamp: Date = Date(),
        messageType: UnifiedMessageType = .text,
        attachments: [MessageAttachment] = [],
        quickOptions: [QuickOption] = [],
        thinkingState: ThinkingState = .idle,
        isThinkingExpanded: Bool = false,
        localImageId: String? = nil,
        serverMessageId: Int? = nil
    ) {
        self.id = id
        self.content = content
        self.isFromUser = isFromUser
        self.timestamp = timestamp
        self.messageType = messageType
        self.attachments = attachments
        self.quickOptions = quickOptions
        self.thinkingState = thinkingState
        self.isThinkingExpanded = isThinkingExpanded
        self.localImageId = localImageId
        self.serverMessageId = serverMessageId
    }

    // 🆕 是否有思考内容
    var hasThinking: Bool {
        switch thinkingState {
        case .idle:
            return false
        case .thinking, .completed:
            return true
        }
    }

    static func userMessage(_ content: String, attachments: [MessageAttachment] = []) -> UnifiedChatMessage {
        return UnifiedChatMessage(content: content, isFromUser: true, attachments: attachments)
    }

    static func aiMessage(_ content: String, quickOptions: [QuickOption] = [], thinkingState: ThinkingState = .idle) -> UnifiedChatMessage {
        return UnifiedChatMessage(content: content, isFromUser: false, quickOptions: quickOptions, thinkingState: thinkingState)
    }

    static func loadingMessage() -> UnifiedChatMessage {
        return UnifiedChatMessage(content: "", isFromUser: false, messageType: .loading)
    }

    // 创建图片消息
    static func imageMessage(_ image: UIImage, content: String, localImageId: String?) -> UnifiedChatMessage {
        return UnifiedChatMessage(
            content: content,
            isFromUser: true,
            messageType: .image(image),
            localImageId: localImageId
        )
    }
}

// MARK: - Unified Session Response
struct UnifiedSessionResponse: Codable {
    let sessionId: String
    let agentType: String

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case agentType = "agent_type"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        sessionId = try container.decode(String.self, forKey: .sessionId)
        agentType = try container.decode(String.self, forKey: .agentType)
    }
}

// MARK: - Unified Message Response
struct UnifiedMessageResponse: Codable {
    let message: String
    let stage: String?
    let progress: Int?
    let quickOptions: [String]?
    let structuredData: StructuredData?
    let eventId: String?
    let isNewEvent: Bool?
    let shouldShowDossierPrompt: Bool?

    // 🆕 思考相关字段
    let currentThought: String?
    let reasoningHistory: [ThoughtEntry]?
    let showThinking: Bool?

    // 诊断相关计算属性
    var diagnosisCard: DiagnosisCard? {
        guard let diagnosisData = structuredData?.data?["diagnosis_card"] else { return nil }
        return diagnosisData.value as? DiagnosisCard
    }

    var adviceHistory: [AdviceEntry]? {
        guard let adviceData = structuredData?.data?["advice_history"] else { return nil }
        return adviceData.value as? [AdviceEntry]
    }

    var knowledgeRefs: [KnowledgeRef]? {
        guard let refsData = structuredData?.data?["knowledge_refs"] else { return nil }
        return refsData.value as? [KnowledgeRef]
    }

    var reasoningSteps: [String]? {
        guard let stepsData = structuredData?.data?["reasoning_steps"] else { return nil }
        return stepsData.value as? [String]
    }

    // 🆕 思考状态计算属性
    var thinkingState: ThinkingState {
        if let history = reasoningHistory, !history.isEmpty {
            return .completed(history)
        } else if let thought = currentThought, !thought.isEmpty {
            return .thinking
        }
        return .idle
    }

    enum CodingKeys: String, CodingKey {
        case message
        case stage
        case progress
        case quickOptions = "quick_options"
        case structuredData = "structured_data"
        case eventId = "event_id"
        case isNewEvent = "is_new_event"
        case shouldShowDossierPrompt = "should_show_dossier_prompt"
        case currentThought = "current_thought"
        case reasoningHistory = "reasoning_history"
        case showThinking = "show_thinking"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        message = try container.decode(String.self, forKey: .message)
        stage = try container.decodeIfPresent(String.self, forKey: .stage)
        progress = try container.decodeIfPresent(Int.self, forKey: .progress)
        quickOptions = try container.decodeIfPresent([String].self, forKey: .quickOptions)
        structuredData = try container.decodeIfPresent(StructuredData.self, forKey: .structuredData)
        eventId = try container.decodeIfPresent(String.self, forKey: .eventId)
        isNewEvent = try container.decodeIfPresent(Bool.self, forKey: .isNewEvent)
        shouldShowDossierPrompt = try container.decodeIfPresent(Bool.self, forKey: .shouldShowDossierPrompt)
        currentThought = try container.decodeIfPresent(String.self, forKey: .currentThought)
        reasoningHistory = try container.decodeIfPresent([ThoughtEntry].self, forKey: .reasoningHistory)
        showThinking = try container.decodeIfPresent(Bool.self, forKey: .showThinking)
    }
}

// MARK: - Advice Entry
struct AdviceEntry: Codable {
    let advice: String
    let reasoning: String
    let category: String?
    let relatedSymptoms: [String]?
    let timestamp: Date
}

// MARK: - Knowledge Reference
struct KnowledgeRef: Codable, Identifiable {
    let id: String
    let title: String
    let snippet: String
    let source: String
    let url: String?
    let authors: [String]?
    let publishedDate: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case snippet
        case source
        case url
        case authors
        case publishedDate = "published_date"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        snippet = try container.decode(String.self, forKey: .snippet)
        source = try container.decode(String.self, forKey: .source)
        url = try container.decodeIfPresent(String.self, forKey: .url)
        authors = try container.decodeIfPresent([String].self, forKey: .authors)
        publishedDate = try container.decodeIfPresent(Date.self, forKey: .publishedDate)
    }

    init(id: String, title: String, snippet: String, source: String, url: String? = nil, authors: [String]? = nil, publishedDate: Date? = nil) {
        self.id = id
        self.title = title
        self.snippet = snippet
        self.source = source
        self.url = url
        self.authors = authors
        self.publishedDate = publishedDate
    }
}

// MARK: - Diagnosis Condition
struct DiagnosisCondition: Codable {
    let name: String
    let confidence: Double
    let rationale: [String]

    enum CodingKeys: String, CodingKey {
        case name
        case confidence
        case rationale
    }

    init(name: String, confidence: Double, rationale: [String]) {
        self.name = name
        self.confidence = confidence
        self.rationale = rationale
    }
}

// MARK: - Diagnosis Card
struct DiagnosisCard: Codable {
    let summary: String
    let conditions: [DiagnosisCondition]
    let riskLevel: String
    let needOfflineVisit: Bool
    let urgency: String?
    let carePlan: [String]
    let references: [KnowledgeRef]
    let reasoningSteps: [String]

    enum CodingKeys: String, CodingKey {
        case summary
        case conditions
        case riskLevel = "risk_level"
        case needOfflineVisit = "need_offline_visit"
        case urgency
        case carePlan = "care_plan"
        case references = "references"
        case reasoningSteps = "reasoning_steps"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        summary = try container.decode(String.self, forKey: .summary)
        conditions = try container.decode([DiagnosisCondition].self, forKey: .conditions)
        riskLevel = try container.decode(String.self, forKey: .riskLevel)
        needOfflineVisit = try container.decodeIfPresent(Bool.self, forKey: .needOfflineVisit) ?? false
        urgency = try container.decodeIfPresent(String.self, forKey: .urgency)
        carePlan = try container.decode([String].self, forKey: .carePlan)
        references = try container.decode([KnowledgeRef].self, forKey: .references)
        reasoningSteps = try container.decode([String].self, forKey: .reasoningSteps)
    }

    init(
        summary: String,
        conditions: [DiagnosisCondition],
        riskLevel: String,
        needOfflineVisit: Bool,
        urgency: String? = nil,
        carePlan: [String],
        references: [KnowledgeRef],
        reasoningSteps: [String]
    ) {
        self.summary = summary
        self.conditions = conditions
        self.riskLevel = riskLevel
        self.needOfflineVisit = needOfflineVisit
        self.urgency = urgency
        self.carePlan = carePlan
        self.references = references
        self.reasoningSteps = reasoningSteps
    }
}

// MARK: - 结构化数据
struct StructuredData: Codable {
    let type: String
    let data: [String: AnyCodable]?

    var isSkinAnalysis: Bool {
        return type == "skin_analysis"
    }

    var isReportInterpretation: Bool {
        return type == "report_interpretation"
    }
}
