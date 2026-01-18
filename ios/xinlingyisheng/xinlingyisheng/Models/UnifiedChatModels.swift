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
struct AgentCapabilities: Codable {
    let actions: [String]
    let acceptsMedia: [String]
    let uiComponents: [String]
    let description: String
    
    enum CodingKeys: String, CodingKey {
        case actions
        case acceptsMedia = "accepts_media"
        case uiComponents = "ui_components"
        case description
    }
    
    var supportsImageUpload: Bool {
        return acceptsMedia.contains { $0.starts(with: "image/") }
    }
    
    var supportsPdfUpload: Bool {
        return acceptsMedia.contains("application/pdf")
    }
}

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

// MARK: - 统一消息类型
enum UnifiedMessageType {
    case text
    case image(UIImage)
    case structuredResult(StructuredData)
    case loading
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
        self.localImageId = localImageId
        self.serverMessageId = serverMessageId
    }
    
    static func userMessage(_ content: String, attachments: [MessageAttachment] = []) -> UnifiedChatMessage {
        return UnifiedChatMessage(content: content, isFromUser: true, attachments: attachments)
    }
    
    static func aiMessage(_ content: String, quickOptions: [QuickOption] = []) -> UnifiedChatMessage {
        return UnifiedChatMessage(content: content, isFromUser: false, quickOptions: quickOptions)
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

// MARK: - 快捷选项
struct QuickOption: Identifiable, Codable {
    var id: UUID = UUID()
    let text: String
    let value: String
    let category: String
    
    enum CodingKeys: String, CodingKey {
        case text, value, category
    }
    
    init(text: String, value: String, category: String = "general") {
        self.text = text
        self.value = value
        self.category = category
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        text = try container.decode(String.self, forKey: .text)
        value = try container.decode(String.self, forKey: .value)
        category = try container.decodeIfPresent(String.self, forKey: .category) ?? "general"
    }
}

// MARK: - 诊断展示增强模型

/// 中间建议
struct AdviceEntry: Codable, Identifiable {
    let id: String
    let title: String
    let content: String
    let evidence: [String]
    let timestamp: String
    
    init(id: String, title: String, content: String, evidence: [String] = [], timestamp: String) {
        self.id = id
        self.title = title
        self.content = content
        self.evidence = evidence
        self.timestamp = timestamp
    }
}

/// 知识引用
struct KnowledgeRef: Codable, Identifiable {
    let id: String
    let title: String
    let snippet: String
    let source: String?
    let link: String?
    
    init(id: String, title: String, snippet: String, source: String? = nil, link: String? = nil) {
        self.id = id
        self.title = title
        self.snippet = snippet
        self.source = source
        self.link = link
    }
}

/// 鉴别诊断条目
struct DiagnosisCondition: Codable {
    let name: String
    let confidence: Double
    let rationale: [String]
    
    init(name: String, confidence: Double, rationale: [String] = []) {
        self.name = name
        self.confidence = confidence
        self.rationale = rationale
    }
}

/// 诊断卡
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
        case references
        case reasoningSteps = "reasoning_steps"
    }
    
    init(
        summary: String,
        conditions: [DiagnosisCondition],
        riskLevel: String,
        needOfflineVisit: Bool,
        urgency: String? = nil,
        carePlan: [String] = [],
        references: [KnowledgeRef] = [],
        reasoningSteps: [String] = []
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

// MARK: - API Response Models

struct UnifiedSessionResponse: Codable {
    let sessionId: String
    let doctorId: Int?
    let doctorName: String?
    let agentType: String
    let lastMessage: String?
    let status: String
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case doctorId = "doctor_id"
        case doctorName = "doctor_name"
        case agentType = "agent_type"
        case lastMessage = "last_message"
        case status
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct UnifiedMessageResponse: Codable {
    let message: String
    let structuredData: StructuredData?
    let quickOptions: [QuickOption]?
    let stage: String?
    let progress: Int?
    let eventId: String?
    let isNewEvent: Bool?
    let shouldShowDossierPrompt: Bool?
    
    // 诊断展示增强字段
    let adviceHistory: [AdviceEntry]?
    let diagnosisCard: DiagnosisCard?
    let knowledgeRefs: [KnowledgeRef]?
    let reasoningSteps: [String]?
    
    enum CodingKeys: String, CodingKey {
        case message
        case structuredData = "structured_data"
        case quickOptions = "quick_options"
        case stage
        case progress
        case eventId = "event_id"
        case isNewEvent = "is_new_event"
        case shouldShowDossierPrompt = "should_show_dossier_prompt"
        case adviceHistory = "advice_history"
        case diagnosisCard = "diagnosis_card"
        case knowledgeRefs = "knowledge_refs"
        case reasoningSteps = "reasoning_steps"
    }
}

// Note: SendMessageRequest and CreateSessionRequest are defined in APIService.swift
