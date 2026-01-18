import Foundation

// MARK: - API Error Types

enum APIError: Error, LocalizedError {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case serverError(String)
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "无效的请求地址"
        case .networkError(let error):
            return "网络错误: \(error.localizedDescription)"
        case .decodingError:
            return "数据解析错误"
        case .serverError(let message):
            return message
        case .unauthorized:
            return "请先登录"
        }
    }
}

// MARK: - Common Response Types

struct ErrorResponse: Decodable {
    let detail: String
}

// MARK: - SSE Data Types

struct SSEChunkData: Decodable {
    let text: String
}

struct SSEErrorData: Decodable {
    let error: String
}
