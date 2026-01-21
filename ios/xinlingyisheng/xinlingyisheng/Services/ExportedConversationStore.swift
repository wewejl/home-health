import Foundation
import Combine

/// 导出记录存储管理器
@MainActor
class ExportedConversationStore: ObservableObject {
    static let shared = ExportedConversationStore()
    
    @Published var exports: [ExportedConversation] = []
    
    private let userDefaultsKey = "exported_conversations"
    private let exportsDirectory: URL
    
    private init() {
        let documentsURL = FileManager.default
            .urls(for: .documentDirectory, in: .userDomainMask)[0]
        exportsDirectory = documentsURL.appendingPathComponent("exports")
        
        try? FileManager.default.createDirectory(
            at: exportsDirectory,
            withIntermediateDirectories: true
        )
        
        loadFromUserDefaults()
    }
    
    /// 保存导出记录
    func save(_ export: ExportedConversation) {
        exports.append(export)
        exports.sort { $0.exportDate > $1.exportDate }
        saveToUserDefaults()
    }
    
    /// 删除导出记录
    func delete(_ export: ExportedConversation) {
        try? FileManager.default.removeItem(at: export.pdfURL)
        exports.removeAll { $0.id == export.id }
        saveToUserDefaults()
    }
    
    /// 批量删除
    func deleteMultiple(_ exports: [ExportedConversation]) {
        for export in exports {
            delete(export)
        }
    }
    
    /// 搜索记录
    func search(keyword: String) -> [ExportedConversation] {
        guard !keyword.isEmpty else { return exports }
        
        return exports.filter { export in
            export.title.localizedCaseInsensitiveContains(keyword) ||
            export.department.localizedCaseInsensitiveContains(keyword) ||
            export.doctorName.localizedCaseInsensitiveContains(keyword)
        }
    }
    
    /// 按科室筛选
    func filterByDepartment(_ department: String) -> [ExportedConversation] {
        exports.filter { $0.department == department }
    }
    
    /// 按日期范围筛选
    func filterByDateRange(from: Date, to: Date) -> [ExportedConversation] {
        exports.filter { export in
            export.exportDate >= from && export.exportDate <= to
        }
    }
    
    /// 清理过期的导出文件（超过指定天数）
    func cleanupOldExports(olderThan days: Int = 30) {
        let cutoffDate = Calendar.current.date(byAdding: .day, value: -days, to: Date())!
        let oldExports = exports.filter { $0.exportDate < cutoffDate }
        
        for export in oldExports {
            delete(export)
        }
        
        print("[Cleanup] 清理了 \(oldExports.count) 个过期导出")
    }
    
    /// 获取总存储空间占用
    func getTotalStorageSize() -> Int64 {
        exports.reduce(0) { $0 + $1.fileSize }
    }
    
    /// 获取格式化的存储空间占用
    func getFormattedStorageSize() -> String {
        let totalSize = getTotalStorageSize()
        return ByteCountFormatter.string(fromByteCount: totalSize, countStyle: .file)
    }
    
    // MARK: - Private Methods
    
    private func loadFromUserDefaults() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            return
        }
        
        do {
            exports = try JSONDecoder().decode([ExportedConversation].self, from: data)
        } catch {
            print("Failed to load exports: \(error)")
        }
    }
    
    private func saveToUserDefaults() {
        do {
            let data = try JSONEncoder().encode(exports)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            print("Failed to save exports: \(error)")
        }
    }
}
