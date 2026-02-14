import Foundation

// MARK: - Virtual Doctor Models

/// 虚拟医生性格类型
enum PersonalityType: String, Codable, CaseIterable {
    case formal = "formal"
    case friendly = "friendly"
    case concise = "concise"
    case detailed = "detailed"

    var displayName: String {
        switch self {
        case .formal:
            return "专业严谨型"
        case .friendly:
            return "温和亲切型"
        case .concise:
            return "干练直接型"
        case .detailed:
            return "详细耐心型"
        }
    }

    var description: String {
        switch self {
        case .formal:
            return "用词严谨专业，遵循医学标准"
        case .friendly:
            return "像长辈一样温和，多用鼓励性语言"
        case .concise:
            return "直击问题要点，少用客套话"
        case .detailed:
            return "解释详细，说明原因，提供背景知识"
        }
    }
}

/// 虚拟医生性格配置
struct PersonalityConfig: Codable {
    let code: String
    let name: String
    let description: String
    let styleTags: [String]
    let temperature: Double
    let greetingTemplate: String

    enum CodingKeys: String, CodingKey {
        case code
        case name
        case description
        case styleTags = "style_tags"
        case temperature
        case greetingTemplate = "greeting_template"
    }
}

/// 虚拟医生列表响应
struct VirtualDoctorListResponse: Codable {
    let doctors: [VirtualDoctor]
}

/// 虚拟医生摘要
struct VirtualDoctor: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let title: String
    let departmentId: Int?
    let specialty: String?
    let intro: String?
    let personalityType: String?
    let greetingTemplate: String?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case title
        case departmentId = "department_id"
        case specialty
        case intro
        case personalityType = "personality_type"
        case greetingTemplate = "greeting_template"
    }

    // Hashable conformance
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: VirtualDoctor, rhs: VirtualDoctor) -> Bool {
        lhs.id == rhs.id
    }
}

/// 虚拟医生详情
struct VirtualDoctorDetail: Codable {
    let id: Int
    let name: String
    let title: String
    let departmentId: Int?
    let specialty: String?
    let intro: String?
    let personalityType: String?
    let personalityConfig: PersonalityConfig?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case title
        case departmentId = "department_id"
        case specialty
        case intro
        case personalityType = "personality_type"
        case personalityConfig = "personality_config"
    }
}
