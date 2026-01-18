import Foundation

// MARK: - API Response Models
struct MedicalEventListResponse: Decodable {
    let events: [MedicalEventDTO]
    let total: Int
    let page: Int
    let page_size: Int
}

struct MedicalEventDTO: Decodable, Identifiable {
    let id: Int
    let title: String
    let department: String
    let agent_type: String
    let status: String
    let risk_level: String
    let start_time: Date
    let end_time: Date?
    let summary: String?
    let chief_complaint: String?
    let attachment_count: Int
    let session_count: Int
    let created_at: Date
    let updated_at: Date
    
    // Identifiable conformance - convert Int to String
    var idString: String {
        String(id)
    }
}

struct MedicalEventDetailDTO: Decodable {
    let id: Int
    let title: String
    let department: String
    let agent_type: String
    let status: String
    let risk_level: String
    let start_time: Date
    let end_time: Date?
    let summary: String?
    let chief_complaint: String?
    let ai_analysis: AIAnalysisDTO?
    let sessions: [SessionRecordDTO]
    let attachments: [AttachmentDTO]
    let notes: [NoteDTO]
    let attachment_count: Int
    let session_count: Int
    let export_count: Int
    let created_at: Date
    let updated_at: Date
}

struct AIAnalysisDTO: Decodable {
    let symptoms: [String]?
    let possible_diagnosis: [String]?
    let recommendations: [String]?
    let follow_up_reminders: [String]?
    let timeline: [TimelineEventDTO]?
}

struct TimelineEventDTO: Decodable {
    let time: String
    let event: String
    let type: String?
}

struct SessionRecordDTO: Decodable {
    let session_id: String
    let session_type: String
    let timestamp: String
    let summary: String?
}

struct AttachmentDTO: Decodable, Identifiable {
    let id: Int
    let type: String
    let url: String
    let thumbnail_url: String?
    let filename: String?
    let file_size: Int?
    let mime_type: String?
    let description: String?
    let is_important: Bool
    let upload_time: Date
}

struct NoteDTO: Decodable, Identifiable {
    let id: Int
    let content: String
    let is_important: Bool
    let created_at: Date
    let updated_at: Date
}

struct AggregateSessionResponse: Decodable {
    let event_id: String
    let message: String
    let is_new_event: Bool
    
    enum CodingKeys: String, CodingKey {
        case event_id
        case message
        case is_new_event
    }
}

// MARK: - MedicalEventAPIService
class MedicalEventAPIService {
    static let shared = MedicalEventAPIService()
    private init() {}
    
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
    
    // MARK: - Fetch Events List
    func fetchEvents(
        page: Int = 1,
        pageSize: Int = 20,
        status: String? = nil,
        department: String? = nil
    ) async throws -> MedicalEventListResponse {
        var endpoint = APIConfig.Endpoints.medicalEvents + "?page=\(page)&page_size=\(pageSize)"
        if let status = status {
            endpoint += "&status=\(status)"
        }
        if let department = department {
            endpoint += "&department=\(department.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? department)"
        }
        
        return try await makeRequest(endpoint: endpoint, requiresAuth: true)
    }
    
    // MARK: - Fetch Event Detail
    func fetchEventDetail(eventId: String) async throws -> MedicalEventDetailDTO {
        let endpoint = APIConfig.Endpoints.medicalEventDetail(eventId: eventId)
        return try await makeRequest(endpoint: endpoint, requiresAuth: true)
    }
    
    // MARK: - Aggregate Session to Medical Event
    func aggregateSession(
        sessionId: String,
        sessionType: String
    ) async throws -> AggregateSessionResponse {
        let endpoint = APIConfig.Endpoints.medicalEvents + "/aggregate"
        
        let requestBody: [String: Any] = [
            "session_id": sessionId,
            "session_type": sessionType
        ]
        
        let jsonData = try JSONSerialization.data(withJSONObject: requestBody)
        
        return try await makeRequest(
            endpoint: endpoint,
            method: "POST",
            body: jsonData,
            requiresAuth: true
        )
    }
    
    // MARK: - Private Request Helper
    private func makeRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        requiresAuth: Bool = false
    ) async throws -> T {
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            guard let token = AuthManager.shared.token else {
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        print("[MedicalEventAPI] 📤 \(method) \(endpoint)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse {
            print("[MedicalEventAPI] 📥 Status: \(httpResponse.statusCode)")
            
            if httpResponse.statusCode == 401 {
                DispatchQueue.main.async {
                    NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                }
                throw APIError.unauthorized
            }
            
            if httpResponse.statusCode >= 400 {
                if let responseString = String(data: data, encoding: .utf8) {
                    print("[MedicalEventAPI] ❌ Error: \(responseString)")
                }
                throw APIError.serverError("请求失败: \(httpResponse.statusCode)")
            }
        }
        
        return try decoder.decode(T.self, from: data)
    }
}

// MARK: - DTO to Model Conversion
extension MedicalEventDTO {
    func toMedicalEvent() -> MedicalEvent {
        MedicalEvent(
            id: String(id),
            title: title,
            department: DepartmentType(rawValue: agent_type) ?? .general,
            status: EventStatus(rawValue: status) ?? .inProgress,
            createdAt: created_at,
            updatedAt: updated_at,
            summary: summary ?? "",
            riskLevel: DossierRiskLevel(rawValue: risk_level) ?? .low,
            sessions: [],
            attachments: [],
            aiAnalysis: nil,
            notes: nil,
            exportedAt: nil
        )
    }
}

extension MedicalEventDetailDTO {
    func toMedicalEvent() -> MedicalEvent {
        let mappedSessions = sessions.map { dto in
            SessionRecord(
                sessionId: dto.session_id,
                startTime: ISO8601DateFormatter().date(from: dto.timestamp) ?? Date(),
                endTime: nil,
                messages: [],
                summary: dto.summary
            )
        }
        
        let mappedAttachments = attachments.map { dto in
            Attachment(
                id: String(dto.id),
                type: AttachmentType(rawValue: dto.type) ?? .image,
                url: dto.url,
                thumbnailUrl: dto.thumbnail_url,
                fileName: dto.filename,
                fileSize: dto.file_size,
                createdAt: dto.upload_time
            )
        }
        
        var mappedAnalysis: AIAnalysis? = nil
        if let analysis = ai_analysis {
            let diagnoses = (analysis.possible_diagnosis ?? []).enumerated().map { index, name in
                Diagnosis(name: name, confidence: Double(100 - index * 10) / 100.0, description: nil)
            }
            
            mappedAnalysis = AIAnalysis(
                chiefComplaint: chief_complaint ?? "",
                symptoms: analysis.symptoms ?? [],
                possibleDiagnosis: diagnoses,
                recommendations: analysis.recommendations ?? [],
                riskLevel: DossierRiskLevel(rawValue: risk_level) ?? .low,
                needOfflineVisit: false,
                visitUrgency: analysis.follow_up_reminders?.first
            )
        }
        
        return MedicalEvent(
            id: String(id),
            title: title,
            department: DepartmentType(rawValue: agent_type) ?? .general,
            status: EventStatus(rawValue: status) ?? .inProgress,
            createdAt: created_at,
            updatedAt: updated_at,
            summary: summary ?? "",
            riskLevel: DossierRiskLevel(rawValue: risk_level) ?? .low,
            sessions: mappedSessions,
            attachments: mappedAttachments,
            aiAnalysis: mappedAnalysis,
            notes: notes.first?.content,
            exportedAt: nil
        )
    }
}
