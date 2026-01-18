import Foundation

// MARK: - AgentResponse V2 统一响应格式
// 与后端 AgentResponse schema 完全对应

/// 统一智能体响应格式
struct AgentResponseV2: Codable {
    // MARK: - 基础字段（必填）
    let message: String
    let stage: String
    let progress: Int
    
    // MARK: - 可选字段
    let quickOptions: [String]
    let riskLevel: String?
    
    // 病历事件相关
    let eventId: String?
    let isNewEvent: Bool
    let shouldShowDossierPrompt: Bool
    
    // MARK: - 专科扩展数据
    let specialtyData: SpecialtyDataV2?
    
    // MARK: - 状态持久化
    let nextState: [String: AnyCodable]
    
    enum CodingKeys: String, CodingKey {
        case message
        case stage
        case progress
        case quickOptions = "quick_options"
        case riskLevel = "risk_level"
        case eventId = "event_id"
        case isNewEvent = "is_new_event"
        case shouldShowDossierPrompt = "should_show_dossier_prompt"
        case specialtyData = "specialty_data"
        case nextState = "next_state"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        message = try container.decode(String.self, forKey: .message)
        stage = try container.decode(String.self, forKey: .stage)
        progress = try container.decode(Int.self, forKey: .progress)
        quickOptions = try container.decodeIfPresent([String].self, forKey: .quickOptions) ?? []
        riskLevel = try container.decodeIfPresent(String.self, forKey: .riskLevel)
        eventId = try container.decodeIfPresent(String.self, forKey: .eventId)
        isNewEvent = try container.decodeIfPresent(Bool.self, forKey: .isNewEvent) ?? false
        shouldShowDossierPrompt = try container.decodeIfPresent(Bool.self, forKey: .shouldShowDossierPrompt) ?? false
        specialtyData = try container.decodeIfPresent(SpecialtyDataV2.self, forKey: .specialtyData)
        nextState = try container.decodeIfPresent([String: AnyCodable].self, forKey: .nextState) ?? [:]
    }
    
    /// 将快捷选项转换为 QuickOption 数组
    var quickOptionModels: [QuickOption] {
        return quickOptions.map { QuickOption(text: $0, value: $0) }
    }
    
    /// 阶段枚举
    var stageEnum: ConsultationStage {
        return ConsultationStage(rawValue: stage) ?? .collecting
    }
    
    /// 风险等级枚举
    var riskLevelEnum: RiskLevel? {
        guard let level = riskLevel else { return nil }
        return RiskLevel(rawValue: level)
    }
}

// MARK: - 问诊阶段
enum ConsultationStage: String, Codable {
    case greeting = "greeting"
    case collecting = "collecting"
    case analyzing = "analyzing"
    case diagnosing = "diagnosing"
    case completed = "completed"
    
    var displayName: String {
        switch self {
        case .greeting: return "开始问诊"
        case .collecting: return "收集信息"
        case .analyzing: return "分析中"
        case .diagnosing: return "诊断中"
        case .completed: return "问诊完成"
        }
    }
    
    var progressRange: ClosedRange<Int> {
        switch self {
        case .greeting: return 0...10
        case .collecting: return 10...50
        case .analyzing: return 50...70
        case .diagnosing: return 70...90
        case .completed: return 90...100
        }
    }
}

// MARK: - 风险等级
enum RiskLevel: String, Codable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case emergency = "emergency"
    
    var displayName: String {
        switch self {
        case .low: return "低风险"
        case .medium: return "中风险"
        case .high: return "高风险"
        case .emergency: return "紧急"
        }
    }
    
    var color: String {
        switch self {
        case .low: return "green"
        case .medium: return "orange"
        case .high: return "red"
        case .emergency: return "purple"
        }
    }
}

// MARK: - 专科扩展数据
struct SpecialtyDataV2: Codable {
    // 皮肤科相关
    let diagnosisCard: DiagnosisCardV2?
    let symptoms: [String]?
    
    // 通用字段 - 使用 AnyCodable 支持任意数据
    let rawData: [String: AnyCodable]?
    
    enum CodingKeys: String, CodingKey {
        case diagnosisCard = "diagnosis_card"
        case symptoms
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        diagnosisCard = try container.decodeIfPresent(DiagnosisCardV2.self, forKey: .diagnosisCard)
        symptoms = try container.decodeIfPresent([String].self, forKey: .symptoms)
        
        // 解析所有原始数据
        let rawContainer = try decoder.singleValueContainer()
        rawData = try? rawContainer.decode([String: AnyCodable].self)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(diagnosisCard, forKey: .diagnosisCard)
        try container.encodeIfPresent(symptoms, forKey: .symptoms)
    }
}

// MARK: - 诊断卡 V2
struct DiagnosisCardV2: Codable {
    let summary: String
    let conditions: [DiagnosisConditionV2]?
    let riskLevel: String?
    let needOfflineVisit: Bool?
    let urgency: String?
    let carePlan: [String]?
    let references: [KnowledgeReferenceV2]?
    let reasoningSteps: [String]?
    
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
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        summary = try container.decode(String.self, forKey: .summary)
        conditions = try container.decodeIfPresent([DiagnosisConditionV2].self, forKey: .conditions)
        riskLevel = try container.decodeIfPresent(String.self, forKey: .riskLevel)
        needOfflineVisit = try container.decodeIfPresent(Bool.self, forKey: .needOfflineVisit)
        urgency = try container.decodeIfPresent(String.self, forKey: .urgency)
        carePlan = try container.decodeIfPresent([String].self, forKey: .carePlan)
        references = try container.decodeIfPresent([KnowledgeReferenceV2].self, forKey: .references)
        reasoningSteps = try container.decodeIfPresent([String].self, forKey: .reasoningSteps)
    }
}

// MARK: - 诊断条目 V2
struct DiagnosisConditionV2: Codable {
    let name: String
    let confidence: Double
    let rationale: [String]?
    
    enum CodingKeys: String, CodingKey {
        case name
        case confidence
        case rationale
    }
    
    init(name: String, confidence: Double, rationale: [String]? = nil) {
        self.name = name
        self.confidence = confidence
        self.rationale = rationale
    }
}

// MARK: - 知识引用 V2
struct KnowledgeReferenceV2: Codable {
    let id: String
    let title: String
    let snippet: String
    let source: String?
    let link: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case snippet
        case source
        case link
    }
}

// MARK: - SSE 事件类型
enum SSEEventTypeV2: String {
    case meta = "meta"
    case chunk = "chunk"
    case complete = "complete"
    case error = "error"
}

// MARK: - SSE Meta 事件
struct SSEMetaEventV2: Codable {
    let sessionId: String
    let agentType: String
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case agentType = "agent_type"
    }
}

// MARK: - SSE Chunk 事件
struct SSEChunkEventV2: Codable {
    let text: String
}

// MARK: - SSE Error 事件
struct SSEErrorEventV2: Codable {
    let error: String
}
