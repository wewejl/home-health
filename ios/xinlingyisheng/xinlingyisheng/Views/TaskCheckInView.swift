import SwiftUI
import PhotosUI

// MARK: - 任务打卡视图（治愈系风格）

struct TaskCheckInView: View {
    let task: TaskInstance
    let viewModel: MedicalOrderViewModel

    @Environment(\.dismiss) private var dismiss
    @State private var isLoading: Bool = false
    @State private var selectedType: CompletionType = .check
    @State private var notes: String = ""
    @State private var valueInput: String = ""
    @State private var selectedImage: [PhotosPickerItem] = []
    @State private var inputImage: Image?

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 背景
                HealingColors.warmCream
                    .ignoresSafeArea()

                // 顶部装饰
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geometry.size.width * 0.3, y: -geometry.size.height * 0.15)
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: layout.cardSpacing) {
                        // 任务信息卡片
                        healingTaskInfoSection(layout: layout)

                        // 打卡类型选择
                        healingCompletionTypeSection(layout: layout)

                        // 动态输入区域
                        healingDynamicInputSection(layout: layout)

                        // 备注输入
                        healingNotesSection(layout: layout)

                        // 提交按钮
                        healingSubmitButton(layout: layout)
                    }
                    .padding(.horizontal, layout.horizontalPadding)
                    .padding(.top, layout.cardSpacing)
                    .padding(.bottom, layout.cardInnerPadding * 6)
                }
            }
            .navigationTitle("任务打卡")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundColor(HealingColors.forestMist)
                }
            }
        }
    }

    // MARK: - 治愈系任务信息

    private func healingTaskInfoSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            // 任务类型标签
            HStack(spacing: layout.cardSpacing / 2) {
                if let orderType = task.order_type, let type = OrderType(rawValue: orderType) {
                    HStack(spacing: 4) {
                        Image(systemName: type.iconName)
                            .font(.system(size: layout.captionFontSize))

                        Text(type.displayName)
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, layout.cardInnerPadding)
                    .padding(.vertical, 6)
                    .background(
                        Capsule()
                            .fill(HealingColors.forestMist)
                    )
                }

                Spacer()

                // 计划时间
                HStack(spacing: 4) {
                    Image(systemName: "clock.fill")
                        .font(.system(size: layout.captionFontSize - 1))
                    Text(task.scheduled_time)
                        .font(.system(size: layout.captionFontSize + 1))
                }
                .foregroundColor(HealingColors.textSecondary)
            }

            // 任务标题
            Text(task.order_title ?? "未命名任务")
                .font(.system(size: layout.bodyFontSize + 4, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(4)

            // 鼓励语
            HStack(spacing: 6) {
                Image(systemName: "heart.fill")
                    .font(.system(size: layout.captionFontSize))
                Text("按时完成，守护健康")
                    .font(.system(size: layout.captionFontSize))
            }
            .foregroundColor(HealingColors.forestMist.opacity(0.8))
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        )
    }

    // MARK: - 治愈系打卡类型选择

    private func healingCompletionTypeSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            Text("选择打卡方式")
                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            HStack(spacing: layout.cardSpacing / 2) {
                ForEach([CompletionType.check, .photo, .value, .medication], id: \.self) { type in
                    Button {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                            selectedType = type
                        }
                    } label: {
                        VStack(spacing: layout.cardSpacing / 3) {
                            ZStack {
                                Circle()
                                    .fill(selectedType == type ? HealingColors.forestMist.opacity(0.2) : HealingColors.warmSand.opacity(0.3))
                                    .frame(width: layout.iconLargeSize, height: layout.iconLargeSize)

                                Image(systemName: typeIcon(type))
                                    .font(.system(size: layout.captionFontSize + 2))
                                    .foregroundColor(selectedType == type ? HealingColors.forestMist : HealingColors.textSecondary)
                            }

                            Text(type.displayName)
                                .font(.system(size: layout.captionFontSize, weight: selectedType == type ? .semibold : .regular))
                                .foregroundColor(selectedType == type ? HealingColors.forestMist : HealingColors.textSecondary)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
        )
    }

    // MARK: - 治愈系动态输入区域

    @ViewBuilder
    private func healingDynamicInputSection(layout: AdaptiveLayout) -> some View {
        switch selectedType {
        case .check:
            healingCheckInputSection(layout: layout)
        case .photo:
            healingPhotoInputSection(layout: layout)
        case .value:
            healingValueInputSection(layout: layout)
        case .medication:
            healingMedicationInputSection(layout: layout)
        }
    }

    // MARK: - 打卡确认

    private func healingCheckInputSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: 6) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("确认完成")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
            }
            .foregroundColor(HealingColors.forestMist)

            // 鼓励语
            Text("完成打卡后，医生可以看到您的执行情况")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)

            // 按钮组
            HStack(spacing: layout.cardSpacing / 2) {
                Button("已完成") {
                    submitCompletion(type: .check)
                }
                .healingPrimaryButton(layout: layout, color: HealingColors.forestMist)

                Button("无法完成") {
                    notes = "因特殊原因无法完成"
                    submitCompletion(type: .check)
                }
                .healingSecondaryButton(layout: layout, color: HealingColors.terracotta)
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 3)
        )
    }

    // MARK: - 照片输入

    private func healingPhotoInputSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            HStack(spacing: 6) {
                Image(systemName: "camera.fill")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("拍照上传")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
            }
            .foregroundColor(HealingColors.dustyBlue)

            if let image = inputImage {
                ZStack(alignment: .topTrailing) {
                    image
                        .resizable()
                        .scaledToFit()
                        .frame(height: 200)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                    Button(action: {
                        selectedImage = []
                        inputImage = nil
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: layout.captionFontSize + 4))
                            .foregroundColor(.white)
                            .padding(6)
                            .background(Circle().fill(HealingColors.terracotta))
                    }
                    .padding(8)
                }
            } else {
                // 上传占位
                VStack(spacing: layout.cardSpacing) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .fill(HealingColors.dustyBlue.opacity(0.08))
                            .frame(height: 160)

                        VStack(spacing: layout.cardSpacing / 2) {
                            Image(systemName: "photo.on.rectangle.angled")
                                .font(.system(size: layout.titleFontSize))
                                .foregroundColor(HealingColors.dustyBlue.opacity(0.5))

                            Text("点击下方按钮选择照片")
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                    }

                    PhotosPicker("选择照片", selection: $selectedImage, matching: .images)
                        .photosPickerStyle(.inline)
                        .onChange(of: selectedImage) { _, newValue in
                            Task { @MainActor in
                                if let item = newValue.first,
                                   let data = try? await item.loadTransferable(type: Data.self),
                                   let uiImage = UIImage(data: data) {
                                    inputImage = Image(uiImage: uiImage)
                                }
                            }
                        }
                }
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 3)
        )
    }

    // MARK: - 数值输入

    private func healingValueInputSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            HStack(spacing: 6) {
                Image(systemName: "number")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("记录数值")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
            }
            .foregroundColor(HealingColors.warmSand)

            TextField("输入数值，如血糖 7.8", text: $valueInput)
                .font(.system(size: layout.bodyFontSize))
                .foregroundColor(HealingColors.textPrimary)
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding - 2)
                .background(HealingColors.warmCream.opacity(0.5))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .keyboardType(.decimalPad)

            if let orderType = task.order_type {
                valueTypeHint(for: orderType, layout: layout)
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 3)
        )
    }

    // MARK: - 用药记录

    private func healingMedicationInputSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            HStack(spacing: 6) {
                Image(systemName: "pills.fill")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("用药记录")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
            }
            .foregroundColor(HealingColors.forestMist)

            // 提示
            Text("请根据医嘱按时服药，记录您的服药情况")
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textSecondary)

            // 按钮组
            HStack(spacing: layout.cardSpacing / 2) {
                Button("已服用") {
                    notes = "按医嘱已服用"
                    submitCompletion(type: .medication)
                }
                .healingPrimaryButton(layout: layout, color: HealingColors.forestMist)

                Button("未服用") {
                    notes = "因特殊原因未服用"
                    submitCompletion(type: .medication)
                }
                .healingSecondaryButton(layout: layout, color: HealingColors.terracotta)
            }
        }
        .padding(layout.cardInnerPadding + 4)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 3)
        )
    }

    // MARK: - 备注输入

    private func healingNotesSection(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            HStack(spacing: 6) {
                Image(systemName: "text.bubble")
                    .font(.system(size: layout.captionFontSize + 2))
                Text("备注（可选）")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
            }
            .foregroundColor(HealingColors.textSecondary)

            TextField("输入备注信息...", text: $notes, axis: .vertical)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding - 2)
                .background(HealingColors.warmCream.opacity(0.5))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .lineLimit(3...6)
        }
    }

    // MARK: - 提交按钮

    private func healingSubmitButton(layout: AdaptiveLayout) -> some View {
        Button {
            submitCompletion()
        } label: {
            HStack(spacing: layout.cardSpacing / 2) {
                if isLoading {
                    ProgressView()
                        .tint(.white)
                        .progressViewStyle(CircularProgressViewStyle())
                } else {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: layout.captionFontSize + 2))

                    Text("提交打卡")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                }
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, layout.cardInnerPadding + 4)
            .background(
                LinearGradient(
                    colors: [HealingColors.deepSage, HealingColors.forestMist],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(Capsule())
            .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 8, x: 0, y: 4)
        }
        .disabled(isLoading)
    }

    // MARK: - Helper Methods

    private func typeIcon(_ type: CompletionType) -> String {
        switch type {
        case .check: return "checkmark.circle.fill"
        case .photo: return "camera.fill"
        case .value: return "number.circle.fill"
        case .medication: return "pills.fill"
        }
    }

    private func valueTypeHint(for orderType: String, layout: AdaptiveLayout) -> some View {
        let hint: String
        switch orderType {
        case "monitoring":
            hint = "请输入您的监测值，如血糖、血压等"
        default:
            hint = "请输入相关数值"
        }

        return HStack(spacing: 4) {
            Image(systemName: "info.circle")
                .font(.system(size: layout.captionFontSize - 1))
            Text(hint)
                .font(.system(size: layout.captionFontSize))
        }
        .foregroundColor(HealingColors.textTertiary)
    }

    private func submitCompletion(type: CompletionType? = nil) {
        Task { @MainActor in
            isLoading = true

            var valueData: [String: String]?
            let photoURL: String? = nil

            switch type ?? selectedType {
            case .value:
                if !valueInput.isEmpty {
                    valueData = ["value": valueInput, "unit": "mmol/L"]
                }
            case .photo:
                // TODO: Upload image and get URL
                break
            default:
                break
            }

            let success = await viewModel.completeTask(
                taskId: task.id,
                type: type ?? selectedType,
                value: valueData,
                photoURL: photoURL,
                notes: notes.isEmpty ? nil : notes
            )

            isLoading = false

            if success {
                dismiss()
            }
        }
    }
}

