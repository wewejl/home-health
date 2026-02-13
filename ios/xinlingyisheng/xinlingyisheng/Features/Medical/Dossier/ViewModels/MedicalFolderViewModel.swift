import Foundation
import SwiftUI
import Combine

// MARK: - MedicalFolderViewModel

/// 病历夹管理 ViewModel
@MainActor
class MedicalFolderViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var folders: [MedicalFolder] = []
    @Published var records: [MedicalRecord] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedFolder: MedicalFolder?
    @Published var selectedRecord: MedicalRecord?

    // MARK: - Dependencies
    private let apiService: APIService
    private let baseURL: String = APIConfig.baseURL

    // MARK: - Initializer
    init(apiService: APIService) {
        self.apiService = apiService
    }

    // MARK: - Helper Methods

    private func makeRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil
    ) async throws -> T {
        guard let token = AuthManager.shared.token else {
            throw APIError.unauthorized
        }

        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        if let body = body {
            request.httpBody = body
            print("[API] \(method) \(baseURL)\(endpoint)")
            print("[API] Body: \(String(data: body, encoding: .utf8) ?? "nil")")
        } else {
            print("[API] \(method) \(baseURL)\(endpoint)")
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        if let httpResponse = response as? HTTPURLResponse {
            print("[API] Status: \(httpResponse.statusCode)")

            if httpResponse.statusCode == 401 {
                DispatchQueue.main.async {
                    NotificationCenter.default.post(name: AuthManager.unauthorizedNotification, object: nil)
                }
                throw APIError.unauthorized
            }
            if httpResponse.statusCode >= 400 {
                let errorString = String(data: data, encoding: .utf8) ?? "No error data"
                print("[API] Error Response: \(errorString)")
                throw APIError.serverError("请求失败 (HTTP \(httpResponse.statusCode)): \(errorString)")
            }
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        do {
            let result = try decoder.decode(T.self, from: data)
            print("[API] Success: decoded response")
            return result
        } catch {
            print("[API] Decode Error: \(error)")
            print("[API] Response data: \(String(data: data, encoding: .utf8) ?? "nil")")
            throw error
        }
    }

    // MARK: - Folder Operations

    /// 加载所有病历夹
    func loadFolders() async {
        isLoading = true
        errorMessage = nil

        do {
            let response: MedicalFolderListResponse = try await makeRequest(endpoint: "/medical-folders", method: "GET")
            folders = response.folders.sorted { $0.sortOrder < $1.sortOrder }
        } catch {
            errorMessage = "加载病历夹失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to load folders: \(error)")
        }

        isLoading = false
    }

    /// 创建病历夹
    func createFolder(name: String, description: String? = nil, color: String = "#7B5FEA", icon: String = "folder") async -> MedicalFolder? {
        isLoading = true
        errorMessage = nil

        let request = MedicalFolderCreateRequest(
            name: name,
            description: description,
            color: color,
            icon: icon
        )

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(request)
            let response: MedicalFolder = try await makeRequest(endpoint: "/medical-folders", method: "POST", body: data)
            folders.append(response)
            isLoading = false
            return response
        } catch {
            errorMessage = "创建病历夹失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to create folder: \(error)")
            isLoading = false
            return nil
        }
    }

    /// 更新病历夹
    func updateFolder(_ folder: MedicalFolder, name: String? = nil, description: String? = nil, color: String? = nil, icon: String? = nil) async {
        isLoading = true
        errorMessage = nil

        var request = MedicalFolderUpdateRequest()
        if let name = name { request.name = name }
        if let description = description { request.description = description }
        if let color = color { request.color = color }
        if let icon = icon { request.icon = icon }

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(request)
            let updated: MedicalFolder = try await makeRequest(endpoint: "/medical-folders/\(folder.id)", method: "PUT", body: data)

            if let index = folders.firstIndex(where: { $0.id == folder.id }) {
                folders[index] = updated
            }
        } catch {
            errorMessage = "更新病历夹失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to update folder: \(error)")
        }

        isLoading = false
    }

    /// 删除病历夹
    func deleteFolder(_ folder: MedicalFolder) async {
        isLoading = true
        errorMessage = nil

        do {
            let _: EmptyResponse = try await makeRequest(endpoint: "/medical-folders/\(folder.id)", method: "DELETE")
            folders.removeAll { $0.id == folder.id }
        } catch {
            errorMessage = "删除病历夹失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to delete folder: \(error)")
        }

        isLoading = false
    }

    // MARK: - Record Operations

    /// 加载指定文件夹下的病历记录
    func loadRecords(folderId: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let endpoint: String
            if let folderId = folderId {
                endpoint = "/medical-records/by-folder/\(folderId)"
            } else {
                endpoint = "/medical-records"
            }

            let response: MedicalRecordListResponse = try await makeRequest(endpoint: endpoint, method: "GET")
            records = response.records
        } catch {
            errorMessage = "加载病历记录失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to load records: \(error)")
        }

        isLoading = false
    }

    /// 创建病历记录
    func createRecord(folderId: String, title: String, recordDate: Date, description: String? = nil) async -> MedicalRecord? {
        isLoading = true
        errorMessage = nil

        let request = MedicalRecordCreateRequest(
            folderId: folderId,
            title: title,
            recordDate: recordDate,
            description: description
        )

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(request)
            print("[MedicalFolderViewModel] Creating record with data: \(String(data: data, encoding: .utf8) ?? "nil")")
            let response: MedicalRecord = try await makeRequest(endpoint: "/medical-records", method: "POST", body: data)
            records.insert(response, at: 0)

            // 更新文件夹记录数
            if let index = folders.firstIndex(where: { $0.id == folderId }) {
                var folder = folders[index]
                folder.recordCount += 1
                folders[index] = folder
            }

            isLoading = false
            return response
        } catch {
            errorMessage = "创建病历记录失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to create record: \(error)")
            isLoading = false
            return nil
        }
    }

    /// 更新病历记录
    func updateRecord(_ record: MedicalRecord, title: String? = nil, recordDate: Date? = nil, description: String? = nil) async {
        isLoading = true
        errorMessage = nil

        var request = MedicalRecordUpdateRequest()
        if let title = title { request.title = title }
        if let recordDate = recordDate { request.recordDate = recordDate }
        if let description = description { request.description = description }

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(request)
            let updated: MedicalRecord = try await makeRequest(endpoint: "/medical-records/\(record.id)", method: "PUT", body: data)

            if let index = records.firstIndex(where: { $0.id == record.id }) {
                records[index] = updated
            }
        } catch {
            errorMessage = "更新病历记录失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to update record: \(error)")
        }

        isLoading = false
    }

    /// 删除病历记录
    func deleteRecord(_ record: MedicalRecord) async {
        isLoading = true
        errorMessage = nil

        do {
            let _: EmptyResponse = try await makeRequest(endpoint: "/medical-records/\(record.id)", method: "DELETE")
            records.removeAll { $0.id == record.id }

            // 更新文件夹记录数
            if let index = folders.firstIndex(where: { $0.id == record.folderId }) {
                var folder = folders[index]
                folder.recordCount = max(0, folder.recordCount - 1)
                folders[index] = folder
            }
        } catch {
            errorMessage = "删除病历记录失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to delete record: \(error)")
        }

        isLoading = false
    }

    /// 获取病历记录详情（包含文件）
    func loadRecordDetail(_ record: MedicalRecord) async -> MedicalRecord? {
        isLoading = true
        errorMessage = nil

        do {
            let detail: MedicalRecord = try await makeRequest(endpoint: "/medical-records/\(record.id)", method: "GET")

            if let index = records.firstIndex(where: { $0.id == record.id }) {
                records[index] = detail
            }

            isLoading = false
            return detail
        } catch {
            errorMessage = "加载病历详情失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to load record detail: \(error)")
            isLoading = false
            return nil
        }
    }

    // MARK: - File Operations

    // 最大文件大小限制 (50MB)
    private let maxFileSize: Int64 = 50 * 1024 * 1024

    /// 上传文件（核心方法，由调用者处理错误）
    func uploadFile(recordId: String, fileURL: URL, progressHandler: ((Double) -> Void)? = nil) async throws -> MedicalFile {
        // 检查文件是否存在
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            throw APIError.serverError("文件不存在")
        }

        // 获取文件大小
        let attributes = try FileManager.default.attributesOfItem(atPath: fileURL.path)
        guard let fileSize = attributes[.size] as? Int64 else {
            throw APIError.serverError("无法读取文件大小")
        }

        // 检查文件大小限制
        guard fileSize <= maxFileSize else {
            throw APIError.serverError("文件大小超过 50MB 限制")
        }

        // 使用流式上传避免大文件内存问题
        guard let url = URL(string: baseURL + "/medical-files/upload") else {
            throw APIError.invalidURL
        }

        guard let token = AuthManager.shared.token else {
            throw APIError.unauthorized
        }

        // 创建请求
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        // 创建临时文件用于上传
        let tempFileURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)

        defer {
            // 清理临时文件
            try? FileManager.default.removeItem(at: tempFileURL)
        }

        // 构建 multipart/form-data body
        let fileName = fileURL.lastPathComponent
        var body = Data()

        // 添加 file 字段头部
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)

        try body.write(to: tempFileURL)

        // 使用 InputStream 进行流式复制
        let fileHandle = try FileHandle(forReadingFrom: fileURL)
        defer { try? fileHandle.close() }

        let outputHandle = try FileHandle(forWritingTo: tempFileURL)
        defer { try? outputHandle.close() }

        // 移动到文件末尾
        try outputHandle.seekToEnd()

        // 分块读取和写入 (1MB chunks)
        let chunkSize = 1024 * 1024
        var bytesProcessed: Int64 = 0

        while autoreleasepool(invoking: {
            let chunk = fileHandle.readData(ofLength: chunkSize)
            if !chunk.isEmpty {
                outputHandle.write(chunk)
                bytesProcessed += Int64(chunk.count)

                // 报告进度
                if let progressHandler = progressHandler {
                    let progress = Double(bytesProcessed) / Double(fileSize)
                    Task { @MainActor in
                        progressHandler(progress)
                    }
                }
                return true
            }
            return false
        }) {}

        // 添加 record_id 字段
        body = Data()
        body.append("\r\n--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"record_id\"\r\n\r\n".data(using: .utf8)!)
        body.append(recordId.data(using: .utf8)!)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        outputHandle.write(body)

        // 使用 URLSession uploadTask（流式上传）
        let (result, response) = try await URLSession.shared.upload(for: request, fromFile: tempFileURL)

        if let httpResponse = response as? HTTPURLResponse {
            if httpResponse.statusCode == 401 {
                throw APIError.unauthorized
            }
            if httpResponse.statusCode >= 400 {
                if let errorString = String(data: result, encoding: .utf8) {
                    throw APIError.serverError("上传失败 (HTTP \(httpResponse.statusCode)): \(errorString)")
                }
                throw APIError.serverError("上传失败")
            }
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let uploadResponse: FileUploadResponse = try decoder.decode(FileUploadResponse.self, from: result)

        // 更新记录的文件列表
        if let index = records.firstIndex(where: { $0.id == recordId }) {
            var record = records[index]
            record.fileCount += 1
            if record.files == nil {
                record.files = []
            }
            record.files?.append(uploadResponse.file)
            records[index] = record
        }

        return uploadResponse.file
    }

    /// 上传文件（便利方法，自动处理错误并更新UI状态）
    func uploadFileSafely(recordId: String, fileURL: URL, progress: ((Double) -> Void)? = nil) async -> MedicalFile? {
        isLoading = true
        errorMessage = nil

        do {
            let file = try await uploadFile(recordId: recordId, fileURL: fileURL, progressHandler: progress)
            isLoading = false
            return file
        } catch {
            errorMessage = "上传文件失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to upload file: \(error)")
            isLoading = false
            return nil
        }
    }

    /// 删除文件
    func deleteFile(_ file: MedicalFile, recordId: String) async {
        isLoading = true
        errorMessage = nil

        do {
            let _: EmptyResponse = try await makeRequest(endpoint: "/medical-files/\(file.id)", method: "DELETE")

            // 更新记录的文件列表
            if let index = records.firstIndex(where: { $0.id == recordId }) {
                var record = records[index]
                record.fileCount = max(0, record.fileCount - 1)
                record.files?.removeAll { $0.id == file.id }
                records[index] = record
            }
        } catch {
            errorMessage = "删除文件失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to delete file: \(error)")
        }

        isLoading = false
    }

    /// 重命名文件
    func renameFile(_ file: MedicalFile, newName: String) async {
        isLoading = true
        errorMessage = nil

        let request = MedicalFileRenameRequest(filename: newName)

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(request)
            let updated: MedicalFile = try await makeRequest(endpoint: "/medical-files/\(file.id)", method: "PUT", body: data)

            // 更新记录中的文件
            for index in records.indices {
                if let fileIndex = records[index].files?.firstIndex(where: { $0.id == file.id }) {
                    records[index].files?[fileIndex] = updated
                }
            }
        } catch {
            errorMessage = "重命名文件失败: \(error.localizedDescription)"
            print("[MedicalFolderViewModel] Failed to rename file: \(error)")
        }

        isLoading = false
    }
}
