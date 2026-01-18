import Foundation
import UIKit

// MARK: - 本地图片存储管理器
/// 负责图片的本地存储、读取、删除和清理
/// 所有图片仅保存在用户设备本地，不上传到服务器
class LocalImageManager {
    static let shared = LocalImageManager()
    
    private let fileManager = FileManager.default
    private let userDefaults = UserDefaults.standard
    private let metadataKey = "LocalImageRecords"
    
    // 图片存储目录
    private var imageDirectory: URL {
        let paths = fileManager.urls(for: .documentDirectory, in: .userDomainMask)
        let documentsDirectory = paths[0]
        let imageDir = documentsDirectory.appendingPathComponent("MedicalImages")
        
        // 创建目录（如果不存在）
        if !fileManager.fileExists(atPath: imageDir.path) {
            try? fileManager.createDirectory(at: imageDir, withIntermediateDirectories: true)
        }
        
        return imageDir
    }
    
    private init() {
        // 启动时清理过期图片
        cleanupOldImages()
    }
    
    // MARK: - 保存图片
    /// 保存图片到本地
    /// - Parameters:
    ///   - image: 要保存的UIImage
    ///   - sessionId: 关联的会话ID
    ///   - note: 可选的备注信息
    /// - Returns: 保存成功返回LocalImageRecord，失败返回nil
    @discardableResult
    func saveImage(_ image: UIImage, sessionId: String, note: String? = nil) -> LocalImageRecord? {
        let imageId = UUID().uuidString
        let fileName = "\(sessionId)_\(imageId).jpg"
        let fileURL = imageDirectory.appendingPathComponent(fileName)
        
        // 压缩图片质量至0.8
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            print("❌ [LocalImageManager] 图片压缩失败")
            return nil
        }
        
