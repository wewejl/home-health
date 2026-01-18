import UIKit
import PDFKit

class PDFGenerator {
    static let shared = PDFGenerator()
    
    private init() {}
    
    // MARK: - PDF Configuration
    struct PDFConfig {
        let pageSize = CGSize(width: 595, height: 842) // A4
        let margin = UIEdgeInsets(top: 50, left: 40, bottom: 50, right: 40)
        
        var contentWidth: CGFloat {
            pageSize.width - margin.left - margin.right
        }
        
        var contentHeight: CGFloat {
            pageSize.height - margin.top - margin.bottom
        }
    }
    
    // MARK: - Fonts
    private struct Fonts {
        static func headerTitle() -> UIFont {
            UIFont.systemFont(ofSize: 18, weight: .semibold)
        }
        
        static func headerSubtitle() -> UIFont {
            UIFont.systemFont(ofSize: 12, weight: .regular)
        }
        
        static func sectionTitle() -> UIFont {
            UIFont.systemFont(ofSize: 14, weight: .semibold)
        }
        
        static func body() -> UIFont {
            UIFont.systemFont(ofSize: 12, weight: .regular)
        }
        
        static func label() -> UIFont {
            UIFont.systemFont(ofSize: 11, weight: .regular)
        }
        
        static func disclaimer() -> UIFont {
            UIFont.systemFont(ofSize: 10, weight: .regular)
        }
    }
    
    // MARK: - Colors
    private struct Colors {
        static let primary = UIColor(red: 0.36, green: 0.27, blue: 1.0, alpha: 1.0)
        static let teal = UIColor(red: 0.20, green: 0.77, blue: 0.75, alpha: 1.0)
        static let textPrimary = UIColor(red: 0.2, green: 0.2, blue: 0.2, alpha: 1.0)
        static let textSecondary = UIColor(red: 0.4, green: 0.4, blue: 0.4, alpha: 1.0)
        static let textTertiary = UIColor(red: 0.6, green: 0.6, blue: 0.6, alpha: 1.0)
        static let divider = UIColor(red: 0.9, green: 0.9, blue: 0.9, alpha: 1.0)
        static let cardBackground = UIColor(red: 0.97, green: 0.97, blue: 0.98, alpha: 1.0)
        static let riskLow = UIColor(red: 0.30, green: 0.72, blue: 0.52, alpha: 1.0)
        static let riskMedium = UIColor(red: 1.0, green: 0.70, blue: 0.24, alpha: 1.0)
        static let riskHigh = UIColor(red: 0.94, green: 0.33, blue: 0.31, alpha: 1.0)
    }
    
    // MARK: - Generate PDF
    func generatePDF(event: MedicalEvent, config: ExportConfig, userInfo: ExportUserInfo?) -> Data {
        let pdfConfig = PDFConfig()
        let renderer = UIGraphicsPDFRenderer(bounds: CGRect(origin: .zero, size: pdfConfig.pageSize))
        
        let data = renderer.pdfData { context in
            var currentY: CGFloat = 0
            var pageNumber = 1
            let totalPages = calculateTotalPages(event: event, config: config, pdfConfig: pdfConfig)
            
            // Page 1
            context.beginPage()
            currentY = pdfConfig.margin.top
            
            currentY = drawHeader(context: context.cgContext, config: pdfConfig, y: currentY)
            currentY += 20
            
            if let userInfo = userInfo {
                currentY = drawPatientInfo(context: context.cgContext, config: pdfConfig, userInfo: userInfo, y: currentY)
                currentY += 16
            }
            
            currentY = drawEventSummary(context: context.cgContext, config: pdfConfig, event: event, y: currentY)
            currentY += 16
            
            if config.includeAIAnalysis, let analysis = event.aiAnalysis {
                currentY = drawAIAnalysis(context: context.cgContext, config: pdfConfig, analysis: analysis, y: currentY)
            }
            
            drawFooter(context: context.cgContext, config: pdfConfig, pageNumber: pageNumber, totalPages: totalPages)
            
            // Page 2 (if needed)
            if config.includeAttachments && !event.attachments.isEmpty {
                context.beginPage()
                pageNumber += 1
                currentY = pdfConfig.margin.top
                
                currentY = drawHeader(context: context.cgContext, config: pdfConfig, y: currentY)
                currentY += 20
                
                currentY = drawAttachments(context: context.cgContext, config: pdfConfig, attachments: event.attachments, y: currentY)
                currentY += 16
                
                if config.includeDialogueSummary {
                    currentY = drawConversationSummary(context: context.cgContext, config: pdfConfig, sessions: event.sessions, y: currentY)
                }
                
                drawFooter(context: context.cgContext, config: pdfConfig, pageNumber: pageNumber, totalPages: totalPages)
            }
        }
        
        return data
    }
    
