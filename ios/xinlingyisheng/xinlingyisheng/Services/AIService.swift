import Foundation

class AIService {
    static let shared = AIService()
    private init() {}
    
    // MARK: - Private Helper
    
    private func makeRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil
    ) async throws -> T {
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            print("[AI] ❌ Invalid URL: \(APIConfig.baseURL + endpoint)")
            throw APIError.invalidURL
        }
        
        guard let token = AuthManager.shared.token else {
            print("[AI] ❌ No token available")
            throw APIError.unauthorized
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        if let body = body {
            request.httpBody = body
            if let bodyString = String(data: body, encoding: .utf8) {
                print("[AI] 📤 \(method) \(endpoint)")
                print("[AI] Body: \(bodyString)")
            }
        } else {
            print("[AI] 📤 \(method) \(endpoint)")
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("[AI] 📥 Status: \(httpResponse.statusCode)")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("[AI] Response: \(responseString.prefix(500))")
                }
            }
            
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 {
                    print("[AI] ❌ 401 Unauthorized")
                    DispatchQueue.main.async {
                        NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                    }
                    throw APIError.unauthorized
                }
                
                if httpResponse.statusCode >= 400 {
                    if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                        throw APIError.serverError(errorResponse.detail)
                    }
                    throw APIError.serverError("请求失败")
                }
            }
            
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
        } catch let error as APIError {
            print("[AI] ❌ APIError: \(error.errorDescription ?? "Unknown")")
            throw error
        } catch let error as DecodingError {
            print("[AI] ❌ DecodingError: \(error)")
            throw APIError.decodingError(error)
        } catch {
            print("[AI] ❌ NetworkError: \(error.localizedDescription)")
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - AI Summary APIs
    
    /// 生成 AI 摘要
    func generateSummary(eventId: String, forceRegenerate: Bool = false) async throws -> AISummaryResponse {
        let request = AISummaryRequest(eventId: eventId, forceRegenerate: forceRegenerate)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/summary", method: "POST", body: data)
    }
    
    /// 获取已生成的 AI 摘要
    func getSummary(eventId: String) async throws -> AISummaryResponse {
        return try await makeRequest(endpoint: "/ai/summary/\(eventId)")
    }
    
    // MARK: - Smart Aggregation APIs
    
    /// 分析两个事件的关联性
    func analyzeRelation(eventIdA: String, eventIdB: String) async throws -> AnalyzeRelationResponse {
        let request = AnalyzeRelationRequest(event_id_a: eventIdA, event_id_b: eventIdB)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/analyze-relation", method: "POST", body: data)
    }
    
    /// 智能聚合分析 - 判断新会话应归入哪个事件
    func smartAggregate(
        sessionId: String,
        sessionType: String,
        department: String? = nil,
        chiefComplaint: String? = nil
    ) async throws -> SmartAggregateResponse {
        // department 改为必填，使用后端格式的值
        let dept: String
        if let department = department {
            // 如果传入了前端枚举值，转换为后端值
            if let deptType = DepartmentType(rawValue: department) {
                dept = DepartmentMapping.toBackend(deptType)
            } else {
                dept = department
            }
        } else {
            // 默认值使用后端格式
            dept = "general"
        }

        let request = SmartAggregateRequest(
            session_id: sessionId,
            session_type: sessionType,
            department: dept,  // ✅ 确保传递后端格式的值
            chief_complaint: chiefComplaint
        )
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/smart-aggregate", method: "POST", body: data)
    }
    
    /// 查找相关事件
    func findRelatedEvents(eventId: String, maxResults: Int = 5) async throws -> FindRelatedResponse {
        let request = FindRelatedRequest(eventId: eventId, maxResults: maxResults)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/find-related", method: "POST", body: data)
    }
    
    /// 合并多个事件
    func mergeEvents(eventIds: [String], newTitle: String? = nil) async throws -> MergeEventsResponse {
        let request = MergeEventsRequest(event_ids: eventIds, new_title: newTitle)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/merge-events", method: "POST", body: data)
    }
    
    // MARK: - Transcription APIs
    
    /// 语音转写（URL方式）
    func transcribeAudioURL(audioUrl: String, language: String = "zh", extractSymptoms: Bool = true) async throws -> TranscribeResponse {
        let request = TranscribeRequest(audioUrl: audioUrl, language: language, extractSymptoms: extractSymptoms)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/transcribe", method: "POST", body: data)
    }
    
    /// 语音转写（Base64方式）
    func transcribeAudioBase64(audioBase64: String, language: String = "zh", extractSymptoms: Bool = true) async throws -> TranscribeResponse {
        let request = TranscribeRequest(audioBase64: audioBase64, language: language, extractSymptoms: extractSymptoms)
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "/ai/transcribe", method: "POST", body: data)
    }
    
    /// 上传音频文件进行转写
    func transcribeAudioFile(audioData: Data, fileName: String, language: String = "zh", extractSymptoms: Bool = true) async throws -> TranscribeResponse {
        let endpoint = "/ai/transcribe/upload"
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        guard let token = AuthManager.shared.token else {
            throw APIError.unauthorized
        }
        
        let boundary = UUID().uuidString
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // 添加音频文件
        let mimeType = getMimeType(for: fileName)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)
        
        // 添加语言参数
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"language\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(language)\r\n".data(using: .utf8)!)
        
        // 添加提取症状参数
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"extract_symptoms\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(extractSymptoms)\r\n".data(using: .utf8)!)
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body
        
        print("[AI] 📤 Upload audio to \(endpoint)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse {
            print("[AI] 📥 Upload Status: \(httpResponse.statusCode)")
            
            if httpResponse.statusCode == 401 {
                DispatchQueue.main.async {
                    NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                }
                throw APIError.unauthorized
            }
            
            if httpResponse.statusCode >= 400 {
                if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                    throw APIError.serverError(errorResponse.detail)
                }
                throw APIError.serverError("上传失败")
            }
        }
        
        return try JSONDecoder().decode(TranscribeResponse.self, from: data)
    }
    
    /// 获取转写任务状态
    func getTranscriptionStatus(taskId: String) async throws -> TranscribeStatusResponse {
        return try await makeRequest(endpoint: "/ai/transcribe/\(taskId)")
    }
    
    // MARK: - Helper Methods
    
    private func getMimeType(for fileName: String) -> String {
        let ext = (fileName as NSString).pathExtension.lowercased()
        switch ext {
        case "mp3": return "audio/mpeg"
        case "wav": return "audio/wav"
        case "m4a": return "audio/mp4"
        case "aac": return "audio/aac"
        case "ogg": return "audio/ogg"
        case "flac": return "audio/flac"
        case "webm": return "audio/webm"
        default: return "audio/mpeg"
        }
    }
}
