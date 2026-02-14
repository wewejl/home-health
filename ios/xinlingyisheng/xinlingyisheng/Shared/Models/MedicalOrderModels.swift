import SwiftUI

// MARK: - 医嘱执行监督 Models

// MARK: - Enums

enum OrderType: String, Codable {
    case medication = "medication"    // 用药任务
    case monitoring = "monitoring"    // 监测任务
    case behavior = "behavior"        // 行为任务
    case followup = "followup"        // 复诊任务

    var displayName: String {
        switch self {
        case .medication: return "用药"
        case .monitoring: return "监测"
        case .behavior: return "行为"
        case .followup: return "复诊"
        }
    }

    var iconName: String {
        switch self {
        case .medication: return "pills"
        case .monitoring: return "heart.text.square"
        case .behavior: return "figure.walk"
        case .followup: return "calendar"
        }
    }

    var color: Color {
        switch self {
        case .medication: return .blue
        case .monitoring: return .orange
        case .behavior: return .green
        case .followup: return .purple
        }
    }
}

enum ScheduleType: String, Codable {
    case once = "once"               // 一次性
    case daily = "daily"             // 每日
    case weekly = "weekly"           // 每周
    case custom = "custom"           // 自定义

    var displayName: String {
        switch self {
        case .once: return "一次性"
        case .daily: return "每日"
        case .weekly: return "每周"
        case .custom: return "自定义"
        }
    }
}

enum OrderStatus: String, Codable {
    case draft = "draft"             // 草稿
    case active = "active"           // 进行中
    case completed = "completed"     // 已完成
    case stopped = "stopped"         // 已停用

    var displayName: String {
        switch self {
        case .draft: return "草稿"
        case .active: return "进行中"
        case .completed: return "已完成"
        case .stopped: return "已停用"
        }
    }

    var colorName: String {
        switch self {
        case .draft: return "gray"
        case .active: return "blue"
        case .completed: return "green"
        case .stopped: return "red"
        }
    }
}

enum TaskStatus: String, Codable {
    case pending = "pending"         // 待完成
    case completed = "completed"     // 已完成
    case overdue = "overdue"         // 已超时
    case skipped = "skipped"         // 已跳过

    var displayName: String {
        switch self {
        case .pending: return "待完成"
        case .completed: return "已完成"
        case .overdue: return "已超时"
        case .skipped: return "已跳过"
        }
    }

    var colorName: String {
        switch self {
        case .pending: return "gray"
        case .completed: return "green"
        case .overdue: return "red"
        case .skipped: return "orange"
        }
    }

    var iconName: String {
        switch self {
        case .pending: return "circle"
        case .completed: return "checkmark.circle.fill"
        case .overdue: return "exclamationmark.triangle.fill"
        case .skipped: return "minus.circle.fill"
        }
    }
}

enum CompletionType: String, Codable {
    case check = "check"              // 打卡确认
    case photo = "photo"              // 照片证明
    case value = "value"              // 数值录入
    case medication = "medication"    // 用药记录

    var displayName: String {
        switch self {
        case .check: return "打卡"
        case .photo: return "拍照"
        case .value: return "记录数值"
        case .medication: return "用药记录"
        }
    }
}

enum NotificationLevel: String, Codable {
    case all = "all"                 // 全部通知
    case abnormal = "abnormal"       // 仅异常
    case summary = "summary"         // 仅摘要
    case none = "none"               // 不通知

    var displayName: String {
        switch self {
        case .all: return "全部通知"
        case .abnormal: return "仅异常"
        case .summary: return "仅摘要"
        case .none: return "不通知"
        }
    }
}

// MARK: - Request Models

struct MedicalOrderCreateRequest: Codable {
    let order_type: String
    let title: String
    var description: String?
    let schedule_type: String
    let start_date: String
    var end_date: String?
    var frequency: String?
    var reminder_times: [String]?
    var ai_generated: Bool?
    var ai_session_id: String?
}

struct ActivateOrderRequest: Codable {
    let confirm: Bool
}

struct CompletionRecordRequest: Encodable {
    let task_instance_id: Int
    let completion_type: String
    var value: [String: String]?
    var photo_url: String?
    var notes: String?
}

struct MedicalOrderUpdateRequest: Codable {
    var title: String?
    var description: String?
    var end_date: String?
    var frequency: String?
    var reminder_times: [String]?
}

struct AbnormalRecord: Codable, Identifiable {
    let id: Int
    let patient_id: Int
    let record_type: String
    let value: String
    let threshold_min: String?
    let threshold_max: String?
    let recorded_at: String
    let is_acknowledged: Bool
}

