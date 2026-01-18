import Foundation
import SwiftUI

// MARK: - 科室类型
enum DepartmentType: String, Codable, CaseIterable {
    case dermatology = "dermatology"
    case cardiology = "cardiology"
    case general = "general"
    case pediatrics = "pediatrics"
    case gynecology = "gynecology"
    case neurology = "neurology"
    case gastroenterology = "gastroenterology"
    case orthopedics = "orthopedics"
    
    var displayName: String {
        switch self {
        case .dermatology: return "皮肤科"
        case .cardiology: return "心内科"
        case .general: return "全科"
        case .pediatrics: return "儿科"
        case .gynecology: return "妇科"
        case .neurology: return "神经科"
        case .gastroenterology: return "消化科"
        case .orthopedics: return "骨科"
        }
    }
    
    var icon: String {
        switch self {
        case .dermatology: return "hand.raised.fingers.spread"
        case .cardiology: return "heart.fill"
        case .general: return "stethoscope"
        case .pediatrics: return "figure.and.child.holdinghands"
        case .gynecology: return "person.crop.circle"
        case .neurology: return "brain.head.profile"
        case .gastroenterology: return "stomach"
        case .orthopedics: return "figure.walk"
        }
    }
    
    var color: Color {
        switch self {
        case .dermatology: return DXYColors.teal
        case .cardiology: return Color.red
        case .general: return DXYColors.primaryPurple
        case .pediatrics: return Color.orange
        case .gynecology: return Color.pink
        case .neurology: return Color.purple
        case .gastroenterology: return Color.green
        case .orthopedics: return Color.blue
        }
    }
}

// MARK: - 风险等级
enum DossierRiskLevel: String, Codable, CaseIterable {
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
    
    var color: Color {
        switch self {
        case .low: return DossierColors.riskLow
        case .medium: return DossierColors.riskMedium
        case .high: return DossierColors.riskHigh
        case .emergency: return DossierColors.riskEmergency
        }
    }
    
    var icon: String {
        switch self {
        case .low: return "checkmark.circle.fill"
        case .medium: return "exclamationmark.circle.fill"
        case .high: return "exclamationmark.triangle.fill"
        case .emergency: return "xmark.octagon.fill"
        }
    }
}

// MARK: - 事件状态
enum EventStatus: String, Codable, CaseIterable {
    case inProgress = "in_progress"
    case completed = "completed"
    case exported = "exported"
    case archived = "archived"
    
    var displayName: String {
        switch self {
        case .inProgress: return "进行中"
        case .completed: return "已完成"
        case .exported: return "已导出"
        case .archived: return "已归档"
        }
    }
    
    var color: Color {
        switch self {
        case .inProgress: return DossierColors.statusInProgress
        case .completed: return DossierColors.statusCompleted
        case .exported: return DossierColors.statusExported
        case .archived: return DXYColors.textTertiary
        }
    }
}

// MARK: - 附件类型
enum AttachmentType: String, Codable {
    case image = "image"
    case report = "report"
    case audio = "audio"
    case video = "video"
}

// MARK: - 附件模型
struct Attachment: Identifiable, Codable {
    let id: String
    let type: AttachmentType
    let url: String
    let thumbnailUrl: String?
    let fileName: String?
    let fileSize: Int?
    let createdAt: Date
    let description: String?
    
    init(id: String = UUID().uuidString, type: AttachmentType, url: String, thumbnailUrl: String? = nil, fileName: String? = nil, fileSize: Int? = nil, createdAt: Date = Date(), description: String? = nil) {
        self.id = id
        self.type = type
        self.url = url
        self.thumbnailUrl = thumbnailUrl
        self.fileName = fileName
        self.fileSize = fileSize
        self.createdAt = createdAt
        self.description = description
    }
}

// MARK: - 消息角色
enum MessageRole: String, Codable {
    case user = "user"
    case assistant = "assistant"
    case system = "system"
}

// MARK: - 对话消息
struct DossierChatMessage: Identifiable, Codable {
    let id: String
    let role: MessageRole
    let content: String
    let timestamp: Date
    let attachments: [Attachment]?
    let isImportant: Bool
    
    init(id: String = UUID().uuidString, role: MessageRole, content: String, timestamp: Date = Date(), attachments: [Attachment]? = nil, isImportant: Bool = false) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.attachments = attachments
        self.isImportant = isImportant
    }
}

// MARK: - 会话记录
struct SessionRecord: Identifiable, Codable {
    let id: String
    let sessionId: String
    let startTime: Date
    let endTime: Date?
    let messages: [DossierChatMessage]
    let summary: String?
    
    init(id: String = UUID().uuidString, sessionId: String, startTime: Date = Date(), endTime: Date? = nil, messages: [DossierChatMessage] = [], summary: String? = nil) {
        self.id = id
        self.sessionId = sessionId
        self.startTime = startTime
        self.endTime = endTime
        self.messages = messages
        self.summary = summary
    }
}

// MARK: - 诊断结果
struct Diagnosis: Identifiable, Codable {
    let id: String
    let name: String
    let confidence: Double
    let description: String?
    
