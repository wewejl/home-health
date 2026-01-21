# 对话 PDF 导出功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 实现对话导出为 PDF 功能，用户可以在对话界面点击导出按钮，生成 PDF 文件并保存到病历资料夹，支持查看、分享和删除。

**架构：** 纯前端实现，使用 PDFKit 生成 PDF 文件，存储在 Documents/exports/ 目录，元数据保存在 UserDefaults。病历资料夹页面重构为 PDF 档案管理器，支持列表展示、搜索、查看和分享。

**技术栈：** SwiftUI, PDFKit, Combine, FileManager, UserDefaults

---

## 任务 1：创建导出数据模型

**文件：**
- Create: `ios/xinlingyisheng/xinlingyisheng/Models/ExportedConversation.swift`

**步骤 1：创建导出记录模型**

创建文件 `ios/xinlingyisheng/xinlingyisheng/Models/ExportedConversation.swift`：

```swift
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
    let userInfo: ExportUserInfo?
    
    /// 生成标题
    var generatedTitle: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateStr = formatter.string(from: sessionDate)
        return "\(department)咨询 - \(dateStr)"
    }
}

/// 用户信息（用于 PDF 导出）
struct ExportUserInfo {
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
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Models/ExportedConversation.swift
git commit -m "feat: add exported conversation data models"
```

---

## 任务 2：创建 PDF 生成器

**文件：**
- Create: `ios/xinlingyisheng/xinlingyisheng/Services/ConversationPDFGenerator.swift`

**步骤 1：创建 PDF 生成器基础结构**

创建文件 `ios/xinlingyisheng/xinlingyisheng/Services/ConversationPDFGenerator.swift`：