struct FamilyBondCreateRequest: Codable {
    let patient_id: Int
    let family_member_phone: String
    let relationship_type: String
    let notification_level: String
}

// MARK: - Response Models

struct MedicalOrder: Codable, Identifiable {
    let id: Int
    let patient_id: Int
    var doctor_id: Int?
    let order_type: String
    let title: String
    var description: String?
    let schedule_type: String
    let start_date: String
    var end_date: String?
    var frequency: String?
    let reminder_times: [String]
    let ai_generated: Bool
    var ai_session_id: String?
    let status: String
    let created_at: String
    let updated_at: String

    var orderTypeEnum: OrderType? { OrderType(rawValue: order_type) }
    var scheduleTypeEnum: ScheduleType? { ScheduleType(rawValue: schedule_type) }
    var statusEnum: OrderStatus? { OrderStatus(rawValue: status) }

    private enum CodingKeys: String, CodingKey {
        case id, patient_id, doctor_id, order_type, title, description
        case schedule_type, start_date, end_date, frequency, reminder_times
        case ai_generated, ai_session_id, status, created_at, updated_at
    }
}

struct TaskInstance: Codable, Identifiable {
    let id: Int
    let order_id: Int
    let patient_id: Int
    let scheduled_date: String
    let scheduled_time: String
    let status: String
    var completed_at: String?
    var completion_notes: String?
    var order_title: String?
    var order_type: String?

    var statusEnum: TaskStatus? { TaskStatus(rawValue: status) }
    var scheduledDateTime: Date? {
        let formatter = ISO8601DateFormatter()
        let dateTimeString = "\(scheduled_date)T\(scheduled_time)"
        return formatter.date(from: dateTimeString)
    }

    var isPending: Bool { status == "pending" }
    var isCompleted: Bool { status == "completed" }
    var isOverdue: Bool { status == "overdue" }
}

struct CompletionRecord: Codable, Identifiable {
    let id: Int
    let task_instance_id: Int
    let completed_by: Int
    let completion_type: String
    var value: [String: String]?
    var photo_url: String?
    var notes: String?
    let created_at: String

    var completionTypeEnum: CompletionType? { CompletionType(rawValue: completion_type) }
}

struct ComplianceSummary: Codable {
    let date: String?
    let total: Int
    let completed: Int
    let overdue: Int
    let pending: Int
    let rate: Double

    var ratePercent: Int { Int(rate * 100) }
}

struct TaskListResponse: Codable {
    let date: String
    let pending: [TaskInstance]
    let completed: [TaskInstance]
    let overdue: [TaskInstance]
    let summary: ComplianceSummary
}

struct WeeklyComplianceResponse: Codable {
    let daily_rates: [Double]
    let average_rate: Double
    let dates: [String]

    var averagePercent: Int { Int(average_rate * 100) }
}

struct Alert: Codable, Identifiable {
    let id: Int
    let patient_id: Int
    let alert_type: String
    let severity: String
    let title: String
    let message: String
    var task_instance_id: Int?
    var completion_record_id: Int?
    var value_data: [String: String]?
    let is_acknowledged: Bool
    var acknowledged_at: String?
    let created_at: String

    var severityColor: String {
        switch severity {
        case "critical": return "red"
        case "warning": return "orange"
        case "info": return "blue"
        default: return "gray"
        }
    }

    var iconName: String {
        switch alert_type {
        case "glucose_low": return "exclamationmark.arrow.triangle.down"
        case "glucose_high": return "exclamationmark.arrow.triangle.up"
        case "bp_high": return "heart.fill"
        case "temp_high": return "thermometer"
        case "task_overdue": return "clock.fill"
        case "compliance_low": return "chart.bar.fill"
        default: return "bell.fill"
        }
    }
}

struct AcknowledgeAlertResponse: Codable {
    let success: Bool
    let message: String
}

struct FamilyBond: Codable, Identifiable {
    let id: Int
    let patient_id: Int
    let family_member_id: Int
    let relationship_type: String
    let notification_level: String
    var family_member_name: String?
    var family_member_phone: String?
    var patient_name: String?

    var notificationLevelEnum: NotificationLevel? { NotificationLevel(rawValue: notification_level) }
}

// MARK: - Grouped Tasks for UI Display

struct GroupedTasks {
    var pending: [TaskInstance] = []
    var completed: [TaskInstance] = []
    var overdue: [TaskInstance] = []

    var totalCount: Int { pending.count + completed.count + overdue.count }
    var completedCount: Int { completed.count }
    var rate: Double {
        totalCount > 0 ? Double(completedCount) / Double(totalCount) : 0
    }
}