    private func calculateTotalPages(event: MedicalEvent, config: ExportConfig, pdfConfig: PDFConfig) -> Int {
        var pages = 1
        if config.includeAttachments && !event.attachments.isEmpty {
            pages += 1
        }
        return pages
    }
    
    // MARK: - Draw Header
    private func drawHeader(context: CGContext, config: PDFConfig, y: CGFloat) -> CGFloat {
        var currentY = y
        
        // Logo placeholder
        let logoRect = CGRect(x: config.margin.left, y: currentY, width: 30, height: 30)
        context.setFillColor(Colors.teal.cgColor)
        context.fillEllipse(in: logoRect)
        
        // Draw cross in logo
        context.setStrokeColor(UIColor.white.cgColor)
        context.setLineWidth(2)
        context.move(to: CGPoint(x: logoRect.midX, y: logoRect.minY + 8))
        context.addLine(to: CGPoint(x: logoRect.midX, y: logoRect.maxY - 8))
        context.move(to: CGPoint(x: logoRect.minX + 8, y: logoRect.midY))
        context.addLine(to: CGPoint(x: logoRect.maxX - 8, y: logoRect.midY))
        context.strokePath()
        
        // Title
        let title = "鑫琳医生 - AI 辅助病历"
        let titleAttributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.headerTitle(),
            .foregroundColor: Colors.textPrimary
        ]
        let titleRect = CGRect(x: config.margin.left + 40, y: currentY + 5, width: config.contentWidth - 40, height: 24)
        title.draw(in: titleRect, withAttributes: titleAttributes)
        
