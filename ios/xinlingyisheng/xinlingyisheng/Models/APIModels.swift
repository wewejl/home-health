import Foundation

struct UserModel: Codable, Identifiable {
    let id: Int
    let phone: String
    var nickname: String?
    var avatar_url: String?
    var gender: String?
    var birthday: String?
    var emergency_contact_name: String?
    var emergency_contact_phone: String?
    var emergency_contact_relation: String?
    var is_profile_completed: Bool
    let created_at: Date?
    var updated_at: Date?
    
    enum CodingKeys: String, CodingKey {
        case id, phone, nickname, avatar_url, gender, birthday
        case emergency_contact_name, emergency_contact_phone, emergency_contact_relation
        case is_profile_completed, created_at, updated_at
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        phone = try container.decode(String.self, forKey: .phone)
        nickname = try container.decodeIfPresent(String.self, forKey: .nickname)
        avatar_url = try container.decodeIfPresent(String.self, forKey: .avatar_url)
        gender = try container.decodeIfPresent(String.self, forKey: .gender)
        birthday = try container.decodeIfPresent(String.self, forKey: .birthday)
        emergency_contact_name = try container.decodeIfPresent(String.self, forKey: .emergency_contact_name)
        emergency_contact_phone = try container.decodeIfPresent(String.self, forKey: .emergency_contact_phone)
        emergency_contact_relation = try container.decodeIfPresent(String.self, forKey: .emergency_contact_relation)
        is_profile_completed = try container.decodeIfPresent(Bool.self, forKey: .is_profile_completed) ?? false
        
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let dateString = try container.decodeIfPresent(String.self, forKey: .created_at) {
            created_at = formatter.date(from: dateString)
        } else {
            created_at = nil
        }
        
        if let dateString = try container.decodeIfPresent(String.self, forKey: .updated_at) {
            updated_at = formatter.date(from: dateString)
        } else {
            updated_at = nil
        }
    }
    
    // MARK: - Computed Properties
    var displayGender: String {
        switch gender {
        case "male": return "男"
        case "female": return "女"
        case "other": return "其他"
        default: return "未设置"
        }
    }
    
    var maskedPhone: String {
        guard phone.count == 11 else { return phone }
        let start = phone.prefix(3)
        let end = phone.suffix(4)
        return "\(start)****\(end)"
    }
}

struct DepartmentModel: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let description: String?
    let icon: String?
    let sort_order: Int
    
    static func == (lhs: DepartmentModel, rhs: DepartmentModel) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct DoctorModel: Codable, Identifiable {
    let id: Int
    let name: String
    let title: String?
    let department_id: Int
    let hospital: String?
    let specialty: String?
    let intro: String?
    let avatar_url: String?
    let rating: Double
    let monthly_answers: Int
    let avg_response_time: String
    let can_prescribe: Bool
    let is_top_hospital: Bool
    let is_ai: Bool?
    let is_active: Bool?
    
    var isAIDoctor: Bool { is_ai ?? true }
}

struct FeedbackRequest: Codable {
    let message_id: Int?
    let rating: Int?
    let feedback_type: String?
    let feedback_text: String?
}

struct FeedbackResponse: Codable, Identifiable {
    let id: Int
    let session_id: String
    let message_id: Int?
    let user_id: Int
    let rating: Int?
    let feedback_type: String?
    let feedback_text: String?
    let status: String
    let created_at: String?
}

struct SessionModel: Codable, Identifiable, Hashable {
    let session_id: String
    let doctor_id: Int?
    let doctor_name: String?
    let agent_type: String?
    let last_message: String?
    let status: String
    let created_at: Date
    let updated_at: Date
    
    var id: String { session_id }
    
    static func == (lhs: SessionModel, rhs: SessionModel) -> Bool {
        lhs.session_id == rhs.session_id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(session_id)
    }
    