```swift
import UIKit
import PDFKit

/// PDF 样式配置
struct PDFStyle {
    // 页面设置
    static let pageSize = CGSize(width: 595, height: 842) // A4
    static let margin: CGFloat = 50
    
    // 字体
    static let titleFont = UIFont.systemFont(ofSize: 24, weight: .bold)
    static let headerFont = UIFont.systemFont(ofSize: 14, weight: .medium)
    static let bodyFont = UIFont.systemFont(ofSize: 12, weight: .regular)
    static let footerFont = UIFont.systemFont(ofSize: 10, weight: .light)
    
    // 颜色
    static let titleColor = UIColor.black
    static let userMessageColor = UIColor(red: 0.0, green: 0.48, blue: 1.0, alpha: 1.0)
    static let aiMessageColor = UIColor(red: 0.5, green: 0.5, blue: 0.5, alpha: 1.0)
    static let footerColor = UIColor.lightGray
    
    // 间距
    static let lineSpacing: CGFloat = 8
    static let paragraphSpacing: CGFloat = 16
    static let messageBubbleSpacing: CGFloat = 12
}

/// 格式化的消息
struct FormattedMessage {
    let role: String
    let timestamp: String
    let content: String
    let hasImage: Bool
    let isUser: Bool
}

/// 对话 PDF 生成器
class ConversationPDFGenerator {
    
    /// 生成 PDF 文件
    func generate(data: ConversationExportData) async throws -> URL {
        // 1. 准备输出路径
        let fileName = generateFileName(from: data.sessionDate)
        let outputURL = getExportsDirectory().appendingPathComponent(fileName)
        
        // 2. 创建 PDF 数据
        let pdfData = NSMutableData()
        let pageSize = PDFStyle.pageSize
        
        UIGraphicsBeginPDFContextToData(pdfData, CGRect(origin: .zero, size: pageSize), nil)
        
        // 3. 添加标题页
        UIGraphicsBeginPDFPage()
        addTitlePage(data: data, pageSize: pageSize)
        
        // 4. 添加对话内容
        let formattedMessages = formatMessages(data.messages)
        addMessagesPages(messages: formattedMessages, pageSize: pageSize)
        
        // 5. 结束 PDF 上下文
        UIGraphicsEndPDFContext()
        
        // 6. 保存文件
        try pdfData.write(to: outputURL)
        
        return outputURL
    }
    
    // MARK: - Private Methods
    
    private func addTitlePage(data: ConversationExportData, pageSize: CGSize) {
        let margin = PDFStyle.margin
        var yPosition: CGFloat = margin
        
        // 标题
        let titleText = "心灵医生 - 对话记录"
        let titleAttributes: [NSAttributedString.Key: Any] = [
            .font: PDFStyle.titleFont,
            .foregroundColor: PDFStyle.titleColor
        ]
        let titleSize = titleText.size(withAttributes: titleAttributes)
        let titleRect = CGRect(
            x: (pageSize.width - titleSize.width) / 2,
            y: yPosition,
            width: titleSize.width,
            height: titleSize.height
        )
        titleText.draw(in: titleRect, withAttributes: titleAttributes)
        yPosition += titleSize.height + 30
        
        // 分隔线
        let context = UIGraphicsGetCurrentContext()!
        context.setStrokeColor(UIColor.lightGray.cgColor)
        context.setLineWidth(1)
        context.move(to: CGPoint(x: margin, y: yPosition))
        context.addLine(to: CGPoint(x: pageSize.width - margin, y: yPosition))
        context.strokePath()
        yPosition += 20
        
        // 元信息
        let infoAttributes: [NSAttributedString.Key: Any] = [
            .font: PDFStyle.headerFont,
            .foregroundColor: UIColor.darkGray
        ]
        
        var infoLines = [
            "科室：\(data.department)",
            "医生：\(data.doctorName)",
            "日期：\(formatDate(data.sessionDate))",
        ]
        
        if let userInfo = data.userInfo, !userInfo.displayText.isEmpty {
            infoLines.append("患者：\(userInfo.displayText)")
        }
        
        for line in infoLines {
            let lineSize = line.size(withAttributes: infoAttributes)
            let lineRect = CGRect(
                x: margin,
                y: yPosition,
                width: pageSize.width - 2 * margin,
                height: lineSize.height
            )
            line.draw(in: lineRect, withAttributes: infoAttributes)
            yPosition += lineSize.height + 8
        }
    }
    
    private func addMessagesPages(messages: [FormattedMessage], pageSize: CGSize) {
        let margin = PDFStyle.margin
        var yPosition: CGFloat = margin
        let maxY = pageSize.height - margin - 30
        var pageNumber = 2
        
        for message in messages {
            let messageHeight = calculateMessageHeight(message, width: pageSize.width - 2 * margin)
            
            if yPosition + messageHeight > maxY {
                addPageFooter(pageNumber: pageNumber, pageSize: pageSize)
                UIGraphicsBeginPDFPage()
                yPosition = margin
                pageNumber += 1
            }
            
            drawMessage(message, at: CGPoint(x: margin, y: yPosition), width: pageSize.width - 2 * margin)
            yPosition += messageHeight + PDFStyle.messageBubbleSpacing
        }
        
        addPageFooter(pageNumber: pageNumber, pageSize: pageSize)
    }
    
    private func drawMessage(_ message: FormattedMessage, at origin: CGPoint, width: CGFloat) {
        var yPosition = origin.y
        
        // 时间戳和角色
        let headerText = "[\(message.role)] \(message.timestamp)"
        let headerAttributes: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: 10, weight: .medium),
            .foregroundColor: message.isUser ? PDFStyle.userMessageColor : PDFStyle.aiMessageColor
        ]
        let headerSize = headerText.size(withAttributes: headerAttributes)
        let headerRect = CGRect(x: origin.x, y: yPosition, width: width, height: headerSize.height)
        headerText.draw(in: headerRect, withAttributes: headerAttributes)
        yPosition += headerSize.height + 4
        
        // 消息内容
        let contentAttributes: [NSAttributedString.Key: Any] = [
            .font: PDFStyle.bodyFont,
            .foregroundColor: UIColor.black
        ]
        let contentSize = message.content.boundingRect(
            with: CGSize(width: width, height: .greatestFiniteMagnitude),
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: contentAttributes,
            context: nil
        )
        message.content.draw(
            in: CGRect(x: origin.x, y: yPosition, width: width, height: contentSize.height),
            withAttributes: contentAttributes
        )
        
        if message.hasImage {
            yPosition += contentSize.height + 8
            let imagePlaceholder = "[图片]"
            let placeholderAttributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 10, weight: .light),
                .foregroundColor: UIColor.gray
            ]
            imagePlaceholder.draw(at: CGPoint(x: origin.x, y: yPosition), withAttributes: placeholderAttributes)
        }
    }
    
    private func addPageFooter(pageNumber: Int, pageSize: CGSize) {
        let margin = PDFStyle.margin
        let yPosition = pageSize.height - margin + 10
        
        let footerText = "第 \(pageNumber) 页 | 导出时间：\(formatDate(Date())) | 本记录由心灵医生 AI 生成"
        let footerAttributes: [NSAttributedString.Key: Any] = [
            .font: PDFStyle.footerFont,
            .foregroundColor: PDFStyle.footerColor
        ]
        
        let footerSize = footerText.size(withAttributes: footerAttributes)
        let footerRect = CGRect(
            x: (pageSize.width - footerSize.width) / 2,
            y: yPosition,
            width: footerSize.width,
            height: footerSize.height
        )
        footerText.draw(in: footerRect, withAttributes: footerAttributes)
    }
    
    private func formatMessages(_ messages: [UnifiedChatMessage]) -> [FormattedMessage] {
        messages.map { message in
            FormattedMessage(
                role: message.isFromUser ? "用户" : "医生",
                timestamp: formatTime(message.timestamp ?? Date()),
                content: message.content,
                hasImage: message.messageType == .image,
                isUser: message.isFromUser
            )
        }
    }
    
    private func calculateMessageHeight(_ message: FormattedMessage, width: CGFloat) -> CGFloat {
        let headerHeight: CGFloat = 14
        let contentAttributes: [NSAttributedString.Key: Any] = [
            .font: PDFStyle.bodyFont
        ]
        let contentSize = message.content.boundingRect(
            with: CGSize(width: width, height: .greatestFiniteMagnitude),
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: contentAttributes,
            context: nil
        )
        
        var totalHeight = headerHeight + contentSize.height
        if message.hasImage {
            totalHeight += 20
        }
        
        return totalHeight
    }
    
    private func generateFileName(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateStr = formatter.string(from: date)
        
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HHmmss"
        let timeStr = timeFormatter.string(from: date)
        
        return "conversation_\(dateStr)_\(timeStr).pdf"
    }
    
    private func getExportsDirectory() -> URL {
        let documentsURL = FileManager.default
            .urls(for: .documentDirectory, in: .userDomainMask)[0]
        let exportsURL = documentsURL.appendingPathComponent("exports")
        
        try? FileManager.default.createDirectory(
            at: exportsURL,
            withIntermediateDirectories: true
        )
        
        return exportsURL
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/ConversationPDFGenerator.swift
git commit -m "feat: add PDF generator for conversation export"
```

