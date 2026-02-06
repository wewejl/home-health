import SwiftUI
import PhotosUI

// MARK: - 新建病历弹窗

struct CreateRecordSheet: View {
    @ObservedObject var viewModel: MedicalFolderViewModel
    let folders: [MedicalFolder]
    let preselectedFolder: MedicalFolder?

    @Environment(\.dismiss) private var dismiss
    @State private var currentStep = 1
    @State private var selectedFolder: MedicalFolder?
    @State private var title = ""
    @State private var recordDate = Date()
    @State private var description = ""
    @State private var selectedFiles: [URL] = []
    @State private var photoPickerItems: [PhotosPickerItem] = []
    @State private var isCreating = false
    @State private var showFilePicker = false
    @State private var errorMessage: String?

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy年MM月dd日"
        return formatter
    }()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // 进度指示器
                progressIndicator

                ScrollView {
                    VStack(spacing: 24) {
                        switch currentStep {
                        case 1:
                            step1_SelectFolder()
                        case 2:
                            step2_FillInfo()
                        case 3:
                            step3_UploadFiles()
                        default:
                            EmptyView()
                        }
                    }
                    .padding()
                }

                // 底部操作按钮
                actionButtons
            }
            .navigationTitle("新建病历")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
            }
        }
    }

    private var progressIndicator: some View {
        HStack(spacing: 8) {
            ForEach(1...3, id: \.self) { step in
                Circle()
                    .fill(step <= currentStep ? HealingColors.forestMist : HealingColors.textTertiary.opacity(0.3))
                    .frame(width: 8, height: 8)

                if step < 3 {
                    Rectangle()
                        .fill(step < currentStep ? HealingColors.forestMist : HealingColors.textTertiary.opacity(0.3))
                        .frame(height: 2)
                }
            }
        }
        .padding()
    }

    // MARK: - 步骤1: 选择文件夹

    private func step1_SelectFolder() -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("选择文件夹")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            if folders.isEmpty {
                emptyFoldersView
            } else {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    ForEach(folders) { folder in
                        FolderSelectionCard(
                            folder: folder,
                            isSelected: selectedFolder?.id == folder.id
                        ) {
                            selectedFolder = folder
                        }
                    }
                }
            }
        }
    }

    private var emptyFoldersView: some View {
        VStack(spacing: 12) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 40))
                .foregroundColor(HealingColors.textTertiary)

            Text("还没有文件夹")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textSecondary)

            Text("请先创建文件夹来组织病历")
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(HealingColors.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - 步骤2: 填写信息

    private func step2_FillInfo() -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("填写病历信息")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            // 已选文件夹
            if let folder = selectedFolder {
                HStack {
                    Circle()
                        .fill(Color(hex: folder.color))
                        .frame(width: 12, height: 12)
                    Text(folder.name)
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textSecondary)
                    Spacer()
                    Button("更改") {
                        currentStep = 1
                    }
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.forestMist)
                }
                .padding()
                .background(HealingColors.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            // 标题输入
            VStack(alignment: .leading, spacing: 8) {
                Text("标题 *")
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.textSecondary)

                TextField("如：血常规检查", text: $title)
                    .font(.system(size: UnifiedFont.footnote))
                    .padding()
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            // 日期选择
            VStack(alignment: .leading, spacing: 8) {
                Text("记录日期 *")
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.textSecondary)

                DatePicker("", selection: $recordDate, displayedComponents: .date)
                    .datePickerStyle(.compact)
                    .labelsHidden()
            }

            // 描述输入
            VStack(alignment: .leading, spacing: 8) {
                Text("描述")
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.textSecondary)

                TextEditor(text: $description)
                    .font(.system(size: UnifiedFont.footnote))
                    .frame(minHeight: 80)
                    .padding(8)
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(HealingColors.textTertiary.opacity(0.2), lineWidth: 1)
                    )
            }
        }
    }

    // MARK: - 步骤3: 上传文件

    private func step3_UploadFiles() -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("上传文件")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("可以稍后添加文件")
                .font(.system(size: UnifiedFont.caption))
                .foregroundColor(HealingColors.textTertiary)

            // 文件选择按钮
            VStack(spacing: 12) {
                // 图片选择器
                PhotosPicker(
                    selection: $photoPickerItems,
                    maxSelectionCount: 10 - selectedFiles.count,
                    matching: .images
                ) {
                    HStack {
                        Image(systemName: "photo.on.rectangle.angled")
                            .font(.system(size: 20))
                        Text("选择图片")
                            .font(.system(size: UnifiedFont.footnote))
                    }
                    .foregroundColor(HealingColors.forestMist)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .onChange(of: photoPickerItems) { _, newItems in
                    Task {
                        await loadPhotos(from: newItems)
                    }
                }

                // 文档选择器
                Button(action: { showFilePicker = true }) {
                    HStack {
                        Image(systemName: "doc.fill")
                            .font(.system(size: 20))
                        Text("选择文档")
                            .font(.system(size: UnifiedFont.footnote))
                    }
                    .foregroundColor(HealingColors.forestMist)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(HealingColors.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }

            // 已选文件列表
            if !selectedFiles.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("已选择 \(selectedFiles.count) 个文件")
                        .font(.system(size: UnifiedFont.caption))
                        .foregroundColor(HealingColors.textSecondary)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 8) {
                        ForEach(Array(selectedFiles.enumerated()), id: \.offset) { _, fileURL in
                            SelectedFileThumbnail(fileURL: fileURL) {
                                selectedFiles.removeAll { $0 == fileURL }
                            }
                        }
                    }
                }
            }
        }
        .fileImporter(
            isPresented: $showFilePicker,
            allowedContentTypes: [.pdf, .text],
            allowsMultipleSelection: true
        ) { result in
            switch result {
            case .success(let urls):
                selectedFiles.append(contentsOf: urls)
            case .failure(let error):
                print("File import error: \(error)")
            }
        }
    }

    // MARK: - 底部操作按钮

    private var actionButtons: some View {
        HStack(spacing: 12) {
            if currentStep > 1 {
                Button("上一步") {
                    currentStep -= 1
                }
                .buttonStyle(SecondaryButtonStyle())
            }

            Spacer()

            if currentStep < 3 {
                Button("下一步") {
                    currentStep += 1
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(currentStep == 1 && selectedFolder == nil)
            } else {
                Button("完成") {
                    Task {
                        await createRecord()
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(isCreating || title.isEmpty)
            }
        }
        .padding()
    }

    // MARK: - Helper Methods

    private func loadPhotos(from items: [PhotosPickerItem]) async {
        for item in items {
            if let data = try? await item.loadTransferable(type: Data.self) {
                let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".jpg")
                try? data.write(to: tempURL)
                selectedFiles.append(tempURL)
            }
        }
        photoPickerItems.removeAll()
    }

    private func createRecord() async {
        guard let folder = selectedFolder, !title.isEmpty else { return }

        isCreating = true
        errorMessage = nil

        if let record = await viewModel.createRecord(
            folderId: folder.id,
            title: title,
            recordDate: recordDate,
            description: description.isEmpty ? nil : description
        ) {
            // 上传文件
            for fileURL in selectedFiles {
                _ = await viewModel.uploadFileSafely(recordId: record.id, fileURL: fileURL)
            }
            dismiss()
        } else {
            errorMessage = "创建失败，请重试"
        }

        isCreating = false
    }
}

// MARK: - 文件夹选择卡片

struct FolderSelectionCard: View {
    let folder: MedicalFolder
    let isSelected: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(Color(hex: folder.color))
                        .frame(width: 44, height: 44)

                    Image(systemName: folder.iconValue)
                        .font(.system(size: 20))
                        .foregroundColor(.white)
                }

                Text(folder.name)
                    .font(.system(size: UnifiedFont.caption))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineLimit(1)

                Text("\(folder.recordCount) 个病历")
                    .font(.system(size: UnifiedFont.caption2))
                    .foregroundColor(HealingColors.textTertiary)
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(isSelected ? HealingColors.forestMist.opacity(0.15) : HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(isSelected ? Color(hex: folder.color) : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 已选文件缩略图

struct SelectedFileThumbnail: View {
    let fileURL: URL
    var onDelete: () -> Void

    var body: some View {
        ZStack(alignment: .topTrailing) {
            if let image = UIImage(contentsOfFile: fileURL.path) {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 80, height: 80)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            } else {
                RoundedRectangle(cornerRadius: 8)
                    .fill(HealingColors.textTertiary.opacity(0.2))
                    .frame(width: 80, height: 80)
                    .overlay(
                        Image(systemName: "doc.fill")
                            .foregroundColor(HealingColors.textTertiary)
                    )
            }

            Button(action: onDelete) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 18))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.2), radius: 2)
            }
            .offset(x: 8, y: -8)
        }
    }
}

