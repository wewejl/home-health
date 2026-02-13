import Foundation

// MARK: - Unified Chat API Extension
// 使用多智能体架构 /sessions 端点

extension APIService {
    
    // MARK: - 会话端点常量
    private struct SessionEndpoints {
        static let sessions = "/sessions"
        static func messages(sessionId: String) -> String {
            return "/sessions/\(sessionId)/messages"
        }
        static let agents = "/sessions/agents"
        static func agentCapabilities(agentType: String) -> String {
            return "/sessions/agents/\(agentType)/capabilities"
        }
    }
    
    // MARK: - 创建会话
    func createSession(doctorId: Int? = nil, agentType: AgentType? = nil) async throws -> UnifiedSessionResponse {
        var bodyDict: [String: Any] = [:]
        if let doctorId = doctorId {
            bodyDict["doctor_id"] = doctorId
        }
        if let agentType = agentType {
            bodyDict["agent_type"] = agentType.rawValue
        }

        let data = try JSONSerialization.data(withJSONObject: bodyDict)
        return try await makeRequest(endpoint: SessionEndpoints.sessions, method: "POST", body: data, requiresAuth: true)
    }

    // MARK: - 发送消息 - 流式响应
    func sendMessageStreaming(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (UnifiedMessageResponse) -> Void,
        onError: @escaping (Error) -> Void,
        isRetry: Bool = false
    ) async {
        let endpoint = SessionEndpoints.messages(sessionId: sessionId)
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
                if !isRetry {
                    print("[API] 🔄 Token过期,尝试刷新...")
                    do {
                        try await AuthManager.shared.refreshTokenIfNeeded()
                        print("[API] ✅ Token刷新成功,重试发送消息...")
                        await sendMessageStreaming(
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
                    
                    await MainActor.run {
                        processSSEEvent(
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
    
    // MARK: - 发送消息 - 非流式响应
    func sendMessage(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async throws -> AgentResponse {
        let endpoint = SessionEndpoints.messages(sessionId: sessionId)
        
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
        return try await makeRequest(endpoint: endpoint, method: "POST", body: data, requiresAuth: true)
    }

    // MARK: - 获取智能体列表
    func listAgents() async throws -> [String: SessionAgentCapabilities] {
        return try await makeRequest(endpoint: SessionEndpoints.agents, method: "GET", requiresAuth: false)
    }

    // MARK: - 获取智能体能力
    func getAgentCapabilities(_ agentType: AgentType) async throws -> SessionAgentCapabilities {
        let endpoint = SessionEndpoints.agentCapabilities(agentType: agentType.rawValue)
        return try await makeRequest(endpoint: endpoint, method: "GET", requiresAuth: false)
    }
    
    // MARK: - Private Helpers
    
    private func makeRequest<T: Decodable>(
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
    
    private func processSSEEvent(
        event: String,
        data: String,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (UnifiedMessageResponse) -> Void,
        onError: @escaping (Error) -> Void
    ) {
        switch event {
        case "chunk":
            if let jsonData = data.data(using: .utf8),
               let chunkObj = try? JSONDecoder().decode(SSEChunkEvent.self, from: jsonData) {
                onChunk(chunkObj.text)
            }

        case "complete":
            if let jsonData = data.data(using: .utf8) {
                do {
                    let decoder = JSONDecoder()
                    decoder.dateDecodingStrategy = .iso8601
                    let messageResponse = try decoder.decode(UnifiedMessageResponse.self, from: jsonData)
                    print("[API] ✅ SSE complete - stage: \(messageResponse.stage ?? "nil"), progress: \(messageResponse.progress ?? 0)")
                    onComplete(messageResponse)
                } catch {
                    print("[API] ❌ SSE complete decode error: \(error)")
                    onError(APIError.decodingError(error))
                }
            }

        case "error":
            if let jsonData = data.data(using: .utf8),
               let errorObj = try? JSONDecoder().decode(SSEErrorEvent.self, from: jsonData) {
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

// MARK: - Agent Capabilities Model
struct SessionAgentCapabilities: Codable {
    let displayName: String
    let description: String
    let actions: [String]
    let acceptsMedia: [String]

    enum CodingKeys: String, CodingKey {
        case displayName = "display_name"
        case description
        case actions
        case acceptsMedia = "accepts_media"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        displayName = try container.decode(String.self, forKey: .displayName)
        description = try container.decode(String.self, forKey: .description)
        actions = try container.decode([String].self, forKey: .actions)
        acceptsMedia = try container.decode([String].self, forKey: .acceptsMedia)
    }

    init(
        displayName: String = "",
        description: String = "",
        actions: [String] = [],
        acceptsMedia: [String] = []
    ) {
        self.displayName = displayName
        self.description = description
        self.actions = actions
        self.acceptsMedia = acceptsMedia
    }

    var supportsImageUpload: Bool {
        return acceptsMedia.contains { $0.starts(with: "image/") }
    }

    var supportsPdfUpload: Bool {
        return acceptsMedia.contains("application/pdf")
    }
}
