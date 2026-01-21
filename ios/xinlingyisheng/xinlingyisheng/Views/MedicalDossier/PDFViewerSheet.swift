import SwiftUI
import PDFKit

/// PDF 查看器（用于导出的对话记录）
struct PDFViewerSheet: View {
    let export: ExportedConversation
    @Environment(\.dismiss) var dismiss
    @State private var showShareSheet = false
    @State private var currentPage = 1
    @State private var totalPages = 1
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.opacity(0.05)
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // PDF 内容
                    ExportPDFContentView(url: export.pdfURL)
                        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
                        .shadow(color: Color.black.opacity(0.1), radius: 10, x: 0, y: 4)
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .padding(.top, ScaleFactor.padding(16))
                    
                    // 信息栏
                    infoBar
                    
                    Spacer()
                }
            }
            .navigationTitle(export.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("关闭") {
                        dismiss()
                    }
                    .foregroundColor(DXYColors.primaryPurple)
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
                            .foregroundColor(DXYColors.primaryPurple)
                    }
                }
            }
        }
        .sheet(isPresented: $showShareSheet) {
            ShareSheet(items: [export.pdfURL])
        }
    }
    
    private var infoBar: some View {
        HStack(spacing: ScaleFactor.spacing(16)) {
            Label(export.department, systemImage: "stethoscope")
            
            Text("•")
            
            Label("\(export.messageCount) 条对话", systemImage: "bubble.left.and.bubble.right")
            
            Text("•")
            
            Text(export.formattedFileSize)
        }
        .font(.system(size: AdaptiveFont.footnote))
        .foregroundColor(DXYColors.textSecondary)
        .padding(.vertical, ScaleFactor.padding(12))
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

/// 导出 PDF 内容视图（从 URL 加载）
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