// MARK: - 按钮样式

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundColor(.white)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(
                LinearGradient(
                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(Capsule())
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundColor(HealingColors.textSecondary)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(HealingColors.cardBackground)
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(HealingColors.textTertiary.opacity(0.3), lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

// MARK: - 创建文件夹弹窗

struct CreateFolderSheet: View {
    @ObservedObject var viewModel: MedicalFolderViewModel
    var onCreate: (MedicalFolder) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var description = ""
    @State private var selectedColor = "#7B5FEA"
    @State private var selectedIcon = "folder"
    @State private var isCreating = false

    private let folderColors = ["#7B5FEA", "#FF6B6B", "#4ECDC4", "#95E1D3", "#F38181", "#AA96DA"]

    private var isFormValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("文件夹名称", text: $name)
                        .textFieldStyle(.plain)

                    TextField("描述（可选）", text: $description)
                        .textFieldStyle(.plain)
                }

                Section("颜色") {
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 12) {
                        ForEach(folderColors, id: \.self) { color in
                            Circle()
                                .fill(Color(hex: color))
                                .frame(width: 36, height: 36)
                                .overlay(
                                    Circle()
                                        .stroke(Color.white, lineWidth: 3)
                                        .opacity(selectedColor == color ? 1 : 0)
                                )
                                .onTapGesture {
                                    selectedColor = color
                                }
                        }
                    }
                    .padding(.vertical, 8)
                }
            }
            .navigationTitle("新建文件夹")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("创建") {
                        Task {
                            await createFolder()
                        }
                    }
                    .disabled(!isFormValid || isCreating)
                }
            }
        }
    }

    private func createFolder() async {
        isCreating = true

        if let folder = await viewModel.createFolder(
            name: name.trimmingCharacters(in: .whitespaces),
            description: description.isEmpty ? nil : description.trimmingCharacters(in: .whitespaces),
            color: selectedColor,
            icon: selectedIcon
        ) {
            onCreate(folder)
            dismiss()
        }

        isCreating = false
    }
}

#Preview {
    CreateRecordSheet(
        viewModel: MedicalFolderViewModel(apiService: .shared),
        folders: [],
        preselectedFolder: nil
    )
}
