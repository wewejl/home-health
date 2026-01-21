import Foundation

/// 导出的对话记录
struct ExportedConversation: Identifiable, Codable {
    /// 唯一标识符
    let id: String
    
    /// 标题（自动生成）
    let title: String
    
    /// 科室名称
    let department: String
    
    /// 医生名称
    let doctorName: String
    
    /// 导出时间
    let exportDate: Date
    
    /// PDF 文件名
    let pdfFileName: String
    
    /// 对话消息数量
    let messageCount: Int
    
    /// 文件大小（字节）
    let fileSize: Int64
    
    /// 计算属性：PDF 文件完整路径
    var pdfURL: URL {
        FileManager.default
            .urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("exports")
            .appendingPathComponent(pdfFileName)
    }
    
    /// 计算属性：格式化的文件大小
    var formattedFileSize: String {
        ByteCountFormatter.string(fromByteCount: fileSize, countStyle: .file)
    }
    
    /// 计算属性：格式化的导出日期
    var formattedExportDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: exportDate)
    }
}

/// 用于生成 PDF 的数据结构
struct ConversationExportData {
    /// 医生名称
    let doctorName: String
    
    /// 科室名称
    let department: String
    
    /// 会话日期
    let sessionDate: Date
    
    /// 对话消息列表
    let messages: [UnifiedChatMessage]
    
    /// 用户信息（可选）
    let userInfo: ConversationExportUserInfo?
    
    /// 生成标题
    var generatedTitle: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateStr = formatter.string(from: sessionDate)
        return "\(department)咨询 - \(dateStr)"
    }
}

/// 用户信息（用于对话 PDF 导出）
struct ConversationExportUserInfo {
    let name: String?
    let age: Int?
    let gender: String?
    
    var displayText: String {
        var parts: [String] = []
        if let name = name { parts.append(name) }
        if let gender = gender { parts.append(gender) }
        if let age = age { parts.append("\(age)岁") }
        return parts.joined(separator: " / ")
    }
}