// MARK: - 按钮样式扩展

extension View {
    func healingPrimaryButton(layout: AdaptiveLayout, color: Color) -> some View {
        self
            .font(.system(size: layout.captionFontSize + 1, weight: .semibold))
            .foregroundColor(.white)
            .padding(.horizontal, layout.cardInnerPadding + 4)
            .padding(.vertical, layout.cardInnerPadding)
            .frame(maxWidth: .infinity)
            .background(
                LinearGradient(
                    colors: [color, color.opacity(0.8)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(Capsule())
    }

    func healingSecondaryButton(layout: AdaptiveLayout, color: Color) -> some View {
        self
            .font(.system(size: layout.captionFontSize + 1, weight: .medium))
            .foregroundColor(color)
            .padding(.horizontal, layout.cardInnerPadding + 4)
            .padding(.vertical, layout.cardInnerPadding)
            .frame(maxWidth: .infinity)
            .background(
                Capsule()
                    .fill(color.opacity(0.15))
            )
    }
}

// MARK: - Preview

#Preview {
    CompatibleNavigationStack {
        TaskCheckInView(
            task: TaskInstance(
                id: 1,
                order_id: 1,
                patient_id: 1,
                scheduled_date: "2024-01-23",
                scheduled_time: "08:00",
                status: "pending",
                order_title: "早餐前注射胰岛素",
                order_type: "medication"
            ),
            viewModel: MedicalOrderViewModel()
        )
    }
}
