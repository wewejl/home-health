import SwiftUI
import PDFKit

// MARK: - PDF 预览视图（治愈系风格）
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
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingPDFPreviewBackground(layout: layout)

                VStack(spacing: 0) {
                    // PDF 查看器
                    HealingPDFViewer(
                        pdfData: pdfData,
                        currentPage: $currentPage,
                        totalPages: $totalPages,
                        layout: layout
                    )

                    // 页码指示器
                    HealingPDFPageIndicator(
                        currentPage: currentPage,
                        totalPages: totalPages,
                        layout: layout
                    ) {
                        if currentPage > 1 { currentPage -= 1 }
                    } onNext: {
                        if currentPage < totalPages { currentPage += 1 }
                    }

                    // 操作按钮
                    HealingPDFActionButtons(
                        isSaving: isSaving,
                        layout: layout
                    ) {
                        savePDF()
                    } onShare: {
                        showShareSheet = true
                    }
                }
            }
            .navigationTitle("PDF 预览")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { dismiss() }) {
                        Text("返回")
                            .font(.system(size: layout.bodyFontSize - 1))
                            .foregroundColor(HealingColors.forestMist)
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showShareSheet = true }) {
                        ZStack {
                            Circle()
                                .fill(HealingColors.forestMist.opacity(0.15))
                                .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                            Image(systemName: "square.and.arrow.up")
                                .font(.system(size: 14))
                                .foregroundColor(HealingColors.forestMist)
                        }
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

// MARK: - 治愈系 PDF 预览背景
struct HealingPDFPreviewBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 淡灰色背景，让 PDF 更突出
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

// MARK: - 治愈系 PDF 查看器
struct HealingPDFViewer: View {
    let pdfData: Data
    @Binding var currentPage: Int
    @Binding var totalPages: Int
    let layout: AdaptiveLayout

    var body: some View {
        PDFKitView(data: pdfData, currentPage: $currentPage, totalPages: $totalPages)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 4)
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.top, layout.cardInnerPadding)
    }
}

// MARK: - 治愈系页码指示器
struct HealingPDFPageIndicator: View {
    let currentPage: Int
    let totalPages: Int
    let layout: AdaptiveLayout
    let onPrevious: () -> Void
    let onNext: () -> Void

    var body: some View {
        HStack(spacing: layout.cardSpacing) {
            // 上一页按钮
            Button(action: onPrevious) {
                ZStack {
                    Circle()
                        .fill(currentPage > 1 ?
                                HealingColors.forestMist.opacity(0.15) :
                                HealingColors.textTertiary.opacity(0.08))
                        .frame(width: layout.iconSmallSize + 14, height: layout.iconSmallSize + 14)

                    Image(systemName: "chevron.left")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(currentPage > 1 ? HealingColors.forestMist : HealingColors.textTertiary)
                }
            }
            .disabled(currentPage <= 1)

            // 页码显示
            HStack(spacing: layout.cardSpacing / 3) {
                Text("\(currentPage)")
                    .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                    .foregroundColor(HealingColors.forestMist)

                Text("/")
                    .font(.system(size: layout.bodyFontSize))
                    .foregroundColor(HealingColors.textTertiary)

                Text("\(totalPages)")
                    .font(.system(size: layout.bodyFontSize + 2, weight: .semibold))
                    .foregroundColor(HealingColors.forestMist)
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardSpacing / 2)
            .background(HealingColors.cardBackground)
            .clipShape(Capsule())

            // 下一页按钮
            Button(action: onNext) {
                ZStack {
                    Circle()
                        .fill(currentPage < totalPages ?
                                HealingColors.forestMist.opacity(0.15) :
                                HealingColors.textTertiary.opacity(0.08))
                        .frame(width: layout.iconSmallSize + 14, height: layout.iconSmallSize + 14)

                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(currentPage < totalPages ? HealingColors.forestMist : HealingColors.textTertiary)
                }
            }
            .disabled(currentPage >= totalPages)
        }
        .padding(.vertical, layout.cardSpacing)
    }
}

// MARK: - 治愈系操作按钮
struct HealingPDFActionButtons: View {
    let isSaving: Bool
    let layout: AdaptiveLayout
    let onSave: () -> Void
    let onShare: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)

            HStack(spacing: layout.cardSpacing) {
                // 保存按钮
                Button(action: onSave) {
                    HStack(spacing: layout.cardSpacing / 2) {
                        if isSaving {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: HealingColors.forestMist))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "square.and.arrow.down")
                                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                        }
                        Text("保存")
                            .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    }
                    .foregroundColor(HealingColors.forestMist)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .stroke(HealingColors.forestMist.opacity(0.5), lineWidth: 1.5)
                    )
                }
                .disabled(isSaving)

                // 分享按钮
                Button(action: onShare) {
                    HStack(spacing: layout.cardSpacing / 2) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: layout.bodyFontSize, weight: .semibold))
                        Text("分享给医生")
                            .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.forestMist, HealingColors.deepSage],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 2)
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing)
            .background(HealingColors.cardBackground.opacity(0.9))
        }
    }
}

// MARK: - PDFKit 包装器
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

// MARK: - 分享面板
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

    NavigationView {
        PDFPreviewView(
            pdfData: mockData,
            event: mockEvent
        )
    }
}
