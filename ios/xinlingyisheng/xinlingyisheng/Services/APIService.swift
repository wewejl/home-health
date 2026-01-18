import Foundation

// MARK: - APIService

class APIService {
    static let shared = APIService()
    private init() {}
    
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
                    print("[API] Response: \(responseString)")
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
    
    // MARK: - Auth
    func sendVerificationCode(phone: String) async throws {
        let body = SendCodeRequest(phone: phone)
        let data = try JSONEncoder().encode(body)
        let _: SendCodeResponse = try await makeRequest(endpoint: APIConfig.Endpoints.sendCode, method: "POST", body: data)
    }
    
    func login(phone: String, code: String) async throws -> LoginResponse {
        let body = LoginRequest(phone: phone, code: code)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.login, method: "POST", body: data)
    }
    
    func refreshToken(refreshToken: String) async throws -> RefreshTokenResponse {
        let body = RefreshTokenRequest(refresh_token: refreshToken)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.refresh, method: "POST", body: data)
    }
    
    func getProfile() async throws -> UserModel {
        return try await makeRequest(endpoint: APIConfig.Endpoints.me, requiresAuth: true)
    }
    
    func updateProfile(request: ProfileUpdateRequest) async throws -> UserModel {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: APIConfig.Endpoints.profile, method: "PUT", body: data, requiresAuth: true)
    }
    
    func completeProfile(request: ProfileUpdateRequest) async throws -> UserModel {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: APIConfig.Endpoints.profile, method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - Password Auth
    func checkPhone(phone: String) async throws -> CheckPhoneResponse {
        return try await makeRequest(endpoint: APIConfig.Endpoints.checkPhone + "?phone=\(phone)")
    }
    
    func loginWithPassword(phone: String, password: String) async throws -> LoginResponse {
        let body = PasswordLoginRequest(phone: phone, password: password)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.loginPassword, method: "POST", body: data)
    }
    
    func registerWithPassword(phone: String, code: String, password: String) async throws -> LoginResponse {
        let body = PasswordRegisterRequest(phone: phone, code: code, password: password)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.registerPassword, method: "POST", body: data)
    }
    
    func resetPassword(phone: String, code: String, newPassword: String) async throws -> LoginResponse {
        let body = PasswordResetRequest(phone: phone, code: code, new_password: newPassword)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.resetPassword, method: "POST", body: data)
    }
    
    // MARK: - Departments
    func getDepartments() async throws -> [DepartmentModel] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.departments)
    }
    
    func getDoctors(departmentId: Int) async throws -> [DoctorModel] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.doctors(departmentId: departmentId))
    }
    
    // MARK: - Sessions
    func getSessions() async throws -> [SessionModel] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.sessions, requiresAuth: true)
    }
    
    func createSession(doctorId: Int?) async throws -> SessionModel {
        let body = CreateSessionRequest(doctor_id: doctorId)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.sessions, method: "POST", body: data, requiresAuth: true)
    }
    
    func getMessages(sessionId: String, limit: Int = 20, before: Int? = nil) async throws -> MessageListResponse {
        var endpoint = APIConfig.Endpoints.messages(sessionId: sessionId) + "?limit=\(limit)"
        if let before = before {
            endpoint += "&before=\(before)"
        }
        return try await makeRequest(endpoint: endpoint, requiresAuth: true)
    }
    
    func sendMessage(sessionId: String, content: String) async throws -> SendMessageResponse {
        let body = SendMessageRequest(content: content)
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: APIConfig.Endpoints.messages(sessionId: sessionId), method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - Feedback
    func submitFeedback(sessionId: String, messageId: Int?, rating: Int?, feedbackType: String?, feedbackText: String?) async throws -> FeedbackResponse {
        let body = FeedbackRequest(
            message_id: messageId,
            rating: rating,
            feedback_type: feedbackType,
            feedback_text: feedbackText
        )
        let data = try JSONEncoder().encode(body)
        return try await makeRequest(endpoint: "/sessions/\(sessionId)/feedback", method: "POST", body: data, requiresAuth: true)
    }
    
    // MARK: - Diseases
    func getDepartmentsWithDiseases() async throws -> [DepartmentWithDiseasesModel] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.departmentsWithDiseases)
    }
    
    func getDiseases(departmentId: Int? = nil, isHot: Bool? = nil) async throws -> [DiseaseListModel] {
        var endpoint = APIConfig.Endpoints.diseases
        var params: [String] = []
        if let departmentId = departmentId {
            params.append("department_id=\(departmentId)")
        }
        if let isHot = isHot {
            params.append("is_hot=\(isHot)")
        }
        if !params.isEmpty {
            endpoint += "?" + params.joined(separator: "&")
        }
        return try await makeRequest(endpoint: endpoint)
    }
    
    func getHotDiseases(departmentId: Int? = nil, limit: Int = 10) async throws -> [DiseaseListModel] {
        var endpoint = APIConfig.Endpoints.diseasesHot + "?limit=\(limit)"
        if let departmentId = departmentId {
            endpoint += "&department_id=\(departmentId)"
        }
        return try await makeRequest(endpoint: endpoint)
    }
    
    func searchDiseases(query: String, departmentId: Int? = nil, limit: Int = 20, offset: Int = 0) async throws -> DiseaseSearchResponse {
        var endpoint = APIConfig.Endpoints.diseasesSearch + "?q=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query)&limit=\(limit)&offset=\(offset)"
        if let departmentId = departmentId {
            endpoint += "&department_id=\(departmentId)"
        }
        return try await makeRequest(endpoint: endpoint)
    }
    
    func getDiseaseDetail(diseaseId: Int) async throws -> DiseaseDetailModel {
        return try await makeRequest(endpoint: APIConfig.Endpoints.diseaseDetail(diseaseId: diseaseId))
    }
    
    // MARK: - Drugs
    func getDrugCategoriesWithDrugs(limit: Int = 10) async throws -> [DrugCategoryWithDrugsModel] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.drugsCategories + "?limit=\(limit)")
    }
    
    func getHotDrugs(categoryId: Int? = nil, limit: Int = 20) async throws -> [DrugListModel] {
        var endpoint = APIConfig.Endpoints.drugsHot + "?limit=\(limit)"
        if let categoryId = categoryId {
            endpoint += "&category_id=\(categoryId)"
        }
        return try await makeRequest(endpoint: endpoint)
    }
    
    func searchDrugs(query: String, categoryId: Int? = nil, limit: Int = 20, offset: Int = 0) async throws -> DrugSearchResponse {
        var endpoint = APIConfig.Endpoints.drugsSearch + "?q=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query)&limit=\(limit)&offset=\(offset)"
        if let categoryId = categoryId {
            endpoint += "&category_id=\(categoryId)"
        }
        return try await makeRequest(endpoint: endpoint)
    }
    
    func getDrugDetail(drugId: Int) async throws -> DrugDetailModel {
        return try await makeRequest(endpoint: APIConfig.Endpoints.drugDetail(drugId: drugId))
    }
}