---

## 任务 3：创建导出记录存储管理器

**文件：**
- Create: `ios/xinlingyisheng/xinlingyisheng/Services/ExportedConversationStore.swift`

**步骤 1：创建存储管理器**

创建文件 `ios/xinlingyisheng/xinlingyisheng/Services/ExportedConversationStore.swift`：

```swift
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
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Services/ExportedConversationStore.swift
git commit -m "feat: add exported conversation store manager"
```

---

## 任务 4：在 UnifiedChatViewModel 中集成导出功能

**文件：**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`

**步骤 1：添加导出方法**

在 `UnifiedChatViewModel.swift` 文件末尾添加导出功能：

```swift
// MARK: - 对话导出功能

extension UnifiedChatViewModel {
    
    /// 导出当前对话为 PDF
    func exportConversation() async {
        guard !messages.isEmpty else {
            errorMessage = "没有对话内容可以导出"
            showError = true
            return
        }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            // 1. 准备导出数据
            let exportData = ConversationExportData(
                doctorName: capabilities?.displayName ?? "AI医生",
                department: agentType?.displayName ?? "全科",
                sessionDate: Date(),
                messages: messages,
                userInfo: nil
            )
            
            // 2. 生成 PDF
            let generator = ConversationPDFGenerator()
            let pdfURL = try await generator.generate(data: exportData)
            
            // 3. 获取文件大小
            let fileAttributes = try FileManager.default.attributesOfItem(atPath: pdfURL.path)
            let fileSize = fileAttributes[.size] as? Int64 ?? 0
            
            // 4. 创建导出记录
            let export = ExportedConversation(
                id: UUID().uuidString,
                title: exportData.generatedTitle,
                department: exportData.department,
                doctorName: exportData.doctorName,
                exportDate: Date(),
                pdfFileName: pdfURL.lastPathComponent,
                messageCount: messages.count,
                fileSize: fileSize
            )
            
            // 5. 保存到存储
            await MainActor.run {
                ExportedConversationStore.shared.save(export)
            }
            
            // 6. 发送通知
            await MainActor.run {
                NotificationCenter.default.post(
                    name: .conversationExported,
                    object: export
                )
            }
            
            print("[Export] 导出成功: \(export.title), 文件大小: \(export.formattedFileSize)")
            
        } catch {
            await MainActor.run {
                errorMessage = "导出失败: \(error.localizedDescription)"
                showError = true
            }
            print("[Export] 导出失败: \(error)")
        }
    }
}

