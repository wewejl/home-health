import Foundation

// MARK: - APIService

class APIService {
    static let shared = APIService()
    private init() {
        // 配置 URLSession 增加超时时间
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30.0  // 请求超时 30 秒
        config.timeoutIntervalForResource = 60.0  // 资源超时 60 秒
        URLSession.shared.delegateQueue.maxConcurrentOperationCount = 5
    }

    // 使用自定义的 URLSession
    private var urlSession: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30.0
        config.timeoutIntervalForResource = 60.0
        return URLSession(configuration: config)
    }()

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
            let (data, response) = try await urlSession.data(for: request)
            
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
    func getDepartments(primaryOnly: Bool = false) async throws -> [DepartmentModel] {
        var endpoint = APIConfig.Endpoints.departments
        if primaryOnly {
            endpoint += "?primary_only=true"
        }
        return try await makeRequest(endpoint: endpoint)
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

    // MARK: - MedLive Diseases
    func getDiseaseDetailMedLive(diseaseId: Int) async throws -> MedLiveDiseaseModel {
        return try await makeRequest(endpoint: APIConfig.Endpoints.diseaseDetailMedLive(diseaseId: diseaseId))
    }

    func getDiseaseByWikiId(wikiId: String) async throws -> MedLiveDiseaseModel {
        return try await makeRequest(endpoint: APIConfig.Endpoints.diseaseByWikiId(wikiId: wikiId))
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

    // MARK: - Medical Orders (医嘱执行监督)

    /// 获取医嘱列表
    func getMedicalOrders(status: String? = nil) async throws -> [MedicalOrder] {
        var endpoint = APIConfig.Endpoints.medicalOrders
        if let status = status {
            endpoint += "?status=\(status)"
        }
        return try await makeRequest(endpoint: endpoint, requiresAuth: true)
    }

    /// 获取医嘱详情
    func getMedicalOrder(orderId: Int) async throws -> MedicalOrder {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalOrders)/\(orderId)", requiresAuth: true)
    }

    /// 创建医嘱
    func createMedicalOrder(_ request: MedicalOrderCreateRequest) async throws -> MedicalOrder {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: APIConfig.Endpoints.medicalOrders, method: "POST", body: data, requiresAuth: true)
    }

    /// 更新医嘱
    func updateMedicalOrder(orderId: Int, request: MedicalOrderUpdateRequest) async throws -> MedicalOrder {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalOrders)/\(orderId)", method: "PUT", body: data, requiresAuth: true)
    }

    /// 激活医嘱
    func activateOrder(orderId: Int, request: ActivateOrderRequest) async throws -> MedicalOrder {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalOrders)/\(orderId)/activate", method: "POST", body: data, requiresAuth: true)
    }

    /// 获取指定日期的任务列表
    func getDailyTasks(date: String) async throws -> TaskListResponse {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalTasks)/\(date)", requiresAuth: true)
    }

    /// 获取待完成任务
    func getPendingTasks(date: String) async throws -> [TaskInstance] {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalTasks)/\(date)/pending", requiresAuth: true)
    }

    /// 完成任务打卡
    func completeTask(request: CompletionRecordRequest) async throws -> CompletionRecord {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.medicalTasks)/\(request.task_instance_id)/complete", method: "POST", body: data, requiresAuth: true)
    }

    /// 获取日依从性
    func getDailyCompliance(date: String) async throws -> ComplianceSummary {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.compliance)/daily?task_date=\(date)", requiresAuth: true)
    }

    /// 获取周依从性
    func getWeeklyCompliance() async throws -> WeeklyComplianceResponse {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.compliance)/weekly", requiresAuth: true)
    }

    /// 获取异常记录
    func getAbnormalRecords(days: Int = 30) async throws -> [AbnormalRecord] {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.compliance)/abnormal?days=\(days)", requiresAuth: true)
    }

    /// 获取预警列表
    func getAlerts(activeOnly: Bool = true, limit: Int = 50) async throws -> [Alert] {
        var endpoint = "\(APIConfig.Endpoints.alerts)?active_only=\(activeOnly)&limit=\(limit)"
        return try await makeRequest(endpoint: endpoint, requiresAuth: true)
    }

    /// 确认预警
    func acknowledgeAlert(alertId: Int) async throws -> AcknowledgeAlertResponse {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.alerts)/\(alertId)/acknowledge", method: "POST", requiresAuth: true)
    }

    /// 检查并创建预警
    func checkAlerts() async throws -> [Alert] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.alerts + "/check", method: "POST", requiresAuth: true)
    }

    /// 获取家属关系
    func getFamilyBonds() async throws -> [FamilyBond] {
        return try await makeRequest(endpoint: APIConfig.Endpoints.familyBonds, requiresAuth: true)
    }

    /// 创建家属关系
    func createFamilyBond(_ request: FamilyBondCreateRequest) async throws -> FamilyBond {
        let data = try JSONEncoder().encode(request)
        return try await makeRequest(endpoint: APIConfig.Endpoints.familyBonds, method: "POST", body: data, requiresAuth: true)
    }

    /// 删除家属关系
    func deleteFamilyBond(bondId: Int) async throws -> EmptyResponse {
        return try await makeRequest(endpoint: "\(APIConfig.Endpoints.familyBonds)/\(bondId)", method: "DELETE", requiresAuth: true)
    }
}

// MARK: - Request/Response Models

struct EmptyResponse: Decodable {
    let success: Bool?
    let message: String?
}

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
