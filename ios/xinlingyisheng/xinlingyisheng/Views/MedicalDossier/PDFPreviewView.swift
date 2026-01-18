import SwiftUI
import PDFKit

struct PDFPreviewView: View {
    let pdfData: Data
    let event: MedicalEvent
    var onExportSuccess: (() -> Void)?
    
    @State private var currentPage = 1
    @State private var totalPages = 1
    @State private var showShareSheet = false
    @State private var showSaveSuccess = false
    @State private var isSaving = false
    
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.opacity(0.05)
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    pdfViewer
                    
                    pageIndicator
                    
                    actionButtons
                }
            }
            .navigationTitle("PDF 预览")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("返回") {
                        dismiss()
                    }
                    .foregroundColor(DXYColors.primaryPurple)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showShareSheet = true }) {
                        Image(systemName: "square.and.arrow.up")
                            .foregroundColor(DXYColors.primaryPurple)
                    }
                }
            }
            .sheet(isPresented: $showShareSheet) {
                ShareSheet(items: [pdfData])
            }
            .alert("保存成功", isPresented: $showSaveSuccess) {
                Button("确定", role: .cancel) {
                    onExportSuccess?()
                    dismiss()
                }
            } message: {
                Text("病历 PDF 已保存到文件")
            }
        }
    }
    
    private var pdfViewer: some View {
        PDFKitView(data: pdfData, currentPage: $currentPage, totalPages: $totalPages)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
            .shadow(color: Color.black.opacity(0.1), radius: 10, x: 0, y: 4)
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.top, ScaleFactor.padding(16))
    }
    
    private var pageIndicator: some View {
        HStack(spacing: ScaleFactor.spacing(16)) {
            Button(action: previousPage) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(currentPage > 1 ? DXYColors.primaryPurple : DXYColors.textTertiary)
            }
            .disabled(currentPage <= 1)
            
            Text("\(currentPage) / \(totalPages)")
                .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                .foregroundColor(DXYColors.textSecondary)
            
            Button(action: nextPage) {
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(currentPage < totalPages ? DXYColors.primaryPurple : DXYColors.textTertiary)
            }
            .disabled(currentPage >= totalPages)
        }
        .padding(.vertical, ScaleFactor.padding(12))
    }
    
    private var actionButtons: some View {
        VStack(spacing: 0) {
            Divider()
            
            HStack(spacing: ScaleFactor.spacing(12)) {
                Button(action: savePDF) {
                    HStack(spacing: ScaleFactor.spacing(8)) {
                        if isSaving {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: DXYColors.primaryPurple))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "square.and.arrow.down")
                                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        }
                        Text("保存")
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    }
                    .foregroundColor(DXYColors.primaryPurple)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(14))
                    .background(Color.white)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous)
                            .stroke(DXYColors.primaryPurple, lineWidth: 1.5)
                    )
                }
                .disabled(isSaving)
                
                Button(action: { showShareSheet = true }) {
                    HStack(spacing: ScaleFactor.spacing(8)) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        Text("分享给医生")
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(14))
                    .background(DXYColors.primaryPurple)
                    .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.vertical, ScaleFactor.padding(12))
            .background(Color.white)
        }
    }
    
    private func previousPage() {
        if currentPage > 1 {
            currentPage -= 1
        }
    }
    
    private func nextPage() {
        if currentPage < totalPages {
            currentPage += 1
        }
    }
    
    private func savePDF() {
        isSaving = true
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyyMMdd_HHmmss"
        let fileName = "病历_\(event.title)_\(dateFormatter.string(from: Date())).pdf"
        
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
        
        do {
            try pdfData.write(to: tempURL)
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                isSaving = false
                showSaveSuccess = true
            }
        } catch {
            isSaving = false
        }
    }
}

struct PDFKitView: UIViewRepresentable {
    let data: Data
    @Binding var currentPage: Int
    @Binding var totalPages: Int
    
    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = true
        pdfView.displayMode = .singlePage
        pdfView.displayDirection = .horizontal
        pdfView.backgroundColor = .clear
        
        if let document = PDFDocument(data: data) {
            pdfView.document = document
            DispatchQueue.main.async {
                totalPages = document.pageCount
            }
        }
        
        NotificationCenter.default.addObserver(
            forName: .PDFViewPageChanged,
            object: pdfView,
            queue: .main
        ) { _ in
            if let currentPDFPage = pdfView.currentPage,
               let document = pdfView.document {
                let pageIndex = document.index(for: currentPDFPage)
                DispatchQueue.main.async {
                    currentPage = pageIndex + 1
                }
            }
        }
        
        return pdfView
    }
    
    func updateUIView(_ pdfView: PDFView, context: Context) {
        if let document = pdfView.document,
           currentPage >= 1 && currentPage <= document.pageCount,
           let page = document.page(at: currentPage - 1) {
            if pdfView.currentPage != page {
                pdfView.go(to: page)
            }
        }
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: items, applicationActivities: nil)
        return controller
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

#Preview {
    let mockEvent = MedicalEvent(
        title: "皮肤红疹",
        department: .dermatology,
        status: .inProgress,
        summary: "测试",
        riskLevel: .medium as DossierRiskLevel
    )
    let mockData = PDFGenerator.shared.generatePDF(
        event: mockEvent,
        config: ExportConfig(),
        userInfo: ExportUserInfo(name: "张三", gender: "男", age: 35, phone: nil)
    )
    
    PDFPreviewView(
        pdfData: mockData,
        event: mockEvent
    )
}
