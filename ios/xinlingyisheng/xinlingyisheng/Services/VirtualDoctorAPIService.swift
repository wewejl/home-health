import Foundation

/// 虚拟医生 API 服务
final class VirtualDoctorAPIService {
    static let shared = VirtualDoctorAPIService()

    private let baseURL: String
    private let session: URLSession

    private init() {
        // 从配置中获取基础 URL，默认使用 localhost
        self.baseURL = AppConfig.apiBaseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
    }

    // MARK: - Virtual Doctor List

    /// 获取虚拟医生列表
    func listVirtualDoctors(departmentId: Int? = nil, personalityType: String? = nil) async throws -> [VirtualDoctor] {
        var components = URLComponents(string: "\(baseURL)/virtual-doctors")
        var queryItems: [URLQueryItem] = []

        if let departmentId = departmentId {
            queryItems.append(URLQueryItem(name: "department_id", value: "\(departmentId)"))
        }
        if let personalityType = personalityType {
            queryItems.append(URLQueryItem(name: "personality_type", value: personalityType))
        }

        components?.queryItems = queryItems

        guard let url = components?.url else {
            throw APIError.invalidURL
        }

        let data = try await performRequest(url: url)
        let doctors = try JSONDecoder().decode([VirtualDoctor].self, from: data)
        return doctors
    }

    // MARK: - Personalities

    /// 获取所有性格类型
    func listPersonalities() async throws -> [PersonalityConfig] {
        let url = URL(string: "\(baseURL)/virtual-doctors/personalities")!

        let data = try await performRequest(url: url)
        let response = try JSONDecoder().decode(PersonalitiesResponse.self, from: data)
        return response.personalities
    }

    // MARK: - Specialties

    /// 获取所有科室类型
    func listSpecialties() async throws -> [SpecialtyConfig] {
        let url = URL(string: "\(baseURL)/virtual-doctors/specialties")!

        let data = try await performRequest(url: url)
        let response = try JSONDecoder().decode(SpecialtiesResponse.self, from: data)
        return response.specialties
    }

    // MARK: - Doctor Detail

    /// 获取医生详情
    func getVirtualDoctorDetail(id: Int) async throws -> VirtualDoctorDetail {
        let url = URL(string: "\(baseURL)/virtual-doctors/\(id)")!

        let data = try await performRequest(url: url)
        return try JSONDecoder().decode(VirtualDoctorDetail.self, from: data)
    }

    // MARK: - Helper Methods

    private func performRequest(url: URL) async throws -> Data {
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // 添加认证 token 如果存在
        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200...299:
            return data
        case 401:
            throw APIError.unauthorized
        case 404:
            throw APIError.notFound
        case 500...599:
            throw APIError.serverError(statusCode: httpResponse.statusCode)
        default:
            throw APIError.unknown(statusCode: httpResponse.statusCode)
        }
    }

    // MARK: - Error Types

    enum APIError: LocalizedError {
        case invalidURL
        case invalidResponse
        case unauthorized
        case notFound
        case serverError(statusCode: Int)
        case unknown(statusCode: Int)
        case decodingError(Error)

        var errorDescription: String? {
            switch self {
            case .invalidURL:
                return "无效的 URL"
            case .invalidResponse:
                return "无效的响应"
            case .unauthorized:
                return "未授权，请重新登录"
            case .notFound:
                return "请求的资源不存在"
            case .serverError(let code):
                return "服务器错误 (\(code))"
            case .unknown(let code):
                return "未知错误 (\(code))"
            case .decodingError(let error):
                return "数据解析失败: \(error.localizedDescription)"
            }
        }
    }
}
