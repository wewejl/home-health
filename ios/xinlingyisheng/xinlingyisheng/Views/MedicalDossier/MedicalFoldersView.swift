import SwiftUI
import PhotosUI

// MARK: - 病历夹主页（重构版）

struct MedicalFoldersView: View {
    @StateObject private var viewModel = MedicalFolderViewModel(apiService: .shared)
    @State private var selectedRecord: MedicalRecord?
    @State private var showingCreateRecord = false
    @State private var showingCreateFolder = false
    @State private var selectedFolderForRecords: MedicalFolder?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingDossierBackground(layout: layout)

                VStack(spacing: 0) {
                    headerSection(layout: layout)

                    // 文件夹横向滚动列表
                    foldersSection(layout: layout)

                    // 操作按钮
                    actionButtonSection(layout: layout)

                    // 病历记录列表
                    recordsSection(layout: layout)
                }
            }
        }
        .navigationBarHidden(true)
        .sheet(isPresented: $showingCreateFolder) {
            CreateFolderSheet(viewModel: viewModel) { folder in
                // 创建文件夹后选择它
                selectedFolderForRecords = folder
                Task {
                    await viewModel.loadRecords(folderId: folder.id)
                }
            }
        }
        .sheet(isPresented: $showingCreateRecord) {
            CreateRecordSheet(
                viewModel: viewModel,
                folders: viewModel.folders,
                preselectedFolder: selectedFolderForRecords
            )
        }
        .navigationDestinationCompat(item: $selectedRecord) { record in
            RecordDetailView(record: record, viewModel: viewModel)
        }
        .task {
            await viewModel.loadFolders()
            // 加载所有记录（显示"全部"文件夹时）
            await viewModel.loadRecords()

            // 自动选择第一个文件夹
            if let firstFolder = viewModel.folders.first {
                selectedFolderForRecords = firstFolder
            }
        }
    }

    private func headerSection(layout: AdaptiveLayout) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                Text("健康档案")
                    .font(.system(size: UnifiedFont.subheadline, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "folder.fill")
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.forestMist)
                    Text("分类管理，随时查阅")
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textSecondary)
                }
            }

            Spacer()

            Button(action: { showingCreateFolder = true }) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(HealingColors.forestMist)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardInnerPadding)
        .padding(.bottom, layout.cardSpacing + 2)
    }

    private func foldersSection(layout: AdaptiveLayout) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: layout.cardSpacing) {
                // 全部病历选项
                FolderCard(
                    folder: nil,
                    isSelected: selectedFolderForRecords == nil,
                    recordCount: viewModel.records.count,
                    layout: layout
                ) {
                    selectedFolderForRecords = nil
                    Task { await viewModel.loadRecords() }
                }

                ForEach(viewModel.folders) { folder in
                    FolderCard(
                        folder: folder,
                        isSelected: selectedFolderForRecords?.id == folder.id,
                        recordCount: folder.recordCount,
                        layout: layout
                    ) {
                        selectedFolderForRecords = folder
                        Task { await viewModel.loadRecords(folderId: folder.id) }
                    }
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
        }
        .padding(.bottom, layout.cardSpacing)
    }

    private func actionButtonSection(layout: AdaptiveLayout) -> some View {
        Button(action: { showingCreateRecord = true }) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: UnifiedFont.body))
                Text("新建病历")
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, layout.cardInnerPadding * 2)
            .padding(.vertical, layout.cardInnerPadding)
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
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.bottom, layout.cardSpacing)
    }

    @ViewBuilder
    private func recordsSection(layout: AdaptiveLayout) -> some View {
        if viewModel.isLoading {
            HealingDossierLoadingView(layout: layout)
        } else if viewModel.records.isEmpty {
            emptyRecordsView(layout: layout)
        } else {
            recordsListView(layout: layout)
        }
    }

    private func emptyRecordsView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            Spacer()

            ZStack {
                Circle()
                    .fill(HealingColors.textTertiary.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 1.5, height: layout.iconLargeSize * 1.5)

                Image(systemName: selectedFolderForRecords == nil ? "doc.text.fill" : "folder.fill")
                    .font(.system(size: UnifiedFont.body, weight: .light))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Text(selectedFolderForRecords == nil ? "暂无病历记录" : "此文件夹为空")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("点击下方按钮创建新病历")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textSecondary)

            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
    }

    private func recordsListView(layout: AdaptiveLayout) -> some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: layout.cardSpacing) {
                ForEach(viewModel.records) { record in
                    RecordCard(
                        record: record,
                        folder: viewModel.folders.first { $0.id == record.folderId },
                        layout: layout
                    ) {
                        selectedRecord = record
                    }
                }
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.bottom, layout.cardInnerPadding * 2)
        }
    }
}

