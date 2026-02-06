import SwiftUI
import QuickLook

// MARK: - 病历详情视图

struct RecordDetailView: View {
    let record: MedicalRecord
    @ObservedObject var viewModel: MedicalFolderViewModel

    @Environment(\.dismiss) private var dismiss
    @State private var detailRecord: MedicalRecord
    @State private var showingFilePicker = false
    @State private var selectedFileForPreview: MedicalFile?
    @State private var isLoadingDetail = false

    init(record: MedicalRecord, viewModel: MedicalFolderViewModel) {
        self.record = record
        self.viewModel = viewModel
        self._detailRecord = State(initialValue: record)
    }

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ScrollView {
                VStack(alignment: .leading, spacing: layout.cardSpacing) {
                    // 标题和日期
                    headerSection(layout: layout)

                    // 文件网格
                    if let files = detailRecord.files, !files.isEmpty {
                        fileGridSection(layout: layout)
                    } else {
                        emptyFilesSection(layout: layout)
                    }

                    // 描述
                    if let description = detailRecord.description, !description.isEmpty {
                        descriptionSection(layout: layout)
                    }

                    // 底部操作按钮
                    actionButtonsSection(layout: layout)
                }
                .padding(.horizontal, layout.horizontalPadding)
                .padding(.top, layout.cardInnerPadding)
                .padding(.bottom, layout.cardInnerPadding * 3)
            }
            .background(HealingColors.background.ignoresSafeArea())
        }
        .navigationBarHidden(true)
        .task {
            await loadRecordDetail()
        }
        .sheet(item: $selectedFileForPreview) { file in
            FilePreviewSheet(file: file)
        }
    }

    private func loadRecordDetail() async {
        isLoadingDetail = true
        if let detail = await viewModel.loadRecordDetail(record) {
            detailRecord = detail
        }
        isLoadingDetail = false
    }

    private func headerSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(detailRecord.title)
                        .font(.system(size: UnifiedFont.body, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text(detailRecord.recordDateText)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textTertiary)
                }

                Spacer()

                Button(action: {
                    Task {
                        await viewModel.deleteRecord(detailRecord)
                        dismiss()
                    }
                }) {
                    Image(systemName: "trash")
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textTertiary)
                        .padding(8)
                        .background(HealingColors.textTertiary.opacity(0.1))
                        .clipShape(Circle())
                }
            }
        }
    }

    private func fileGridSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            HStack {
                Text("附件")
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
                    .foregroundColor(HealingColors.textSecondary)

                Spacer()

                Text("\(detailRecord.fileCount) 个文件")
                    .font(.system(size: UnifiedFont.caption1))
                    .foregroundColor(HealingColors.textTertiary)
            }

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(detailRecord.files ?? []) { file in
                    FileGridItem(file: file, layout: layout) {
                        selectedFileForPreview = file
                    }
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private func emptyFilesSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: 60, height: 60)

                Image(systemName: "doc.bubble.fill")
                    .font(.system(size: 24))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text("暂无附件")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textSecondary)

            Text("可以添加图片、PDF等文件")
                .font(.system(size: UnifiedFont.caption1))
                .foregroundColor(HealingColors.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 30)
        .background(HealingColors.cardBackground.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private func descriptionSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            Text("描述")
                .font(.system(size: UnifiedFont.footnote, weight: .medium))
                .foregroundColor(HealingColors.textSecondary)

            Text(detailRecord.description ?? "")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(4)
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private func actionButtonsSection(layout: AdaptiveLayout) -> some View {
        Button(action: { showingFilePicker = true }) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: UnifiedFont.body))
                Text("添加文件")
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, layout.cardInnerPadding * 2)
            .padding(.vertical, layout.cardInnerPadding)
            .frame(maxWidth: .infinity)
            .background(
                LinearGradient(
                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(Capsule())
            .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 2)
        }
        .fileImporter(
            isPresented: $showingFilePicker,
            allowedContentTypes: [.image, .pdf, .text],
            allowsMultipleSelection: true
        ) { result in
            handleFileSelection(result)
        }
    }

    private func handleFileSelection(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            Task {
                for url in urls {
                    _ = await viewModel.uploadFileSafely(recordId: detailRecord.id, fileURL: url)
                }
                await loadRecordDetail()
            }
        case .failure(let error):
            print("File selection error: \(error)")
        }
    }
}

// MARK: - 文件网格项

struct FileGridItem: View {
    let file: MedicalFile
    let layout: AdaptiveLayout
    var onTap: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 6) {
                // 缩略图/图标
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(file.fileTypeEnum.color.opacity(0.15))
                        .frame(height: 80)

                    if let thumbnailUrl = file.thumbnailUrl, !thumbnailUrl.isEmpty {
                        AsyncImage(url: URL(string: APIConfig.baseURL + thumbnailUrl)) { phase in
                            switch phase {
                            case .success(let image):
                                image.resizable()
                                    .aspectRatio(contentMode: .fill)
                            case .failure(_), .empty:
                                placeholder
                            @unknown default:
                                placeholder
                            }
                        }
                        .frame(height: 80)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    } else {
                        placeholder
                    }
                }

                // 文件名
                Text(file.filename)
                    .font(.system(size: UnifiedFont.caption12))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineLimit(2)
                    .frame(height: 32)

                // 文件大小
                Text(file.formattedSize)
                    .font(.system(size: 10))
                    .foregroundColor(HealingColors.textTertiary)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var placeholder: some View {
        Image(systemName: file.fileTypeEnum.icon)
            .font(.system(size: 28))
            .foregroundColor(file.fileTypeEnum.color)
    }
}

// MARK: - 文件预览

struct FilePreviewSheet: UIViewControllerRepresentable {
    let file: MedicalFile

    func makeUIViewController(context: Context) -> QLPreviewController {
        let controller = QLPreviewController()
        controller.dataSource = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: QLPreviewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(file: file)
    }

    class Coordinator: NSObject, QLPreviewControllerDataSource {
        let file: MedicalFile

        init(file: MedicalFile) {
            self.file = file
        }

        func numberOfPreviewItems(in controller: QLPreviewController) -> Int {
            1
        }

        func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem {
            // 构建文件URL
            let fileURL = URL(string: APIConfig.baseURL + file.url)!
            return PreviewItem(url: fileURL, title: file.filename)
        }
    }

    class PreviewItem: NSObject, QLPreviewItem {
        var previewItemURL: URL?
        var previewItemTitle: String?

        init(url: URL, title: String) {
            self.previewItemURL = url
            self.previewItemTitle = title
        }
    }
}

#Preview {
    NavigationStack {
        RecordDetailView(
            record: MedicalRecord(
                id: UUID().uuidString,
                folderId: UUID().uuidString,
                userId: 1,
                title: "血常规检查",
                recordDate: Date(),
                description: "年度体检血常规检查结果",
                fileCount: 3
            ),
            viewModel: MedicalFolderViewModel(apiService: .shared)
        )
    }
}