        do {
            try imageData.write(to: fileURL)
            
            let record = LocalImageRecord(
                id: imageId,
                sessionId: sessionId,
                fileName: fileName,
                filePath: fileURL.path,
                fileSize: imageData.count,
                note: note,
                createdAt: Date()
            )
            
            // 保存元数据
            saveMetadata(record)
            
            print("✅ [LocalImageManager] 图片已保存到本地: \(fileURL.path)")
            print("✅ [LocalImageManager] 文件大小: \(ByteCountFormatter.string(fromByteCount: Int64(imageData.count), countStyle: .file))")
            
            return record
        } catch {
            print("❌ [LocalImageManager] 图片保存失败: \(error)")
            return nil
        }
    }
    
    // MARK: - 获取图片
    /// 根据ID获取本地图片
    func loadImage(byId imageId: String) -> UIImage? {
        guard let record = getMetadata(byId: imageId) else {
            print("❌ [LocalImageManager] 未找到图片记录: \(imageId)")
            return nil
        }
        
        let fileURL = URL(fileURLWithPath: record.filePath)
        
        guard let imageData = try? Data(contentsOf: fileURL),
              let image = UIImage(data: imageData) else {
            print("❌ [LocalImageManager] 图片加载失败: \(record.filePath)")
            return nil
        }
        
        return image
    }
    
    /// 根据文件名获取图片
    func loadImage(byFileName fileName: String) -> UIImage? {
        let fileURL = imageDirectory.appendingPathComponent(fileName)
        
        guard let imageData = try? Data(contentsOf: fileURL),
              let image = UIImage(data: imageData) else {
            return nil
        }
        
        return image
    }
    
    // MARK: - 获取会话图片
    /// 获取指定会话的所有图片记录
    func getImages(forSession sessionId: String) -> [LocalImageRecord] {
        let allRecords = getAllMetadata()
        return allRecords.filter { $0.sessionId == sessionId }
            .sorted { $0.createdAt > $1.createdAt }
    }
    
    /// 获取所有图片记录
    func getAllImages() -> [LocalImageRecord] {
        return getAllMetadata().sorted { $0.createdAt > $1.createdAt }
    }
    
    // MARK: - 删除图片
    /// 根据ID删除图片
    @discardableResult
    func deleteImage(byId imageId: String) -> Bool {
        guard let record = getMetadata(byId: imageId) else {
            return false
        }
        
        let fileURL = URL(fileURLWithPath: record.filePath)
        
        do {
            try fileManager.removeItem(at: fileURL)
            deleteMetadata(byId: imageId)
            print("✅ [LocalImageManager] 图片已删除: \(imageId)")
            return true
        } catch {
            print("❌ [LocalImageManager] 图片删除失败: \(error)")
            return false
        }
    }
    
    /// 删除会话的所有图片
    func deleteImages(forSession sessionId: String) {
        let records = getImages(forSession: sessionId)
        for record in records {
            deleteImage(byId: record.id)
        }
    }
    
    // MARK: - 清理过期图片
    /// 清理30天前的图片
    func cleanupOldImages() {
        let calendar = Calendar.current
        guard let thirtyDaysAgo = calendar.date(byAdding: .day, value: -30, to: Date()) else {
            return
        }
        
        let allRecords = getAllMetadata()
        var deletedCount = 0
        
        for record in allRecords {
            if record.createdAt < thirtyDaysAgo {
                if deleteImage(byId: record.id) {
                    deletedCount += 1
                }
            }
        }
        
        if deletedCount > 0 {
            print("🧹 [LocalImageManager] 已清理 \(deletedCount) 张过期图片")
        }
    }
    
    // MARK: - 存储空间统计
    /// 获取图片占用的总存储空间（字节）
    func getTotalStorageUsed() -> Int64 {
        let records = getAllMetadata()
        return records.reduce(0) { $0 + Int64($1.fileSize) }
    }
    
    /// 获取格式化的存储空间字符串
    func getFormattedStorageUsed() -> String {
        let bytes = getTotalStorageUsed()
        return ByteCountFormatter.string(fromByteCount: bytes, countStyle: .file)
    }
    
    /// 获取图片数量
    func getImageCount() -> Int {
        return getAllMetadata().count
    }
    
    // MARK: - 元数据管理（私有方法）
    
    private func saveMetadata(_ record: LocalImageRecord) {
        var records = getAllMetadata()
        records.append(record)
        
        if let encoded = try? JSONEncoder().encode(records) {
            userDefaults.set(encoded, forKey: metadataKey)
        }
    }
    
    private func getMetadata(byId imageId: String) -> LocalImageRecord? {
        return getAllMetadata().first { $0.id == imageId }
    }
    
    private func getAllMetadata() -> [LocalImageRecord] {
        guard let data = userDefaults.data(forKey: metadataKey),
              let records = try? JSONDecoder().decode([LocalImageRecord].self, from: data) else {
            return []
        }
        return records
    }
    
    private func deleteMetadata(byId imageId: String) {
        var records = getAllMetadata()
        records.removeAll { $0.id == imageId }
        
        if let encoded = try? JSONEncoder().encode(records) {
            userDefaults.set(encoded, forKey: metadataKey)
        }
    }
    
    // MARK: - 图片转Base64
    /// 将图片转换为Base64字符串（用于API传输）
    func imageToBase64(_ image: UIImage, compressionQuality: CGFloat = 0.8) -> String? {
        guard let imageData = image.jpegData(compressionQuality: compressionQuality) else {
            return nil
        }
        return imageData.base64EncodedString()
    }
    
    /// 从本地记录获取Base64
    func getBase64(byId imageId: String, compressionQuality: CGFloat = 0.8) -> String? {
        guard let image = loadImage(byId: imageId) else {
            return nil
        }
        return imageToBase64(image, compressionQuality: compressionQuality)
    }
}

// MARK: - 本地图片记录模型
struct LocalImageRecord: Codable, Identifiable, Equatable {
    let id: String
    let sessionId: String
    let fileName: String
    let filePath: String
    let fileSize: Int
    let note: String?
    let createdAt: Date
    
    // 格式化的文件大小
    var formattedSize: String {
        ByteCountFormatter.string(fromByteCount: Int64(fileSize), countStyle: .file)
    }
    
    // 格式化的创建时间
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: createdAt)
    }
    
    // 相对时间描述
    var relativeDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return formatter.localizedString(for: createdAt, relativeTo: Date())
    }
}

// MARK: - 图片缩略图生成扩展
extension LocalImageManager {
    /// 生成缩略图
    func generateThumbnail(for imageId: String, size: CGSize = CGSize(width: 200, height: 200)) -> UIImage? {
        guard let image = loadImage(byId: imageId) else {
            return nil
        }
        
        let renderer = UIGraphicsImageRenderer(size: size)
        return renderer.image { _ in
            image.draw(in: CGRect(origin: .zero, size: size))
        }
    }
}
