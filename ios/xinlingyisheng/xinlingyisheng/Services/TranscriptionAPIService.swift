import Foundation

enum TranscriptionError: LocalizedError {
    case invalidURL
    case invalidFile
    case server(String)
    case network(Error)
    case decoding(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "语音识别服务地址无效"
        case .invalidFile:
            return "录音文件无效或已损坏"
        case .server(let message):
            return message
        case .network(let error):
            return "网络异常：\(error.localizedDescription)"
        case .decoding:
            return "语音识别返回数据解析失败"
        }
    }
}

final class TranscriptionAPIService {
    static let shared = TranscriptionAPIService()
    private init() {}
    
    private let boundary = "Boundary-\(UUID().uuidString)"
    
    func transcribeAudioFile(at url: URL) async throws -> TranscriptionResponse {
        guard let audioData = try? Data(contentsOf: url) else {
            throw TranscriptionError.invalidFile
        }
        
        guard let requestURL = URL(string: SpeechAPIConfig.baseURL + SpeechAPIConfig.Endpoints.transcription) else {
            throw TranscriptionError.invalidURL
        }
        
        var request = URLRequest(url: requestURL)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = buildMultipartBody(fileURL: url, fileData: audioData)
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode >= 400 {
                if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                    throw TranscriptionError.server(errorResponse.detail)
                }
                throw TranscriptionError.server("语音识别服务请求失败(\(httpResponse.statusCode))")
            }
            
            do {
                return try JSONDecoder().decode(TranscriptionResponse.self, from: data)
            } catch {
                throw TranscriptionError.decoding(error)
            }
        } catch let error as TranscriptionError {
            throw error
        } catch {
            throw TranscriptionError.network(error)
        }
    }
    
    private func buildMultipartBody(fileURL: URL, fileData: Data) -> Data {
        var body = Data()
        body.append("--\(boundary)\r\n")
        let fileName = fileURL.lastPathComponent
        let mimeType = mimeTypeForFileExtension(fileURL.pathExtension)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n")
        body.append("Content-Type: \(mimeType)\r\n\r\n")
        body.append(fileData)
        body.append("\r\n")
        body.append("--\(boundary)--\r\n")
        return body
    }
    
    private func mimeTypeForFileExtension(_ ext: String) -> String {
        switch ext.lowercased() {
        case "m4a":
            return "audio/m4a"
        case "aac":
            return "audio/aac"
        case "mp3":
            return "audio/mpeg"
        case "wav":
            return "audio/wav"
        case "ogg":
            return "audio/ogg"
        case "webm":
            return "audio/webm"
        default:
            return "application/octet-stream"
        }
    }
}

private extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}