// MARK: - Notification

extension Notification.Name {
    static let conversationExported = Notification.Name("conversationExported")
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift
git commit -m "feat: integrate PDF export in UnifiedChatViewModel"
```

---

## 任务 5：修改导航栏添加导出按钮

**文件：**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Components/PhotoCapture/ChatNavBarV2.swift`

**步骤 1：添加导出按钮回调**

在 `ChatNavBarV2` 结构体中添加导出相关属性和按钮：

找到 `ChatNavBarV2` 的属性定义部分，添加：

```swift
var onExportConversation: (() -> Void)? = nil
var canExport: Bool = true
```

在右侧工具按钮部分，修改 `rightToolButtons` 视图：

```swift
private var rightToolButtons: some View {
    HStack(spacing: ScaleFactor.spacing(16)) {
        // 导出对话按钮
        if let onExport = onExportConversation {
            Button(action: {
                onExport()
            }) {
                Image(systemName: "square.and.arrow.up")
                    .font(.system(size: AdaptiveFont.title3))
                    .foregroundColor(canExport ? DXYColors.primaryPurple : DXYColors.textTertiary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .contentShape(Rectangle())
            }
            .disabled(!canExport)
            .opacity(canExport ? 1.0 : 0.5)
            .accessibilityLabel("导出对话")
            .accessibilityHint("将当前对话导出为PDF文件")
        }
        
        // 其他按钮保持不变...
    }
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Components/PhotoCapture/ChatNavBarV2.swift
git commit -m "feat: add export button to chat navigation bar"
```

---

## 任务 6：在对话界面集成导出功能

**文件：**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**步骤 1：添加导出成功状态和处理**

在 `ModernConsultationView` 中添加状态变量：

```swift
@State private var showExportSuccess = false
@State private var exportedConversation: ExportedConversation?
```

修改导航栏部分，添加导出回调：

找到 `ChatNavBarV2` 的调用，添加导出参数：

```swift
ChatNavBarV2(
    doctorName: viewModel.capabilities?.displayName ?? "AI医生",
    department: viewModel.agentType?.displayName,
    dismiss: dismiss,
    onExportConversation: {
        Task {
            await viewModel.exportConversation()
        }
    },
    canExport: viewModel.messages.count >= 2
    // 其他参数保持不变...
)
```

添加导出成功监听：

```swift
.onReceive(NotificationCenter.default.publisher(for: .conversationExported)) { notification in
    if let export = notification.object as? ExportedConversation {
        exportedConversation = export
        showExportSuccess = true
    }
}
.alert("导出成功", isPresented: $showExportSuccess) {
    Button("查看") {
        // TODO: 跳转到病历资料夹
    }
    Button("关闭", role: .cancel) {}
} message: {
    if let export = exportedConversation {
        Text("对话记录已保存到病历资料夹\n文件大小：\(export.formattedFileSize)")
    }
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift
git commit -m "feat: integrate export functionality in consultation view"
```

---

## 任务 7：创建 PDF 查看器组件

**文件：**
- Create: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/PDFViewerSheet.swift`

**步骤 1：创建 PDF 查看器**

创建文件 `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/PDFViewerSheet.swift`：

```swift
import SwiftUI
import PDFKit

/// PDF 查看器
struct PDFViewerSheet: View {
    let export: ExportedConversation
    @Environment(\.dismiss) var dismiss
    @State private var showShareSheet = false
    