        // Generation time
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm"
        let timeText = "生成时间: \(dateFormatter.string(from: Date()))"
        let timeAttributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.headerSubtitle(),
            .foregroundColor: Colors.textSecondary
        ]
        let timeRect = CGRect(x: config.margin.left + 40, y: currentY + 28, width: config.contentWidth - 40, height: 16)
        timeText.draw(in: timeRect, withAttributes: timeAttributes)
        
        currentY += 50
        
        // Divider
        context.setStrokeColor(Colors.divider.cgColor)
        context.setLineWidth(1)
        context.move(to: CGPoint(x: config.margin.left, y: currentY))
        context.addLine(to: CGPoint(x: config.pageSize.width - config.margin.right, y: currentY))
        context.strokePath()
        
        return currentY + 10
    }
    
    // MARK: - Draw Patient Info
    private func drawPatientInfo(context: CGContext, config: PDFConfig, userInfo: ExportUserInfo, y: CGFloat) -> CGFloat {
        var currentY = y
        
        // Section title
        currentY = drawSectionTitle(context: context, config: config, title: "患者基本信息", y: currentY)
        currentY += 8
        
        // Info row
        var infoText = ""
        if let name = userInfo.name, !name.isEmpty {
            infoText += "姓名: \(name)    "
        }
        if let gender = userInfo.gender, !gender.isEmpty {
            infoText += "性别: \(gender)    "
        }
        if let age = userInfo.age {
            infoText += "年龄: \(age)岁    "
        }
        if let phone = userInfo.phone, !phone.isEmpty {
            infoText += "手机: \(phone)"
        }
        
        if !infoText.isEmpty {
            let infoAttributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.textPrimary
            ]
            let infoRect = CGRect(x: config.margin.left, y: currentY, width: config.contentWidth, height: 18)
            infoText.draw(in: infoRect, withAttributes: infoAttributes)
            currentY += 24
        }
        
        return currentY
    }
    
    // MARK: - Draw Event Summary
    private func drawEventSummary(context: CGContext, config: PDFConfig, event: MedicalEvent, y: CGFloat) -> CGFloat {
        var currentY = y
        
        currentY = drawSectionTitle(context: context, config: config, title: "事件概要", y: currentY)
        currentY += 8
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        
        let summaryItems = [
            ("科室", event.department.displayName),
            ("就诊时间", "\(dateFormatter.string(from: event.createdAt)) ~ \(dateFormatter.string(from: event.updatedAt))"),
            ("主诉", event.aiAnalysis?.chiefComplaint ?? event.summary),
            ("风险等级", event.riskLevel.displayName)
        ]
        
        for (label, value) in summaryItems {
            let labelAttributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.label(),
                .foregroundColor: Colors.textSecondary
            ]
            let valueAttributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.textPrimary
            ]
            
            let labelText = "\(label): "
            let labelSize = labelText.size(withAttributes: labelAttributes)
            
            let labelRect = CGRect(x: config.margin.left, y: currentY, width: labelSize.width, height: 18)
            labelText.draw(in: labelRect, withAttributes: labelAttributes)
            
            let valueRect = CGRect(x: config.margin.left + labelSize.width, y: currentY, width: config.contentWidth - labelSize.width, height: 18)
            value.draw(in: valueRect, withAttributes: valueAttributes)
            
            currentY += 20
        }
        
        return currentY
    }
    
    // MARK: - Draw AI Analysis
    private func drawAIAnalysis(context: CGContext, config: PDFConfig, analysis: AIAnalysis, y: CGFloat) -> CGFloat {
        var currentY = y
        
        currentY = drawSectionTitle(context: context, config: config, title: "AI 分析结果", y: currentY)
        currentY += 12
        
        // Symptoms
        currentY = drawSubsectionTitle(context: context, config: config, title: "【症状列表】", y: currentY)
        for symptom in analysis.symptoms {
            let bulletText = "• \(symptom)"
            let attributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.textPrimary
            ]
            let rect = CGRect(x: config.margin.left + 10, y: currentY, width: config.contentWidth - 10, height: 18)
            bulletText.draw(in: rect, withAttributes: attributes)
            currentY += 18
        }
        currentY += 8
        
        // Diagnosis
        currentY = drawSubsectionTitle(context: context, config: config, title: "【可能诊断】", y: currentY)
        for diagnosis in analysis.possibleDiagnosis {
            let percentage = Int(diagnosis.confidence * 100)
            let diagnosisText = "\(diagnosis.name): \(percentage)%"
            let attributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.textPrimary
            ]
            let rect = CGRect(x: config.margin.left + 10, y: currentY, width: config.contentWidth - 10, height: 18)
            diagnosisText.draw(in: rect, withAttributes: attributes)
            
            // Progress bar
            let barY = currentY + 18
            let barWidth = config.contentWidth - 20
            let filledWidth = barWidth * diagnosis.confidence
            
            context.setFillColor(Colors.divider.cgColor)
            context.fill(CGRect(x: config.margin.left + 10, y: barY, width: barWidth, height: 6))
            
            let barColor = diagnosis.confidence >= 0.7 ? Colors.riskHigh : (diagnosis.confidence >= 0.4 ? Colors.riskMedium : Colors.riskLow)
            context.setFillColor(barColor.cgColor)
            context.fill(CGRect(x: config.margin.left + 10, y: barY, width: filledWidth, height: 6))
            
            currentY += 30
        }
        currentY += 8
        
        // Recommendations
        currentY = drawSubsectionTitle(context: context, config: config, title: "【处理建议】", y: currentY)
        for (index, recommendation) in analysis.recommendations.enumerated() {
            let recText = "\(index + 1). \(recommendation)"
            let attributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.textPrimary
            ]
            let rect = CGRect(x: config.margin.left + 10, y: currentY, width: config.contentWidth - 10, height: 18)
            recText.draw(in: rect, withAttributes: attributes)
            currentY += 18
        }
        currentY += 8
        
        // Visit urgency
        if analysis.needOfflineVisit, let urgency = analysis.visitUrgency {
            currentY = drawSubsectionTitle(context: context, config: config, title: "【就医建议】", y: currentY)
            let warningText = "⚠️ \(urgency)"
            let attributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.body(),
                .foregroundColor: Colors.riskMedium
            ]
            let rect = CGRect(x: config.margin.left + 10, y: currentY, width: config.contentWidth - 10, height: 18)
            warningText.draw(in: rect, withAttributes: attributes)
            currentY += 24
        }
        
        return currentY
    }
    
    // MARK: - Draw Attachments
    private func drawAttachments(context: CGContext, config: PDFConfig, attachments: [Attachment], y: CGFloat) -> CGFloat {
        var currentY = y
        
        currentY = drawSectionTitle(context: context, config: config, title: "附件图片", y: currentY)
        currentY += 12
        
        let imageSize: CGFloat = 100
        let spacing: CGFloat = 10
        let imagesPerRow = Int((config.contentWidth + spacing) / (imageSize + spacing))
        
        var col = 0
        for attachment in attachments where attachment.type == .image {
            let x = config.margin.left + CGFloat(col) * (imageSize + spacing)
            let rect = CGRect(x: x, y: currentY, width: imageSize, height: imageSize)
            
            // Placeholder
            context.setFillColor(Colors.cardBackground.cgColor)
            context.fill(rect)
            
            context.setStrokeColor(Colors.divider.cgColor)
            context.setLineWidth(1)
            context.stroke(rect)
            
            // Icon
            let iconText = "📷"
            let iconAttributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 24)
            ]
            let iconSize = iconText.size(withAttributes: iconAttributes)
            let iconRect = CGRect(x: rect.midX - iconSize.width/2, y: rect.midY - iconSize.height/2, width: iconSize.width, height: iconSize.height)
            iconText.draw(in: iconRect, withAttributes: iconAttributes)
            
            // Date label
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "MM-dd"
            let dateText = dateFormatter.string(from: attachment.createdAt)
            let dateAttributes: [NSAttributedString.Key: Any] = [
                .font: Fonts.disclaimer(),
                .foregroundColor: Colors.textTertiary
            ]
            let dateRect = CGRect(x: rect.minX + 4, y: rect.maxY - 16, width: imageSize - 8, height: 14)
            dateText.draw(in: dateRect, withAttributes: dateAttributes)
            
            col += 1
            if col >= imagesPerRow {
                col = 0
                currentY += imageSize + spacing
            }
        }
        
        if col > 0 {
            currentY += imageSize + spacing
        }
        
        return currentY
    }
    
    // MARK: - Draw Conversation Summary
    private func drawConversationSummary(context: CGContext, config: PDFConfig, sessions: [SessionRecord], y: CGFloat) -> CGFloat {
        var currentY = y
        
        currentY = drawSectionTitle(context: context, config: config, title: "对话摘要", y: currentY)
        currentY += 8
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "MM-dd HH:mm"
        
        for session in sessions {
            for message in session.messages.prefix(10) {
                let role = message.role == .user ? "患者" : "AI"
                let preview = String(message.content.prefix(40)) + (message.content.count > 40 ? "..." : "")
                let text = "• \(dateFormatter.string(from: message.timestamp)) \(role): \(preview)"
                
                let attributes: [NSAttributedString.Key: Any] = [
                    .font: Fonts.label(),
                    .foregroundColor: Colors.textSecondary
                ]
                let rect = CGRect(x: config.margin.left, y: currentY, width: config.contentWidth, height: 16)
                text.draw(in: rect, withAttributes: attributes)
                currentY += 18
            }
        }
        
        return currentY
    }
    
    // MARK: - Draw Footer
    private func drawFooter(context: CGContext, config: PDFConfig, pageNumber: Int, totalPages: Int) {
        let footerY = config.pageSize.height - config.margin.bottom + 10
        
        // Divider
        context.setStrokeColor(Colors.divider.cgColor)
        context.setLineWidth(1)
        context.move(to: CGPoint(x: config.margin.left, y: footerY - 10))
        context.addLine(to: CGPoint(x: config.pageSize.width - config.margin.right, y: footerY - 10))
        context.strokePath()
        
        // Disclaimer
        let disclaimerText = "⚠️ 免责声明：本报告由 AI 辅助生成，仅供参考，不构成医疗诊断建议。具体诊疗请遵医嘱。"
        let disclaimerAttributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.disclaimer(),
            .foregroundColor: Colors.textTertiary
        ]
        let disclaimerRect = CGRect(x: config.margin.left, y: footerY, width: config.contentWidth, height: 30)
        disclaimerText.draw(in: disclaimerRect, withAttributes: disclaimerAttributes)
        
        // Page number
        let pageText = "第 \(pageNumber) 页 / 共 \(totalPages) 页"
        let pageAttributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.disclaimer(),
            .foregroundColor: Colors.textTertiary
        ]
        let pageSize = pageText.size(withAttributes: pageAttributes)
        let pageRect = CGRect(x: config.pageSize.width - config.margin.right - pageSize.width, y: footerY + 16, width: pageSize.width, height: 14)
        pageText.draw(in: pageRect, withAttributes: pageAttributes)
    }
    
    // MARK: - Helper Methods
    private func drawSectionTitle(context: CGContext, config: PDFConfig, title: String, y: CGFloat) -> CGFloat {
        let attributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.sectionTitle(),
            .foregroundColor: Colors.textPrimary
        ]
        let rect = CGRect(x: config.margin.left, y: y, width: config.contentWidth, height: 20)
        title.draw(in: rect, withAttributes: attributes)
        
        // Underline
        context.setStrokeColor(Colors.divider.cgColor)
        context.setLineWidth(1)
        context.move(to: CGPoint(x: config.margin.left, y: y + 22))
        context.addLine(to: CGPoint(x: config.pageSize.width - config.margin.right, y: y + 22))
        context.strokePath()
        
        return y + 28
    }
    
    private func drawSubsectionTitle(context: CGContext, config: PDFConfig, title: String, y: CGFloat) -> CGFloat {
        let attributes: [NSAttributedString.Key: Any] = [
            .font: Fonts.body(),
            .foregroundColor: Colors.textSecondary
        ]
        let rect = CGRect(x: config.margin.left, y: y, width: config.contentWidth, height: 18)
        title.draw(in: rect, withAttributes: attributes)
        return y + 20
    }
}
