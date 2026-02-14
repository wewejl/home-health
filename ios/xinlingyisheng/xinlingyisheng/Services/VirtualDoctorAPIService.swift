import Foundation

/// 虚拟医生 API 服务
class VirtualDoctorAPIService {
    static let shared = VirtualDoctorAPIService()

    private let baseURL: String

    private init() {
        self.baseURL = APIConfig.baseURL
    }

    // MARK: - Error Types

    enum VirtualDoctorError: Error {
        case invalidURL
        case decodingFailed
        case networkError(Error)

        var localizedDescription: String {
            switch self {
            case .invalidURL:
                return "无效的 URL"
            case .decodingFailed:
                return "数据解析失败"
            case .networkError(let error):
                return error.localizedDescription
            }
        }
    }

    // MARK: - API Methods

    /// 获取虚拟医生列表
    func listVirtualDoctors(
        departmentId: Int? = nil,
        personalityType: String? = nil,
        limit: Int = 100
    ) async throws -> VirtualDoctorListResponse {

        var components = URLComponents(string: "\(baseURL)/virtual-doctors")
        components?.queryItems = buildQueryItems(
            departmentId: departmentId,
            personalityType: personalityType,
            limit: limit
        )

        guard let url = components?.url else {
            throw VirtualDoctorError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)

        do {
            return try JSONDecoder().decode(VirtualDoctorListResponse.self, from: data)
        } catch {
            print("[VirtualDoctorAPIService] Decoding error: \(error)")
            throw VirtualDoctorError.decodingFailed
        }
    }

    /// 获取所有性格类型
    func listPersonalities() async throws -> [PersonalityConfig] {
        guard let url = URL(string: "\(baseURL)/virtual-doctors/personalities") else {
            throw VirtualDoctorError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)

        do {
            return try JSONDecoder().decode([PersonalityConfig].self, from: data)
        } catch {
            print("[VirtualDoctorAPIService] Decoding error: \(error)")
            throw VirtualDoctorError.decodingFailed
        }
    }

    /// 获取所有科室类型
    func listSpecialties() async throws -> [SpecialtyConfig] {
        guard let url = URL(string: "\(baseURL)/virtual-doctors/specialties") else {
            throw VirtualDoctorError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)

        do {
            return try JSONDecoder().decode([SpecialtyConfig].self, from: data)
        } catch {
            print("[VirtualDoctorAPIService] Decoding error: \(error)")
            throw VirtualDoctorError.decodingFailed
        }
    }

    /// 获取虚拟医生详情
    func getVirtualDoctorDetail(id: Int) async throws -> VirtualDoctorDetail {
        guard let url = URL(string: "\(baseURL)/virtual-doctors/\(id)") else {
            throw VirtualDoctorError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)

        do {
            return try JSONDecoder().decode(VirtualDoctorDetail.self, from: data)
        } catch {
            print("[VirtualDoctorAPIService] Decoding error: \(error)")
            throw VirtualDoctorError.decodingFailed
        }
    }

    /// 获取医生的性格配置
    func getDoctorPersonality(id: Int) async throws -> PersonalityConfig {
        guard let url = URL(string: "\(baseURL)/virtual-doctors/\(id)/personality") else {
            throw VirtualDoctorError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)

        do {
            return try JSONDecoder().decode(PersonalityConfig.self, from: data)
        } catch {
            print("[VirtualDoctorAPIService] Decoding error: \(error)")
            throw VirtualDoctorError.decodingFailed
        }
    }

    // MARK: - Private Helpers

    private func buildQueryItems(
        departmentId: Int?,
        personalityType: String?,
        limit: Int
    ) -> [URLQueryItem] {
        var items: [URLQueryItem] = []
        if let deptId = departmentId {
            items.append(URLQueryItem(name: "department_id", value: "\(deptId)"))
        }
        if let pType = personalityType {
            items.append(URLQueryItem(name: "personality_type", value: pType))
        }
        items.append(URLQueryItem(name: "limit", value: "\(limit)"))
        return items
    }
}

/// 科室配置
struct SpecialtyConfig: Codable {
    let code: String
    let name: String
    let agentClass: String

    enum CodingKeys: String, CodingKey {
        case code
        case name
        case agentClass = "agent_class"
    }
}
