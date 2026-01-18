import Foundation

// MARK: - Unified Chat API Extension
extension APIService {
    
    // MARK: - 创建会话（支持智能体类型）
    func createUnifiedSession(doctorId: Int? = nil, agentType: AgentType? = nil) async throws -> UnifiedSessionResponse {
        let endpoint = APIConfig.Endpoints.sessions
        
        var bodyDict: [String: Any] = [:]
        if let doctorId = doctorId {
            bodyDict["doctor_id"] = doctorId
        }
        if let agentType = agentType {
            bodyDict["agent_type"] = agentType.rawValue
        }
        
        let data = try JSONSerialization.data(withJSONObject: bodyDict)
        return try await makeUnifiedRequest(endpoint: endpoint, method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - 发送消息（支持附件和动作）- 非流式
    func sendUnifiedMessage(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async throws -> UnifiedSendMessageResponse {
        let endpoint = APIConfig.Endpoints.messages(sessionId: sessionId)
        
        var bodyDict: [String: Any] = [
            "content": content,
            "action": action.rawValue
        ]
        
        if !attachments.isEmpty {
            let attachmentsData = attachments.map { att -> [String: Any] in
                var dict: [String: Any] = ["type": att.type]
                if let url = att.url { dict["url"] = url }
                if let base64 = att.base64 { dict["base64"] = base64 }
                return dict
            }
            bodyDict["attachments"] = attachmentsData
        }
        
        let data = try JSONSerialization.data(withJSONObject: bodyDict)
        return try await makeUnifiedRequest(endpoint: endpoint, method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - 发送消息（支持附件和动作）- 流式
    func sendUnifiedMessageStreaming(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (UnifiedMessageResponse) -> Void,
        onError: @escaping (Error) -> Void,
        isRetry: Bool = false
    ) async {
        let endpoint = APIConfig.Endpoints.messages(sessionId: sessionId)
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            onError(APIError.invalidURL)
            return
        }
        
        guard let token = AuthManager.shared.token else {
            onError(APIError.unauthorized)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        var bodyDict: [String: Any] = [
            "content": content,
            "action": action.rawValue
        ]
        
        if !attachments.isEmpty {
            let attachmentsData = attachments.map { att -> [String: Any] in
                var dict: [String: Any] = ["type": att.type]
                if let url = att.url { dict["url"] = url }
                if let base64 = att.base64 { dict["base64"] = base64 }
                return dict
            }
            bodyDict["attachments"] = attachmentsData
        }
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: bodyDict)
        } catch {
            onError(APIError.networkError(error))
            return
        }
        
        print("[API] 📤 SSE POST \(endpoint)\(isRetry ? " (重试)" : "")")
        
        do {
            let (bytes, response) = try await URLSession.shared.bytes(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                onError(APIError.serverError("无效的响应"))
                return
            }
            
            print("[API] 📥 SSE Status: \(httpResponse.statusCode)")
            
            if httpResponse.statusCode == 401 {
                // 如果是第一次尝试,尝试刷新token并重试
                if !isRetry {
                    print("[API] 🔄 Token过期,尝试刷新...")
                    do {
                        try await AuthManager.shared.refreshTokenIfNeeded()
                        print("[API] ✅ Token刷新成功,重试发送消息...")
                        // 重试发送
                        await sendUnifiedMessageStreaming(
                            sessionId: sessionId,
                            content: content,
                            attachments: attachments,
                            action: action,
                            onChunk: onChunk,
                            onComplete: onComplete,
                            onError: onError,
                            isRetry: true
                        )
                        return
                    } catch {
                        print("[API] ❌ Token刷新失败: \(error)")
                        DispatchQueue.main.async {
                            NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                        }
                        onError(APIError.unauthorized)
                        return
                    }
                } else {
                    // 重试后仍然401,放弃
                    DispatchQueue.main.async {
                        NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                    }
                    onError(APIError.unauthorized)
                    return
                }
            }
            
            if httpResponse.statusCode >= 400 {
                onError(APIError.serverError("请求失败: \(httpResponse.statusCode)"))
                return
            }
            
            // 解析SSE事件流
            var currentEvent = ""
            var currentData = ""
            
            for try await line in bytes.lines {
                if line.hasPrefix("event: ") {
                    currentEvent = String(line.dropFirst(7))
                } else if line.hasPrefix("data: ") {
                    currentData = String(line.dropFirst(6))
                    
                    // 处理事件
                    await MainActor.run {
                        processUnifiedSSEEvent(
                            event: currentEvent,
                            data: currentData,
                            onChunk: onChunk,
                            onComplete: onComplete,
                            onError: onError
                        )
                    }
                    
                    currentEvent = ""
                    currentData = ""
                }
            }
        } catch {
            print("[API] ❌ SSE Error: \(error.localizedDescription)")
            onError(APIError.networkError(error))
        }
    }
    
    // MARK: - 获取智能体列表
    func listAgents() async throws -> [String: AgentCapabilities] {
        let endpoint = "/sessions/agents"
        return try await makeUnifiedRequest(endpoint: endpoint, method: "GET", requiresAuth: false)
    }
    
    // MARK: - 获取智能体能力
    func getAgentCapabilities(_ agentType: AgentType) async throws -> AgentCapabilities {
        let endpoint = "/sessions/agents/\(agentType.rawValue)/capabilities"
        return try await makeUnifiedRequest(endpoint: endpoint, method: "GET", requiresAuth: false)
    }
    
    // MARK: - Private Helpers
    
    private func makeUnifiedRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        requiresAuth: Bool = false
    ) async throws -> T {
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            print("[API] ❌ Invalid URL: \(APIConfig.baseURL + endpoint)")
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            guard let token = AuthManager.shared.token else {
                print("[API] ❌ No token available")
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
            if let bodyString = String(data: body, encoding: .utf8) {
                print("[API] 📤 \(method) \(endpoint)")
                print("[API] Body: \(bodyString)")
            }
        } else {
            print("[API] 📤 \(method) \(endpoint)")
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("[API] 📥 Status: \(httpResponse.statusCode)")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("[API] Response: \(responseString.prefix(500))")
                }
            }
            
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 {
                    print("[API] ❌ 401 Unauthorized")
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
            print("[API] ❌ APIError: \(error.errorDescription ?? "Unknown")")
            throw error
        } catch let error as DecodingError {
            print("[API] ❌ DecodingError: \(error)")
            throw APIError.decodingError(error)
        } catch {
            print("[API] ❌ NetworkError: \(error.localizedDescription)")
            throw APIError.networkError(error)
        }
    }
    
    private func processUnifiedSSEEvent(
        event: String,
        data: String,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (UnifiedMessageResponse) -> Void,
        onError: @escaping (Error) -> Void
    ) {
        switch event {
        case "chunk":
            if let jsonData = data.data(using: .utf8),
               let chunkObj = try? JSONDecoder().decode(SSEChunkData.self, from: jsonData) {
                onChunk(chunkObj.text)
            }
            
        case "complete":
            if let jsonData = data.data(using: .utf8) {
                do {
                    // === 调试：打印原始 JSON ===
                    if let jsonString = String(data: jsonData, encoding: .utf8) {
                        print("[API-DEBUG] 收到 complete 事件原始 JSON:")
                        print(jsonString)
                    }
                    // === 调试结束 ===
                    
                    let decoder = JSONDecoder()
                    decoder.dateDecodingStrategy = .iso8601
                    let response = try decoder.decode(UnifiedMessageResponse.self, from: jsonData)
                    
                    // === 调试：打印解码后的字段 ===
                    print("[API-DEBUG] 解码后的 UnifiedMessageResponse:")
                    print("[API-DEBUG] - message: \(response.message.prefix(50))...")
                    print("[API-DEBUG] - adviceHistory: \(response.adviceHistory?.count ?? 0) 条")
                    print("[API-DEBUG] - diagnosisCard: \(response.diagnosisCard != nil ? "有" : "无")")
                    print("[API-DEBUG] - knowledgeRefs: \(response.knowledgeRefs?.count ?? 0) 条")
                    print("[API-DEBUG] - reasoningSteps: \(response.reasoningSteps?.count ?? 0) 步")
                    // === 调试结束 ===
                    
                    onComplete(response)
                } catch {
                    print("[API] ❌ SSE complete decode error: \(error)")
                    if let decodingError = error as? DecodingError {
                        switch decodingError {
                        case .keyNotFound(let key, let context):
                            print("[API] ❌ 缺少字段: \(key.stringValue), path: \(context.codingPath)")
                        case .typeMismatch(let type, let context):
                            print("[API] ❌ 类型不匹配: 期望 \(type), path: \(context.codingPath)")
                        case .valueNotFound(let type, let context):
                            print("[API] ❌ 值为 null: 期望 \(type), path: \(context.codingPath)")
                        case .dataCorrupted(let context):
                            print("[API] ❌ 数据损坏: \(context.debugDescription)")
                        @unknown default:
                            print("[API] ❌ 未知解码错误")
                        }
                    }
                    onError(APIError.decodingError(error))
                }
            }
            
        case "error":
            if let jsonData = data.data(using: .utf8),
               let errorObj = try? JSONDecoder().decode(SSEErrorData.self, from: jsonData) {
                onError(APIError.serverError(errorObj.error))
            } else {
                onError(APIError.serverError("未知错误"))
            }
            
        case "meta":
            print("[API] SSE meta: \(data)")
            
        default:
            break
        }
    }
}

// MARK: - Response Models

struct UnifiedSendMessageResponse: Codable {
    let userMessage: UnifiedMessageModel
    let aiMessage: UnifiedMessageModel
    
    enum CodingKeys: String, CodingKey {
        case userMessage = "user_message"
        case aiMessage = "ai_message"
    }
}

struct UnifiedMessageModel: Codable {
    let id: Int
    let sessionId: String
    let sender: String
    let content: String
    let attachmentUrl: String?
    let messageType: String
    let attachments: [[String: AnyCodable]]?
    let structuredData: StructuredData?
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case sessionId = "session_id"
        case sender
        case content
        case attachmentUrl = "attachment_url"
        case messageType = "message_type"
        case attachments
        case structuredData = "structured_data"
        case createdAt = "created_at"
    }
}