    var body: some View {
        NavigationView {
            PDFKitView(url: export.pdfURL)
                .navigationTitle(export.title)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button("关闭") {
                            dismiss()
                        }
                    }
                    
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Menu {
                            Button(action: { showShareSheet = true }) {
                                Label("分享", systemImage: "square.and.arrow.up")
                            }
                            
                            Button(action: printPDF) {
                                Label("打印", systemImage: "printer")
                            }
                        } label: {
                            Image(systemName: "ellipsis.circle")
                        }
                    }
                }
        }
        .sheet(isPresented: $showShareSheet) {
            ShareSheet(activityItems: [export.pdfURL])
        }
    }
    
    private func printPDF() {
        let printController = UIPrintInteractionController.shared
        let printInfo = UIPrintInfo(dictionary: nil)
        printInfo.outputType = .general
        printInfo.jobName = export.title
        
        printController.printInfo = printInfo
        printController.printingItem = export.pdfURL
        printController.present(animated: true)
    }
}

/// PDFKit 包装视图
struct PDFKitView: UIViewRepresentable {
    let url: URL
    
    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = true
        pdfView.displayMode = .singlePageContinuous
        pdfView.displayDirection = .vertical
        
        if let document = PDFDocument(url: url) {
            pdfView.document = document
        }
        
        return pdfView
    }
    
    func updateUIView(_ uiView: PDFView, context: Context) {
        // 不需要更新
    }
}

/// 系统分享面板
struct ShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(
            activityItems: activityItems,
            applicationActivities: nil
        )
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {
        // 不需要更新
    }
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/PDFViewerSheet.swift
git commit -m "feat: add PDF viewer sheet component"
```

---

## 任务 8：创建导出记录列表项组件

**文件：**
- Create: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/ExportedConversationRow.swift`

**步骤 1：创建列表项组件**

创建文件 `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/ExportedConversationRow.swift`：

