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
            var hasImage = false
            if case .image = message.messageType {
                hasImage = true
            }
            return FormattedMessage(
                role: message.isFromUser ? "用户" : "医生",
                timestamp: formatTime(message.timestamp),
                content: message.content,
                hasImage: hasImage,
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
        let timeStr = timeFormatter.string(from: Date())
        
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