// MARK: - 文件夹卡片

struct FolderCard: View {
    let folder: MedicalFolder?
    let isSelected: Bool
    let recordCount: Int
    let layout: AdaptiveLayout
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: layout.cardSpacing / 2) {
                ZStack {
                    if let folder = folder {
                        Circle()
                            .fill(Color(hex: folder.color))
                            .frame(width: 44, height: 44)

                        Image(systemName: folder.iconValue)
                            .font(.system(size: 20))
                            .foregroundColor(.white)
                    } else {
                        Circle()
                            .fill(HealingColors.forestMist)
                            .frame(width: 44, height: 44)

                        Image(systemName: "square.grid.2x2.fill")
                            .font(.system(size: 18))
                            .foregroundColor(.white)
                    }
                }

                Text(folder?.name ?? "全部")
                    .font(.system(size: UnifiedFont.caption1, weight: isSelected ? .semibold : .regular))
                    .foregroundColor(isSelected ? HealingColors.forestMist : HealingColors.textSecondary)
                    .lineLimit(1)

                if recordCount > 0 {
                    Text("\(recordCount)")
                        .font(.system(size: UnifiedFont.caption12))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }
            .padding(.horizontal, layout.cardInnerPadding)
            .padding(.vertical, layout.cardInnerPadding)
            .background(isSelected ? HealingColors.forestMist.opacity(0.1) : HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(isSelected ? HealingColors.forestMist : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 病历记录卡片

struct RecordCard: View {
    let record: MedicalRecord
    let folder: MedicalFolder?
    let layout: AdaptiveLayout
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                // 顶部：文件夹标签 + 日期
                HStack {
                    if let folder = folder {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(Color(hex: folder.color))
                                .frame(width: 8, height: 8)
                            Text(folder.name)
                                .font(.system(size: UnifiedFont.caption1))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                    }

                    Spacer()

                    Text(record.recordDateShortText)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textTertiary)
                }

                // 标题
                Text(record.title)
                    .font(.system(size: UnifiedFont.footnote, weight: .medium))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineLimit(2)

                // 描述
                if let description = record.description, !description.isEmpty {
                    Text(description)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textSecondary)
                        .lineLimit(2)
                }

                // 文件缩略图网格
                if record.fileCount > 0 {
                    FileThumbnailGrid(files: record.files ?? [], fileCount: record.fileCount, layout: layout)
                }
            }
            .padding(layout.cardInnerPadding)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: Color.black.opacity(0.03), radius: 4, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 文件缩略图网格

struct FileThumbnailGrid: View {
    let files: [MedicalFile]
    let fileCount: Int
    let layout: AdaptiveLayout

    private var displayFiles: [MedicalFile] {
        Array(files.prefix(4))
    }

    var body: some View {
        HStack(spacing: 4) {
            ForEach(displayFiles) { file in
                FileThumbnail(file: file, size: 40)
            }

            if fileCount > 4 {
                Image(systemName: "ellipsis")
                    .font(.system(size: UnifiedFont.caption1))
                    .foregroundColor(HealingColors.textTertiary)
                    .frame(width: 40, height: 40)
                    .background(HealingColors.textTertiary.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
            }

            Spacer()

            Text("\(fileCount) 个文件")
                .font(.system(size: UnifiedFont.caption12))
                .foregroundColor(HealingColors.textTertiary)
        }
    }
}

// MARK: - 文件缩略图

struct FileThumbnail: View {
    let file: MedicalFile
    let size: CGFloat

    var body: some View {
        if let thumbnailUrl = file.thumbnailUrl, !thumbnailUrl.isEmpty {
            AsyncImage(url: URL(string: APIConfig.baseURL + thumbnailUrl)) { phase in
                switch phase {
                case .success(let image):
                    image.resizable()
                        .aspectRatio(contentMode: .fill)
                case .failure(_):
                    placeholder
                case .empty:
                    placeholder
                @unknown default:
                    placeholder
                }
            }
        } else {
            placeholder
        }
    }

    private var placeholder: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 6)
                .fill(file.fileTypeEnum.color.opacity(0.2))
                .frame(width: size, height: size)

            Image(systemName: file.fileTypeEnum.icon)
                .font(.system(size: size / 2.5))
                .foregroundColor(file.fileTypeEnum.color)
        }
    }
}

#Preview {
    CompatibleNavigationStack {
        MedicalFoldersView()
    }
}