    enum CodingKeys: String, CodingKey {
        case session_id, doctor_id, doctor_name, agent_type, last_message, status, created_at, updated_at
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        session_id = try container.decode(String.self, forKey: .session_id)
        doctor_id = try container.decodeIfPresent(Int.self, forKey: .doctor_id)
        doctor_name = try container.decodeIfPresent(String.self, forKey: .doctor_name)
        agent_type = try container.decodeIfPresent(String.self, forKey: .agent_type)
        last_message = try container.decodeIfPresent(String.self, forKey: .last_message)
        status = try container.decode(String.self, forKey: .status)
        
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let dateString = try container.decodeIfPresent(String.self, forKey: .created_at),
           let date = formatter.date(from: dateString) {
            created_at = date
        } else {
            created_at = Date()
        }
        
        if let dateString = try container.decodeIfPresent(String.self, forKey: .updated_at),
           let date = formatter.date(from: dateString) {
            updated_at = date
        } else {
            updated_at = Date()
        }
    }
}

struct MessageModel: Codable, Identifiable {
    let id: Int
    let session_id: String
    let sender: String
    let content: String
    let attachment_url: String?
    let message_type: String?
    let created_at: Date
    
    var isFromUser: Bool { sender == "user" }
    
    enum CodingKeys: String, CodingKey {
        case id, session_id, sender, content, attachment_url, message_type, created_at
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        session_id = try container.decode(String.self, forKey: .session_id)
        sender = try container.decode(String.self, forKey: .sender)
        content = try container.decode(String.self, forKey: .content)
        attachment_url = try container.decodeIfPresent(String.self, forKey: .attachment_url)
        message_type = try container.decodeIfPresent(String.self, forKey: .message_type)
        
        if let dateString = try container.decodeIfPresent(String.self, forKey: .created_at) {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            created_at = formatter.date(from: dateString) ?? Date()
        } else {
            created_at = Date()
        }
    }
}

// MARK: - Disease Models
struct DiseaseListModel: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let department_id: Int
    let department_name: String?
    let recommended_department: String?
    let is_hot: Bool
    let view_count: Int
    
    static func == (lhs: DiseaseListModel, rhs: DiseaseListModel) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct DiseaseDetailModel: Codable, Identifiable {
    let id: Int
    let name: String
    let pinyin: String?
    let department_id: Int
    let department_name: String?
    let recommended_department: String?
    let overview: String?
    let symptoms: String?
    let causes: String?
    let diagnosis: String?
    let treatment: String?
    let prevention: String?
    let care: String?
    let author_name: String?
    let author_title: String?
    let author_avatar: String?
    let reviewer_info: String?
    let is_hot: Bool
    let view_count: Int
    let updated_at: String?
}

struct DepartmentWithDiseasesModel: Codable, Identifiable {
    let id: Int
    let name: String
    let icon: String?
    let disease_count: Int
    let hot_diseases: [DiseaseListModel]
}

struct DiseaseSearchResponse: Codable {
    let total: Int
    let items: [DiseaseListModel]
}

// MARK: - Drug Models
struct DrugListModel: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let common_brands: String?
    let is_hot: Bool
    let view_count: Int
    
    static func == (lhs: DrugListModel, rhs: DrugListModel) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct DrugCategoryWithDrugsModel: Codable, Identifiable {
    let id: Int
    let name: String
    let icon: String?
    let display_type: String
    let drugs: [DrugListModel]
}

struct DrugDetailModel: Codable, Identifiable {
    let id: Int
    let name: String
    let common_brands: String?
    let aliases: String?
    
    let pregnancy_level: String?
    let pregnancy_desc: String?
    let lactation_level: String?
    let lactation_desc: String?
    let children_usable: Bool
    let children_desc: String?
    
    let indications: String?
    let contraindications: String?
    let dosage: String?
    let side_effects: String?
    let precautions: String?
    let interactions: String?
    let storage: String?
    
    let author_name: String?
    let author_title: String?
    let author_avatar: String?
    let reviewer_info: String?
    
    let is_hot: Bool
    let view_count: Int
    let updated_at: String?
}

struct DrugSearchResponse: Codable {
    let total: Int
    let items: [DrugListModel]
}
