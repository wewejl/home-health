import SwiftUI
import PDFKit

// MARK: - PDF 查看器面板（治愈系风格）
struct PDFViewerSheet: View {
    let export: ExportedConversation
    @Environment(\.dismiss) var dismiss
    @State private var showShareSheet = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingPDFViewerBackground(layout: layout)

                VStack(spacing: 0) {
                    // PDF 内容
                    ExportPDFContentView(url: export.pdfURL)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 4)
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.top, layout.cardInnerPadding)

                    // 信息栏
                    HealingPDFViewerInfoBar(
                        export: export,
                        layout: layout
                    )

                    Spacer()
                }
            }
            .navigationTitle(export.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { dismiss() }) {
                        Text("关闭")
                            .font(.system(size: layout.bodyFontSize - 1))
                            .foregroundColor(HealingColors.forestMist)
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
                        ZStack {
                            Circle()
                                .fill(HealingColors.forestMist.opacity(0.15))
                                .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                            Image(systemName: "ellipsis.circle")
                                .font(.system(size: 12))
                                .foregroundColor(HealingColors.forestMist)
                        }
                    }
                }
            }
            .sheet(isPresented: $showShareSheet) {
                ShareSheet(items: [export.pdfURL])
            }
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

// MARK: - 治愈系 PDF 查看器背景
struct HealingPDFViewerBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 淡色背景
            HealingColors.warmCream
                .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.05))
                    .frame(width: layout.decorativeCircleSize * 0.6, height: layout.decorativeCircleSize * 0.6)
                    .offset(x: geo.size.width * 0.5, y: -geo.size.height * 0.2)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.03))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: -geo.size.width * 0.5, y: geo.size.height * 0.3)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系 PDF 查看器信息栏
struct HealingPDFViewerInfoBar: View {
    let export: ExportedConversation
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 科室标签
            HStack(spacing: 4) {
                ZStack {
                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.15))
                        .frame(width: layout.captionFontSize + 6, height: layout.captionFontSize + 6)

                    Image(systemName: "stethoscope")
                        .font(.system(size: 8))
                        .foregroundColor(HealingColors.forestMist)
                }

                Text(export.department)
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 分隔符
            Text("·")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textTertiary)

            // 消息数量
            HStack(spacing: 4) {
                ZStack {
                    Circle()
                        .fill(HealingColors.dustyBlue.opacity(0.15))
                        .frame(width: layout.captionFontSize + 6, height: layout.captionFontSize + 6)

                    Image(systemName: "bubble.left.and.bubble.right")
                        .font(.system(size: 8))
                        .foregroundColor(HealingColors.dustyBlue)
                }

                Text("\(export.messageCount) 条对话")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 分隔符
            Text("·")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textTertiary)

            // 文件大小
            Text(export.formattedFileSize)
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textSecondary)
        }
        .padding(.horizontal, layout.cardInnerPadding)
        .padding(.vertical, layout.cardSpacing)
        .background(HealingColors.cardBackground.opacity(0.9))
        .clipShape(Capsule())
        .padding(.bottom, layout.cardSpacing)
    }
}

// MARK: - 导出 PDF 内容视图（从 URL 加载）
struct ExportPDFContentView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = true
        pdfView.displayMode = .singlePageContinuous
        pdfView.displayDirection = .vertical
        pdfView.backgroundColor = .clear

        if let document = PDFDocument(url: url) {
            pdfView.document = document
        }

        return pdfView
    }

    func updateUIView(_ uiView: PDFView, context: Context) {
        // 不需要更新
    }
}