```swift
import SwiftUI

/// 导出记录列表项
struct ExportedConversationRow: View {
    let export: ExportedConversation
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 图标
            ZStack {
                RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall)
                    .fill(DXYColors.primaryPurple.opacity(0.1))
                    .frame(width: ScaleFactor.size(50), height: ScaleFactor.size(50))
                
                Image(systemName: "doc.text.fill")
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(DXYColors.primaryPurple)
            }
            
            // 信息
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text(export.title)
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                
                HStack(spacing: ScaleFactor.spacing(8)) {
                    Label(export.department, systemImage: "stethoscope")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(DXYColors.textSecondary)
                    
                    Text("•")
                        .foregroundColor(DXYColors.textSecondary)
                    
                    Text("\(export.messageCount) 条对话")
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(DXYColors.textSecondary)
                }
                
                Text(export.formattedExportDate)
                    .font(.system(size: AdaptiveFont.caption2))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            Spacer()
            
            // 文件大小和箭头
            VStack(alignment: .trailing, spacing: ScaleFactor.spacing(4)) {
                Text(export.formattedFileSize)
                    .font(.system(size: AdaptiveFont.caption2))
                    .foregroundColor(DXYColors.textSecondary)
                
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.caption2))
                    .foregroundColor(DXYColors.textTertiary)
            }
        }
        .padding(.vertical, ScaleFactor.padding(8))
    }
}

#Preview {
    ExportedConversationRow(
        export: ExportedConversation(
            id: "1",
            title: "皮肤科咨询 - 2026-01-18",
            department: "皮肤科",
            doctorName: "AI皮肤科医生",
            exportDate: Date(),
            pdfFileName: "conversation_2026-01-18_001.pdf",
            messageCount: 12,
            fileSize: 245760
        )
    )
    .padding()
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/ExportedConversationRow.swift
git commit -m "feat: add exported conversation row component"
```

---

## 任务 9：重构病历资料夹视图

**文件：**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalDossierView.swift`

**步骤 1：重构为导出记录列表**

完全重写 `MedicalDossierView.swift`：

```swift
import SwiftUI

/// 病历资料夹视图（重构为导出记录管理器）
struct MedicalDossierView: View {
    @StateObject private var store = ExportedConversationStore.shared
    @State private var searchText = ""
    @State private var selectedExport: ExportedConversation?
    @State private var showDeleteAlert = false
    @State private var exportToDelete: ExportedConversation?
    
    var filteredExports: [ExportedConversation] {
        store.search(keyword: searchText)
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // 搜索栏
                if !store.exports.isEmpty {
                    searchBar
                }
                
                // 列表
                if filteredExports.isEmpty {
                    emptyStateView
                } else {
                    exportsList
                }
            }
            .navigationTitle("病历资料夹")
            .toolbar {
                if !store.exports.isEmpty {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Menu {
                            Button(action: {}) {
                                Label("存储空间: \(store.getFormattedStorageSize())", systemImage: "info.circle")
                            }
                            .disabled(true)
                            
                            Divider()
                            
                            Button(role: .destructive, action: {
                                store.cleanupOldExports()
                            }) {
                                Label("清理30天前的记录", systemImage: "trash")
                            }
                        } label: {
                            Image(systemName: "ellipsis.circle")
                        }
                    }
                }
            }
        }
        .sheet(item: $selectedExport) { export in
            PDFViewerSheet(export: export)
        }
        .alert("确认删除", isPresented: $showDeleteAlert) {
            Button("取消", role: .cancel) {}
            Button("删除", role: .destructive) {
                if let export = exportToDelete {
                    store.delete(export)
                }
            }
        } message: {
            Text("删除后无法恢复，确定要删除这条记录吗？")
        }
    }
    
    // MARK: - Subviews
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(DXYColors.textTertiary)
            
            TextField("搜索对话记录", text: $searchText)
                .textFieldStyle(.plain)
            
            if !searchText.isEmpty {
                Button(action: { searchText = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(DXYColors.textTertiary)
                }
            }
        }
        .padding(ScaleFactor.padding(12))
        .background(DXYColors.backgroundSecondary)
        .cornerRadius(AdaptiveSize.cornerRadiusSmall)
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(8))
    }
    
    private var exportsList: some View {
        List {
            ForEach(filteredExports) { export in
                ExportedConversationRow(export: export)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        selectedExport = export
                    }
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            exportToDelete = export
                            showDeleteAlert = true
                        } label: {
                            Label("删除", systemImage: "trash")
                        }
                        
                        Button {
                            shareExport(export)
                        } label: {
                            Label("分享", systemImage: "square.and.arrow.up")
                        }
                        .tint(DXYColors.primaryPurple)
                    }
            }
        }
        .listStyle(.plain)
    }
    
    private var emptyStateView: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            Image(systemName: "doc.text")
                .font(.system(size: 60))
                .foregroundColor(DXYColors.textTertiary)
            
            Text(searchText.isEmpty ? "暂无导出记录" : "未找到匹配的记录")
                .font(.system(size: AdaptiveFont.title3, weight: .medium))
                .foregroundColor(DXYColors.textSecondary)
            
            if searchText.isEmpty {
                Text("在对话界面点击"导出"按钮\n即可生成对话记录")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // MARK: - Actions
    
    private func shareExport(_ export: ExportedConversation) {
        let activityVC = UIActivityViewController(
            activityItems: [export.pdfURL],
            applicationActivities: nil
        )
        
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let rootVC = windowScene.windows.first?.rootViewController {
            rootVC.present(activityVC, animated: true)
        }
    }
}

