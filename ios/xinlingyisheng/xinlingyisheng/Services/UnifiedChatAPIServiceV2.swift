import Foundation

// MARK: - Unified Chat API V2 Extension
// 使用新的多智能体架构 /v2/sessions 端点

extension APIService {
    
    // MARK: - V2 端点常量
    private struct V2Endpoints {
        static let sessions = "/v2/sessions"
        static func messages(sessionId: String) -> String {
            return "/v2/sessions/\(sessionId)/messages"
        }
        static let agents = "/v2/sessions/agents"
        static func agentCapabilities(agentType: String) -> String {
            return "/v2/sessions/agents/\(agentType)/capabilities"
        }
    }
    
    // MARK: - 创建会话 V2
    func createSessionV2(doctorId: Int? = nil, agentType: AgentType? = nil) async throws -> UnifiedSessionResponse {
        var bodyDict: [String: Any] = [:]
        if let doctorId = doctorId {
            bodyDict["doctor_id"] = doctorId
        }
        if let agentType = agentType {
            bodyDict["agent_type"] = agentType.rawValue
        }
        
        let data = try JSONSerialization.data(withJSONObject: bodyDict)
        return try await makeV2Request(endpoint: V2Endpoints.sessions, method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - 发送消息 V2 - 流式响应
    func sendMessageStreamingV2(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (AgentResponseV2) -> Void,
        onError: @escaping (Error) -> Void,
        isRetry: Bool = false
    ) async {
        let endpoint = V2Endpoints.messages(sessionId: sessionId)
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
        
        print("[API-V2] 📤 SSE POST \(endpoint)\(isRetry ? " (重试)" : "")")
        
        do {
            let (bytes, response) = try await URLSession.shared.bytes(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                onError(APIError.serverError("无效的响应"))
                return
            }
            
            print("[API-V2] 📥 SSE Status: \(httpResponse.statusCode)")
            
            if httpResponse.statusCode == 401 {
                if !isRetry {
                    print("[API-V2] 🔄 Token过期,尝试刷新...")
                    do {
                        try await AuthManager.shared.refreshTokenIfNeeded()
                        print("[API-V2] ✅ Token刷新成功,重试发送消息...")
                        await sendMessageStreamingV2(
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
                        print("[API-V2] ❌ Token刷新失败: \(error)")
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
                        processSSEEventV2(
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
            print("[API-V2] ❌ SSE Error: \(error.localizedDescription)")
            onError(APIError.networkError(error))
        }
    }
    
    // MARK: - 发送消息 V2 - 非流式响应
    func sendMessageV2(
        sessionId: String,
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async throws -> AgentResponseV2 {
        let endpoint = V2Endpoints.messages(sessionId: sessionId)
        
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
        return try await makeV2Request(endpoint: endpoint, method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - 获取智能体列表 V2
    func listAgentsV2() async throws -> [String: AgentCapabilitiesV2] {
        return try await makeV2Request(endpoint: V2Endpoints.agents, method: "GET", requiresAuth: false)
    }
    
    // MARK: - 获取智能体能力 V2
    func getAgentCapabilitiesV2(_ agentType: AgentType) async throws -> AgentCapabilitiesV2 {
        let endpoint = V2Endpoints.agentCapabilities(agentType: agentType.rawValue)
        return try await makeV2Request(endpoint: endpoint, method: "GET", requiresAuth: false)
    }
    
    // MARK: - Private Helpers
    
    private func makeV2Request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        requiresAuth: Bool = false
    ) async throws -> T {
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            print("[API-V2] ❌ Invalid URL: \(APIConfig.baseURL + endpoint)")
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            guard let token = AuthManager.shared.token else {
                print("[API-V2] ❌ No token available")
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
            if let bodyString = String(data: body, encoding: .utf8) {
                print("[API-V2] 📤 \(method) \(endpoint)")
                print("[API-V2] Body: \(bodyString)")
            }
        } else {
            print("[API-V2] 📤 \(method) \(endpoint)")
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("[API-V2] 📥 Status: \(httpResponse.statusCode)")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("[API-V2] Response: \(responseString.prefix(500))")
                }
            }
            
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 {
                    print("[API-V2] ❌ 401 Unauthorized")
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
            print("[API-V2] ❌ APIError: \(error.errorDescription ?? "Unknown")")
            throw error
        } catch let error as DecodingError {
            print("[API-V2] ❌ DecodingError: \(error)")
            throw APIError.decodingError(error)
        } catch {
            print("[API-V2] ❌ NetworkError: \(error.localizedDescription)")
            throw APIError.networkError(error)
        }
    }
    
    private func processSSEEventV2(
        event: String,
        data: String,
        onChunk: @escaping (String) -> Void,
        onComplete: @escaping (AgentResponseV2) -> Void,
        onError: @escaping (Error) -> Void
    ) {
        switch event {
        case "chunk":
            if let jsonData = data.data(using: .utf8),
               let chunkObj = try? JSONDecoder().decode(SSEChunkEventV2.self, from: jsonData) {
                onChunk(chunkObj.text)
            }
            
        case "complete":
            if let jsonData = data.data(using: .utf8) {
                do {
                    let decoder = JSONDecoder()
                    decoder.dateDecodingStrategy = .iso8601
                    let response = try decoder.decode(AgentResponseV2.self, from: jsonData)
                    print("[API-V2] ✅ SSE complete - stage: \(response.stage), progress: \(response.progress)")
                    onComplete(response)
                } catch {
                    print("[API-V2] ❌ SSE complete decode error: \(error)")
                    onError(APIError.decodingError(error))
                }
            }
            
        case "error":
            if let jsonData = data.data(using: .utf8),
               let errorObj = try? JSONDecoder().decode(SSEErrorEventV2.self, from: jsonData) {
                onError(APIError.serverError(errorObj.error))
            } else {
                onError(APIError.serverError("未知错误"))
            }
            
        case "meta":
            print("[API-V2] SSE meta: \(data)")
            
        default:
            break
        }
    }
}

// MARK: - V2 Capabilities Model
struct AgentCapabilitiesV2: Codable {
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
    
    var supportsImageUpload: Bool {
        return acceptsMedia.contains { $0.starts(with: "image/") }
    }
    
    var supportsPdfUpload: Bool {
        return acceptsMedia.contains("application/pdf")
    }
}
