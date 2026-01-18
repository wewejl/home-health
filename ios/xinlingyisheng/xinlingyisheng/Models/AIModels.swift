import Foundation

// MARK: - AI Summary Models

struct AISummaryRequest: Encodable {
    let event_id: String
    let force_regenerate: Bool
    
    init(eventId: String, forceRegenerate: Bool = false) {
        self.event_id = eventId
        self.force_regenerate = forceRegenerate
    }
}

struct AISummaryResponse: Decodable {
    let event_id: String
    let summary: String?
    let key_points: [String]?
    let symptoms: [String]?
    let symptom_details: [String: SymptomDetail]?
    let possible_diagnosis: [String]?
    let risk_level: String?
    let risk_warning: String?
    let recommendations: [String]?
    let follow_up_reminders: [String]?
    let timeline: [TimelineEvent]?
    let confidence: Double?
    let message: String?
    
    struct SymptomDetail: Decodable {
        let duration: String?
        let severity: String?
        let location: String?
    }
    
    struct TimelineEvent: Decodable {
        let time: String?
        let event: String?
        let type: String?
    }
}

// MARK: - Relation Analysis Models

struct AnalyzeRelationRequest: Encodable {
    let event_id_a: String
    let event_id_b: String
}

struct AnalyzeRelationResponse: Decodable {
    let is_related: Bool
    let relation_type: String?
    let confidence: Double?
    let reasoning: String?
    let should_merge: Bool?
    let merge_suggestion: String?
}

enum RelationType: String, Codable {
    case sameCondition = "same_condition"
    case followUp = "follow_up"
    case complication = "complication"
    case unrelated = "unrelated"
    
    var displayName: String {
        switch self {
        case .sameCondition: return "同一病情"
        case .followUp: return "随访/复诊"
        case .complication: return "并发症"
        case .unrelated: return "不相关"
        }
    }
}

// MARK: - Smart Aggregate Models

struct SmartAggregateRequest: Encodable {
    let session_id: String
    let session_type: String
    let department: String?
    let chief_complaint: String?
}

struct SmartAggregateResponse: Decodable {
    let action: String
    let target_event_id: String?
    let confidence: Double?
    let reasoning: String?
    let should_merge: Bool?
}

enum AggregateAction: String {
    case addToExisting = "add_to_existing"
    case createNew = "create_new"
}

// MARK: - Find Related Events Models

struct FindRelatedRequest: Encodable {
    let event_id: String
    let max_results: Int?
    
    init(eventId: String, maxResults: Int = 5) {
        self.event_id = eventId
        self.max_results = maxResults
    }
}

struct FindRelatedResponse: Decodable {
    let target_event_id: String
    let related_events: [RelatedEvent]
    
    struct RelatedEvent: Decodable, Identifiable {
        var id: String { event_id }
        let event_id: String
        let relation_type: String?
        let confidence: Double?
        let reasoning: String?
    }
}

// MARK: - Merge Events Models

struct MergeEventsRequest: Encodable {
    let event_ids: [String]
    let new_title: String?
}

struct MergeEventsResponse: Decodable {
    let merged_event_id: String
    let merged_title: String?
    let summary: String?
    let disease_progression: String?
    let current_status: String?
    let overall_risk_level: String?
    let recommendations: [String]?
    let message: String?
}

// MARK: - Transcription Models

struct TranscribeRequest: Encodable {
    let audio_url: String?
    let audio_base64: String?
    let language: String
    let extract_symptoms: Bool
    
    init(audioUrl: String? = nil, audioBase64: String? = nil, language: String = "zh", extractSymptoms: Bool = true) {
        self.audio_url = audioUrl
        self.audio_base64 = audioBase64
        self.language = language
        self.extract_symptoms = extractSymptoms
    }
}

struct TranscribeResponse: Decodable {
    let task_id: String
    let status: String
    let text: String?
    let duration: Double?
    let confidence: Double?
    let segments: [TranscriptionSegment]?
    let extracted_symptoms: [String]?
    let language: String?
    let error_message: String?
    
    struct TranscriptionSegment: Decodable {
        let start_time: Double?
        let end_time: Double?
        let text: String?
        let confidence: Double?
    }
}

enum TranscriptionStatus: String {
    case pending = "pending"
    case processing = "processing"
    case completed = "completed"
    case failed = "failed"
    
    var displayName: String {
        switch self {
        case .pending: return "等待处理"
        case .processing: return "处理中"
        case .completed: return "已完成"
        case .failed: return "失败"
        }
    }
}

struct TranscribeStatusResponse: Decodable {
    let task_id: String
    let status: String
    let text: String?
    let error_message: String?
}
