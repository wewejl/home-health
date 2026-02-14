import Foundation
import SwiftUI

// MARK: - 病历夹模型

/// 病历夹 - 用于组织病历记录的文件夹
struct MedicalFolder: Identifiable, Codable, Hashable {
    let id: String
    let userId: Int
    var name: String
    var description: String?
    var color: String
    var icon: String
    var sortOrder: Int
    let createdAt: Date
    let updatedAt: Date
    var recordCount: Int

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case name
        case description
        case color
        case icon
        case sortOrder = "sort_order"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case recordCount = "record_count"
    }

    init(
        id: String = UUID().uuidString,
        userId: Int,
        name: String,
        description: String? = nil,
        color: String = "#7B5FEA",
        icon: String = "folder",
        sortOrder: Int = 0,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        recordCount: Int = 0
    ) {
        self.id = id
        self.userId = userId
        self.name = name
        self.description = description
        self.color = color
        self.icon = icon
        self.sortOrder = sortOrder
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.recordCount = recordCount
    }

    var colorValue: Color {
        Color(hex: color)
    }

    var iconValue: String {
        switch icon {
        case "folder": return "folder.fill"
        case "heart": return "heart.fill"
        case "star": return "star.fill"
        case "checkmark": return "checkmark.circle.fill"
        default: return "folder.fill"
        }
    }
}

// MARK: - 病历记录模型

/// 病历记录 - 单条医疗档案记录
struct MedicalRecord: Identifiable, Codable, Hashable {
    let id: String
    var folderId: String
    let userId: Int
    var title: String
    var recordDate: Date
    var description: String?
    let createdAt: Date
    let updatedAt: Date
    var fileCount: Int
    var files: [MedicalFile]?

    enum CodingKeys: String, CodingKey {
        case id
        case folderId = "folder_id"
        case userId = "user_id"
        case title
        case recordDate = "record_date"
        case description
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case fileCount = "file_count"
        case files
    }

    init(
        id: String = UUID().uuidString,
        folderId: String,
        userId: Int,
        title: String,
        recordDate: Date = Date(),
        description: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        fileCount: Int = 0,
        files: [MedicalFile]? = nil
    ) {
        self.id = id
        self.folderId = folderId
        self.userId = userId
        self.title = title
        self.recordDate = recordDate
        self.description = description
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.fileCount = fileCount
        self.files = files
    }

    var recordDateText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy年MM月dd日"
        return formatter.string(from: recordDate)
    }

    var recordDateShortText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM-dd"
        return formatter.string(from: recordDate)
    }
}

// MARK: - 医疗文件模型

/// 医疗文件 - 病历附件文件
struct MedicalFile: Identifiable, Codable, Hashable {
    let id: String
    var recordId: String
    let userId: Int
    var filename: String
    var fileType: String  // image, pdf, video, audio, document
    var mimeType: String
    var fileSize: Int
    var url: String
    var thumbnailUrl: String?
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case recordId = "record_id"
        case userId = "user_id"
        case filename
        case fileType = "file_type"
        case mimeType = "mime_type"
        case fileSize = "file_size"
        case url
        case thumbnailUrl = "thumbnail_url"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    init(
        id: String = UUID().uuidString,
        recordId: String,
        userId: Int,
        filename: String,
        fileType: String,
        mimeType: String,
        fileSize: Int,
        url: String,
        thumbnailUrl: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.recordId = recordId
        self.userId = userId
        self.filename = filename
        self.fileType = fileType
        self.mimeType = mimeType
        self.fileSize = fileSize
        self.url = url
        self.thumbnailUrl = thumbnailUrl
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    var fileTypeEnum: MedicalFileType {
        MedicalFileType(rawValue: fileType) ?? .document
    }

    var fileExtension: String {
        URL(string: filename)?.pathExtension.lowercased() ?? ""
    }

    var formattedSize: String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useBytes, .useKB, .useMB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(fileSize))
    }
}

// MARK: - 文件类型枚举

enum MedicalFileType: String, CaseIterable {
    case image = "image"
    case pdf = "pdf"
    case video = "video"
    case audio = "audio"
    case document = "document"

    var displayName: String {
        switch self {
        case .image: return "图片"
        case .pdf: return "PDF"
        case .video: return "视频"
        case .audio: return "音频"
        case .document: return "文档"
        }
    }

    var icon: String {
        switch self {
        case .image: return "photo.fill"
        case .pdf: return "doc.fill"
        case .video: return "video.fill"
        case .audio: return "waveform"
        case .document: return "doc.text.fill"
        }
    }

    var color: Color {
        switch self {
        case .image: return .blue
        case .pdf: return .red
        case .video: return .purple
        case .audio: return .orange
        case .document: return .gray
        }
    }
}

// MARK: - API 请求/响应模型

struct MedicalFolderCreateRequest: Codable {
    let name: String
    var description: String? = nil
    var color: String = "#7B5FEA"
    var icon: String = "folder"
    var sortOrder: Int = 0
}

struct MedicalFolderUpdateRequest: Codable {
    var name: String? = nil
    var description: String? = nil
    var color: String? = nil
    var icon: String? = nil
    var sortOrder: Int? = nil
}

struct MedicalFolderListResponse: Codable {
    let folders: [MedicalFolder]
    let total: Int
}

struct MedicalRecordCreateRequest: Codable {
    let folderId: String
    let title: String
    let recordDate: Date // ISO8601 格式
    var description: String? = nil

    enum CodingKeys: String, CodingKey {
        case folderId = "folder_id"
        case title
        case recordDate = "record_date"
        case description
    }
}

struct MedicalRecordUpdateRequest: Codable {
    var title: String? = nil
    var recordDate: Date? = nil
    var description: String? = nil
    var folderId: String? = nil

    enum CodingKeys: String, CodingKey {
        case title
        case recordDate = "record_date"
        case description
        case folderId = "folder_id"
    }
}

struct MedicalRecordListResponse: Codable {
    let records: [MedicalRecord]
    let total: Int
}

struct MedicalFileListResponse: Codable {
    let files: [MedicalFile]
    let total: Int
}

struct MedicalFileRenameRequest: Codable {
    let filename: String
}

struct FileUploadResponse: Codable {
    let file: MedicalFile
    let message: String
}
