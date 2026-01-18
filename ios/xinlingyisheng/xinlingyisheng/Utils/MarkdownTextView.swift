import SwiftUI

/// 简单的 Markdown 文本渲染视图
/// 支持基本的 Markdown 格式：标题、加粗、列表等
struct MarkdownTextView: View {
    let content: String
    let fontSize: CGFloat
    let textColor: Color
    
    init(_ content: String, fontSize: CGFloat = 16, textColor: Color = .primary) {
        self.content = content
        self.fontSize = fontSize
        self.textColor = textColor
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(parseMarkdown(content), id: \.id) { element in
                renderElement(element)
            }
        }
    }
    
    private func renderElement(_ element: MarkdownElement) -> some View {
        Group {
            switch element.type {
            case .heading1:
                Text(element.content)
                    .font(.system(size: fontSize + 8, weight: .bold))
                    .foregroundColor(textColor)
                    .padding(.top, 4)
                
            case .heading2:
                Text(element.content)
                    .font(.system(size: fontSize + 6, weight: .bold))
                    .foregroundColor(textColor)
                    .padding(.top, 4)
                
            case .heading3:
                Text(element.content)
                    .font(.system(size: fontSize + 4, weight: .bold))
                    .foregroundColor(textColor)
                    .padding(.top, 4)
                
            case .bold:
                Text(element.content)
                    .font(.system(size: fontSize, weight: .bold))
                    .foregroundColor(textColor)
                
            case .listItem:
                HStack(alignment: .top, spacing: 6) {
                    Text("•")
                        .font(.system(size: fontSize))
                        .foregroundColor(textColor)
                    Text(element.content)
                        .font(.system(size: fontSize))
                        .foregroundColor(textColor)
                }
                
            case .paragraph:
                Text(parseInlineMarkdown(element.content))
                    .font(.system(size: fontSize))
                    .foregroundColor(textColor)
            }
        }
    }
    
    /// 解析 Markdown 为元素列表
    private func parseMarkdown(_ text: String) -> [MarkdownElement] {
        var elements: [MarkdownElement] = []
        let lines = text.components(separatedBy: .newlines)
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            if trimmed.isEmpty {
                continue
            }
            
            // 标题
            if trimmed.hasPrefix("### ") {
                elements.append(MarkdownElement(
                    type: .heading3,
                    content: String(trimmed.dropFirst(4))
                ))
            } else if trimmed.hasPrefix("## ") {
                elements.append(MarkdownElement(
                    type: .heading2,
                    content: String(trimmed.dropFirst(3))
                ))
            } else if trimmed.hasPrefix("# ") {
                elements.append(MarkdownElement(
                    type: .heading1,
                    content: String(trimmed.dropFirst(2))
                ))
            }
            // 列表项
            else if trimmed.hasPrefix("- ") || trimmed.hasPrefix("* ") {
                elements.append(MarkdownElement(
                    type: .listItem,
                    content: String(trimmed.dropFirst(2))
                ))
            }
            // 普通段落
            else {
                elements.append(MarkdownElement(
                    type: .paragraph,
                    content: trimmed
                ))
            }
        }
        
        return elements
    }
    
    /// 解析行内 Markdown（加粗等）
    private func parseInlineMarkdown(_ text: String) -> AttributedString {
        var attributedString = AttributedString(text)
        
        // 移除 ** 加粗标记
        let boldPattern = "\\*\\*(.+?)\\*\\*"
        if let regex = try? NSRegularExpression(pattern: boldPattern) {
            let nsString = text as NSString
            let matches = regex.matches(in: text, range: NSRange(location: 0, length: nsString.length))
            
            for match in matches.reversed() {
                if let range = Range(match.range(at: 1), in: text) {
                    let boldText = String(text[range])
                    if let attrRange = Range(match.range, in: text) {
                        let startIndex = attributedString.index(attributedString.startIndex, offsetByCharacters: attrRange.lowerBound.utf16Offset(in: text))
                        let endIndex = attributedString.index(attributedString.startIndex, offsetByCharacters: attrRange.upperBound.utf16Offset(in: text))
                        
                        if startIndex < endIndex {
                            attributedString.replaceSubrange(startIndex..<endIndex, with: AttributedString(boldText))
                            if let boldRange = attributedString.range(of: boldText) {
                                attributedString[boldRange].font = .systemFont(ofSize: fontSize, weight: .bold)
                            }
                        }
                    }
                }
            }
        }
        
        return attributedString
    }
}

/// Markdown 元素类型
enum MarkdownElementType {
    case heading1
    case heading2
    case heading3
    case bold
    case listItem
    case paragraph
}

/// Markdown 元素
struct MarkdownElement: Identifiable {
    let id = UUID()
    let type: MarkdownElementType
    let content: String
}