    init(id: String = UUID().uuidString, name: String, confidence: Double, description: String? = nil) {
        self.id = id
        self.name = name
        self.confidence = confidence
        self.description = description
    }
}

// MARK: - AI 分析结果
struct AIAnalysis: Codable {
    let chiefComplaint: String
    let symptoms: [String]
    let possibleDiagnosis: [Diagnosis]
    let recommendations: [String]
    let riskLevel: DossierRiskLevel
    let needOfflineVisit: Bool
    let visitUrgency: String?
    let analysisTime: Date
    
    init(chiefComplaint: String = "", symptoms: [String] = [], possibleDiagnosis: [Diagnosis] = [], recommendations: [String] = [], riskLevel: DossierRiskLevel = .low, needOfflineVisit: Bool = false, visitUrgency: String? = nil, analysisTime: Date = Date()) {
        self.chiefComplaint = chiefComplaint
        self.symptoms = symptoms
        self.possibleDiagnosis = possibleDiagnosis
        self.recommendations = recommendations
        self.riskLevel = riskLevel
        self.needOfflineVisit = needOfflineVisit
        self.visitUrgency = visitUrgency
        self.analysisTime = analysisTime
    }
}

// MARK: - 医疗事件
struct MedicalEvent: Identifiable, Codable, Hashable {
    static func == (lhs: MedicalEvent, rhs: MedicalEvent) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    let id: String
    var title: String
    let department: DepartmentType
    var status: EventStatus
    let createdAt: Date
    var updatedAt: Date
    var summary: String
    var riskLevel: DossierRiskLevel
    var sessions: [SessionRecord]
    var attachments: [Attachment]
    var aiAnalysis: AIAnalysis?
    var notes: String?
    var exportedAt: Date?
    
    init(
        id: String = UUID().uuidString,
        title: String,
        department: DepartmentType,
        status: EventStatus = .inProgress,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        summary: String = "",
        riskLevel: DossierRiskLevel = .low,
        sessions: [SessionRecord] = [],
        attachments: [Attachment] = [],
        aiAnalysis: AIAnalysis? = nil,
        notes: String? = nil,
        exportedAt: Date? = nil
    ) {
        self.id = id
        self.title = title
        self.department = department
        self.status = status
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.summary = summary
        self.riskLevel = riskLevel
        self.sessions = sessions
        self.attachments = attachments
        self.aiAnalysis = aiAnalysis
        self.notes = notes
        self.exportedAt = exportedAt
    }
    
    var photoCount: Int {
        attachments.filter { $0.type == .image }.count
    }
    
    var reportCount: Int {
        attachments.filter { $0.type == .report }.count
    }
    
    var dateRangeText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM-dd"
        let start = formatter.string(from: createdAt)
        let end = formatter.string(from: updatedAt)
        return start == end ? start : "\(start) ~ \(end)"
    }
}

// MARK: - 时间轴项目
struct TimelineItem: Identifiable {
    let id: String
    let date: Date
    let contents: [TimelineContent]
    
    init(id: String = UUID().uuidString, date: Date, contents: [TimelineContent]) {
        self.id = id
        self.date = date
        self.contents = contents
    }
}

// MARK: - 时间轴内容
struct TimelineContent: Identifiable {
    let id: String
    let type: TimelineContentType
    let message: DossierChatMessage?
    let attachment: Attachment?
    
    init(id: String = UUID().uuidString, type: TimelineContentType, message: DossierChatMessage? = nil, attachment: Attachment? = nil) {
        self.id = id
        self.type = type
        self.message = message
        self.attachment = attachment
    }
}

enum TimelineContentType {
    case userMessage
    case aiMessage
    case attachment
    case sessionStart
    case sessionEnd
}

// MARK: - 导出配置
struct ExportConfig {
    var exportScope: ExportScope = .currentEvent
    var startDate: Date = Date()
    var endDate: Date = Date()
    var selectedEventIds: [String] = []
    
    var includeDialogueSummary: Bool = true
    var includeAttachments: Bool = true
    var includeAIAnalysis: Bool = true
    var includeFullDialogue: Bool = false
    var includeNotes: Bool = false
    
    var includeName: Bool = true
    var includeGender: Bool = true
    var includeAge: Bool = true
    var includePhone: Bool = false
}

enum ExportScope: String, CaseIterable {
    case currentEvent = "current"
    case dateRange = "range"
    case multipleEvents = "multiple"
    
    var displayName: String {
        switch self {
        case .currentEvent: return "仅本次事件"
        case .dateRange: return "选择时间范围"
        case .multipleEvents: return "合并多个事件"
        }
    }
}

// MARK: - 用户信息（用于 PDF 导出）
struct ExportUserInfo {
    let name: String?
    let gender: String?
    let age: Int?
    let phone: String?
}

// MARK: - 筛选状态
enum EventFilter: String, CaseIterable {
    case all = "all"
    case inProgress = "in_progress"
    case exported = "exported"
    
    var displayName: String {
        switch self {
        case .all: return "全部"
        case .inProgress: return "进行中"
        case .exported: return "已导出"
        }
    }
}