// MARK: - Request/Response Models

struct SendCodeRequest: Encodable {
    let phone: String
}

struct SendCodeResponse: Decodable {
    let message: String?
    let expires_in: Int?
}

struct LoginRequest: Encodable {
    let phone: String
    let code: String
}

struct LoginResponse: Decodable {
    let token: String
    let refresh_token: String?
    let user: UserModel
    let is_new_user: Bool?
}

struct ProfileUpdateRequest: Encodable {
    var nickname: String?
    var avatar_url: String?
    var gender: String?
    var birth_date: String?
    var emergency_contact_phone: String?
    var emergency_contact_relation: String?
}

struct RefreshTokenRequest: Encodable {
    let refresh_token: String
}

struct RefreshTokenResponse: Decodable {
    let token: String
    let refresh_token: String
}

struct CreateSessionRequest: Encodable {
    let doctor_id: Int?
}

struct SendMessageRequest: Encodable {
    let content: String
}

struct SendMessageResponse: Decodable {
    let user_message: MessageModel
    let ai_message: MessageModel
    
    // 病历事件关联字段（对话结束时自动生成）
    let event_id: String?
    let is_new_event: Bool?
    let should_show_dossier_prompt: Bool?
}

struct MessageListResponse: Decodable {
    let messages: [MessageModel]
    let has_more: Bool
}

// MARK: - Password Auth Models

struct CheckPhoneResponse: Decodable {
    let exists: Bool
    let has_password: Bool
}

struct PasswordLoginRequest: Encodable {
    let phone: String
    let password: String
}

struct PasswordRegisterRequest: Encodable {
    let phone: String
    let code: String
    let password: String
}

struct PasswordResetRequest: Encodable {
    let phone: String
    let code: String
    let new_password: String
}
