import SwiftUI
import PhotosUI

// MARK: - 简化的任务完成页面

struct SimplifiedTaskCompletionView: View {
    let task: TaskInstance
    let viewModel: MedicalOrderViewModel

    @Environment(\.dismiss) private var dismiss

    @State private var selectedImage: Image? = nil
    @State private var selectedImageItem: PhotosPickerItem? = nil
    @State private var voiceText: String = ""
    @State private var isSubmitting: Bool = false

    @StateObject private var speechService = SimpleSpeechInputService.shared

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 背景
                HealingColors.background
                    .ignoresSafeArea()

                // 顶部装饰
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geometry.size.width * 0.3, y: -geometry.size.height * 0.15)
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: layout.cardSpacing + 4) {
                        // 1. 任务信息卡片
                        taskInfoCard(layout: layout)

                        // 2. 拍照区域（可选）
                        photoProofSection(layout: layout)

                        // 3. 语音描述（必须）
                        voiceDescriptionSection(layout: layout)

                        // 4. 完成按钮
                        completeButton(layout: layout)

                        Spacer(minLength: layout.cardInnerPadding * 4)
                    }
                    .padding(.horizontal, layout.horizontalPadding)
                    .padding(.top, layout.cardSpacing)
                }
            }
        }
        .navigationTitle("完成打卡")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("取消") {
                    dismiss()
                }
                .foregroundColor(HealingColors.forestMist)
            }
        }
        .onChange(of: selectedImageItem) { _, newItem in
            Task { @MainActor in
                if let data = try? await newItem?.loadTransferable(type: Data.self),
                   let uiImage = UIImage(data: data) {
                    selectedImage = Image(uiImage: uiImage)
                }
            }
        }
        .onChange(of: speechService.recognizedText) { _, newText in
            voiceText = newText
        }
    }

    // MARK: - 任务信息卡片

    private func taskInfoCard(layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            // 任务标题
            HStack(spacing: layout.cardSpacing / 2) {
                if let orderType = task.order_type, let type = OrderType(rawValue: orderType) {
                    HStack(spacing: 4) {
                        Image(systemName: type.iconName)
                            .font(.system(size: UnifiedFont.caption1))
                            .foregroundColor(HealingColors.forestMist)
                        Text(type.displayName)
                            .font(.system(size: UnifiedFont.caption1, weight: .medium))
                            .foregroundColor(.white)
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(HealingColors.forestMist.opacity(0.8))
                    .cornerRadius(8)
                }

                Spacer()

                Text(task.scheduled_time)
                    .font(.system(size: UnifiedFont.caption1))
                    .foregroundColor(HealingColors.textTertiary)
            }

            // 任务名称
            Text(task.order_title ?? "未命名任务")
                .font(.system(size: UnifiedFont.subheadline, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)

            // 医嘱内容
            if let description = getTaskDescription() {
                VStack(alignment: .leading, spacing: 4) {
                    Text("医嘱内容")
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textSecondary)

                    Text(description)
                        .font(.system(size: UnifiedFont.body))
                        .foregroundColor(HealingColors.textPrimary)
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .cornerRadius(18)
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }

    // MARK: - 拍照区域（可选）

    private func photoProofSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing / 2) {
            Text("拍照证明（可选）")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textSecondary)

            if let image = selectedImage {
                // 已选照片预览
                ZStack(alignment: .topTrailing) {
                    image
                        .resizable()
                        .scaledToFill()
                        .frame(height: 180)
                        .cornerRadius(16)
                        .clipped()

                    Button(action: {
                        selectedImage = nil
                        selectedImageItem = nil
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: UnifiedFont.title3))
                            .foregroundColor(.white)
                            .padding(6)
                            .background(Circle().fill(HealingColors.terracotta))
                    }
                    .padding(8)
                }
            } else {
                // 拍照按钮
                PhotosPicker(selection: $selectedImageItem, matching: .images) {
                    VStack(spacing: layout.cardSpacing / 2) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 16)
                                .fill(HealingColors.dustyBlue.opacity(0.08))
                                .frame(height: 120)

                            VStack(spacing: layout.cardSpacing / 2) {
                                Image(systemName: "camera.fill")
                                    .font(.system(size: UnifiedFont.title3))
                                    .foregroundColor(HealingColors.dustyBlue.opacity(0.5))

                                Text("点击拍照或选择照片")
                                    .font(.system(size: UnifiedFont.caption1))
                                    .foregroundColor(HealingColors.textSecondary)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(HealingColors.textTertiary.opacity(0.1), lineWidth: 1)
        )
    }

    // MARK: - 语音描述（必须）

    private func voiceDescriptionSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing / 2) {
            HStack(spacing: 6) {
                Image(systemName: "mic.circle.fill")
                    .font(.system(size: UnifiedFont.subheadline))
                Text("症状/状态描述（必填）")
                    .font(.system(size: UnifiedFont.body, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 录音按钮
            Button {
                Task {
                    if speechService.isRecording {
                        speechService.stopRecording()
                    } else {
                        await speechService.startRecording()
                    }
                }
            } label: {
                HStack {
                    Image(systemName: speechService.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                        .font(.system(size: UnifiedFont.title3))
                    Text(speechService.isRecording ? "松开结束" : "按住说话")
                        .font(.system(size: UnifiedFont.body, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardInnerPadding - 2)
                .frame(maxWidth: .infinity)
                .background(speechService.isRecording ? HealingColors.terracotta : HealingColors.forestMist)
                .cornerRadius(12)
            }

            // 转文字结果
            if !voiceText.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("已转文字：")
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textSecondary)

                    Text(voiceText)
                        .font(.system(size: UnifiedFont.body))
                        .foregroundColor(HealingColors.textPrimary)
                        .padding(layout.cardInnerPadding - 4)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(HealingColors.warmSand.opacity(0.3))
                        .cornerRadius(10)
                }
            }

            // 备注输入
            TextField("也可以手动输入补充说明...", text: $voiceText, axis: .vertical)
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textPrimary)
                .padding(.horizontal, layout.cardInnerPadding - 4)
                .padding(.vertical, layout.cardInnerPadding - 4)
                .background(HealingColors.background)
                .cornerRadius(10)
                .lineLimit(2...4)
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .cornerRadius(18)
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(HealingColors.textTertiary.opacity(0.1), lineWidth: 1)
        )
    }

    // MARK: - 完成按钮

    private func completeButton(layout: AdaptiveLayout) -> some View {
        Button {
            submitCompletion()
        } label: {
            HStack {
                if isSubmitting {
                    ProgressView()
                        .tint(.white)
                } else {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: UnifiedFont.subheadline))
                    Text("完成任务")
                        .font(.system(size: UnifiedFont.body, weight: .semibold))
                }
            }
            .foregroundColor(.white)
            .padding(.vertical, layout.cardInnerPadding + 2)
            .frame(maxWidth: .infinity)
            .background(
                LinearGradient(
                    colors: voiceText.isEmpty
                        ? [HealingColors.textTertiary, HealingColors.textTertiary]
                        : [HealingColors.forestMist, HealingColors.deepSage],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(14)
            .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 8, y: 4)
        }
        .disabled(isSubmitting || voiceText.isEmpty)
    }

    // MARK: - Helper Methods

    private func getTaskDescription() -> String? {
        // 任务描述目前没有直接字段，可以从 order_title 推断
        // 实际医嘱内容需要从关联的 MedicalOrder 获取
        return nil
    }

    private func submitCompletion() {
        Task { @MainActor in
            isSubmitting = true

            let success = await viewModel.completeTask(
                taskId: task.id,
                type: voiceText.isEmpty ? .check : .photo,
                value: nil,
                photoURL: nil,
                notes: voiceText.isEmpty ? nil : voiceText
            )

            isSubmitting = false

            if success {
                dismiss()
            }
        }
    }
}

// MARK: - Preview

#Preview {
    CompatibleNavigationStack {
        SimplifiedTaskCompletionView(
            task: TaskInstance(
                id: 1,
                order_id: 1,
                patient_id: 1,
                scheduled_date: "2026-02-07",
                scheduled_time: "08:00",
                status: "pending",
                order_title: "擦碘伏",
                order_type: "medication"
            ),
            viewModel: MedicalOrderViewModel()
        )
    }
}