#Preview {
    MedicalDossierView()
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossier/MedicalDossierView.swift
git commit -m "refactor: rewrite medical dossier view as export manager"
```

---

## 任务 10：在应用启动时初始化存储

**文件：**
- Modify: `ios/xinlingyisheng/xinlingyisheng/xinlingyishengApp.swift`

**步骤 1：添加初始化逻辑**

在 `xinlingyishengApp` 中添加初始化：

```swift
@main
struct xinlingyishengApp: App {
    
    init() {
        // 初始化导出存储
        _ = ExportedConversationStore.shared
        
        // 清理过期文件（30天前）
        Task {
            await ExportedConversationStore.shared.cleanupOldExports()
        }
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

**步骤 2：编译验证**

运行编译：
```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug build
```

预期：编译成功，无错误

**步骤 3：提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/xinlingyishengApp.swift
git commit -m "feat: initialize export store on app launch"
```

---

## 任务 11：最终测试和验证

**步骤 1：运行完整编译**

```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -configuration Debug clean build
```

预期：编译成功，无错误和警告

**步骤 2：在模拟器中测试**

1. 启动应用
2. 进入对话界面
3. 发送几条消息
4. 点击右上角"导出"按钮
5. 验证导出成功提示
6. 进入病历资料夹
7. 验证记录显示
8. 点击记录查看 PDF
9. 测试分享功能
10. 测试删除功能

**步骤 3：最终提交**

```bash
git add -A
git commit -m "feat: complete conversation PDF export feature

- Add PDF generator with formatted layout
- Add export record storage manager
- Integrate export button in chat interface
- Refactor medical dossier view as export manager
- Add PDF viewer with share and print support
- Add automatic cleanup for old exports"
```

---

## 完成标准

1. ✅ 用户可以在对话界面点击导出按钮
2. ✅ PDF 生成成功并保存到本地
3. ✅ 病历资料夹显示导出记录列表
4. ✅ 用户可以查看 PDF 内容
5. ✅ 用户可以分享 PDF 给他人
6. ✅ 用户可以删除导出记录
7. ✅ 支持搜索功能
8. ✅ 自动清理30天前的记录
9. ✅ 所有功能编译通过，无错误

---

## 注意事项

1. **PDF 生成性能**：对于超过100条消息的对话，生成可能需要2-3秒，已添加 loading 状态
2. **存储空间**：每个 PDF 约 200-500KB，建议定期清理
3. **UserDefaults 限制**：元数据存储在 UserDefaults，建议记录数不超过1000条
4. **文件权限**：PDF 存储在 Documents/exports/，用户可通过文件 App 访问
5. **后续优化**：可考虑添加云端同步、PDF 加密等高级功能
