import SwiftUI

struct NoteEditorView: View {
    let eventId: String
    let initialContent: String
    @ObservedObject var viewModel: MedicalDossierViewModel
    let onSave: () -> Void

    @State private var content: String
    @State private var isImportant: Bool
    @Environment(\.dismiss) private var dismiss

    init(eventId: String, initialContent: String, viewModel: MedicalDossierViewModel, onSave: @escaping () -> Void) {
        self.eventId = eventId
        self.initialContent = initialContent
        self.viewModel = viewModel
        self.onSave = onSave
        self._content = State(initialValue: initialContent)
        self._isImportant = State(initialValue: false)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                ScrollView {
                    VStack(alignment: .leading, spacing: ScaleFactor.spacing(20)) {
                        // 说明文字
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(spacing: 6) {
                                Image(systemName: "note.text")
                                    .font(.system(size: AdaptiveFont.body))
                                    .foregroundColor(DXYColors.primaryPurple)
                                Text("病历备注")
                                    .font(.system(size: AdaptiveFont.title3, weight: .bold))
                                    .foregroundColor(DXYColors.textPrimary)
                            }

                            Text("添加您的个人备注、医嘱提醒或其他重要信息。")
                                .font(.system(size: AdaptiveFont.subheadline))
                                .foregroundColor(DXYColors.textSecondary)
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .padding(.top, ScaleFactor.padding(16))

                        // 文本编辑区
                        VStack(alignment: .leading, spacing: 8) {
                            Text("备注内容")
                                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                                .foregroundColor(DXYColors.textTertiary)

                            ZStack(alignment: .topLeading) {
                                if content.isEmpty {
                                    Text("输入备注内容...")
                                        .font(.system(size: AdaptiveFont.body))
                                        .foregroundColor(DXYColors.textTertiary)
                                        .padding(ScaleFactor.padding(12))
                                }

                                TextEditor(text: $content)
                                    .font(.system(size: AdaptiveFont.body))
                                    .foregroundColor(DXYColors.textPrimary)
                                    .padding(ScaleFactor.padding(8))
                                    .scrollContentBackground(.hidden)
                                    .background(Color.clear)
                            }
                            .frame(minHeight: ScaleFactor.size(150))
                            .padding(ScaleFactor.padding(4))
                            .background(DXYColors.background)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                        // 重要标记
                        Button(action: {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                isImportant.toggle()
                            }
                        }) {
                            HStack(spacing: ScaleFactor.spacing(12)) {
                                Image(systemName: isImportant ? "star.fill" : "star")
                                    .font(.system(size: AdaptiveFont.body))
                                    .foregroundColor(isImportant ? Color.orange : DXYColors.textTertiary)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text("标记为重要")
                                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                                        .foregroundColor(DXYColors.textPrimary)

                                    Text("重要备注会在列表中突出显示")
                                        .font(.system(size: AdaptiveFont.footnote))
                                        .foregroundColor(DXYColors.textSecondary)
                                }

                                Spacer()

                                if isImportant {
                                    Image(systemName: "checkmark")
                                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                                        .foregroundColor(DXYColors.primaryPurple)
                                }
                            }
                            .padding(ScaleFactor.padding(12))
                            .background(isImportant ? Color.orange.opacity(0.05) : DXYColors.background)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(isImportant ? Color.orange.opacity(0.3) : Color.clear, lineWidth: 1)
                            )
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)
                        .buttonStyle(PlainButtonStyle())

                        // 快捷输入模板
                        VStack(alignment: .leading, spacing: 8) {
                            Text("快捷输入")
                                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                                .foregroundColor(DXYColors.textTertiary)

                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible())
                            ], spacing: ScaleFactor.spacing(8)) {
                                QuickInputButton(title: "复诊提醒", icon: "calendar") {
                                    insertTemplate("复诊时间：\n医生：\n注意事项：")
                                }

                                QuickInputButton(title: "用药说明", icon: "pills") {
                                    insertTemplate("药品名称：\n用法用量：\n注意事项：")
                                }

                                QuickInputButton(title: "检查项目", icon: "stethoscope") {
                                    insertTemplate("检查项目：\n检查时间：\n注意事项：")
                                }

                                QuickInputButton(title: "生活习惯", icon: "heart") {
                                    insertTemplate("饮食注意：\n运动建议：\n其他注意事项：")
                                }
                            }
                        }
                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                        Spacer(minLength: 100)
                    }
                }

                // 底部按钮
                VStack(spacing: 0) {
                    Divider()

                    HStack(spacing: ScaleFactor.spacing(12)) {
                        Button(action: {
                            if !initialContent.isEmpty && content.isEmpty {
                                // 如果删除了原有内容，确认删除
                                Task {
                                    if await viewModel.deleteNote(for: eventId, noteId: "0") {
                                        dismiss()
                                    }
                                }
                            } else {
                                dismiss()
                            }
                        }) {
                            Text(initialContent.isEmpty ? "取消" : "删除")
                                .font(.system(size: AdaptiveFont.body, weight: .medium))
                                .foregroundColor(initialContent.isEmpty ? DXYColors.textSecondary : .red)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, ScaleFactor.padding(14))
                                .background(DXYColors.background)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }

                        Button(action: {
                            Task {
                                let success = await viewModel.saveNote(for: eventId, content: content, isImportant: isImportant)
                                if success {
                                    onSave()
                                    dismiss()
                                }
                            }
                        }) {
                            HStack(spacing: 6) {
                                if viewModel.isSavingNote {
                                    ProgressView()
                                        .tint(.white)
                                        .scaleEffect(0.8)
                                } else {
                                    Image(systemName: "checkmark")
                                }
                                Text("保存")
                            }
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, ScaleFactor.padding(14))
                            .background(content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? DXYColors.textTertiary : DXYColors.primaryPurple)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .disabled(content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSavingNote)
                    }
                    .padding(.horizontal, LayoutConstants.horizontalPadding)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(Color.white)
                }
            }
            .background(DXYColors.background)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(DXYColors.textTertiary)
                    }
                }
            }
        }
    }

    private func insertTemplate(_ template: String) {
        if content.isEmpty {
            content = template
        } else {
            content += "\n\n" + template
        }
    }
}

// MARK: - Quick Input Button
struct QuickInputButton: View {
    let title: String
    let icon: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.title3))
                    .foregroundColor(DXYColors.primaryPurple)

                Text(title)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textPrimary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, ScaleFactor.padding(12))
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(DXYColors.primaryPurple.opacity(0.2), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    let mockEvent = MedicalEvent(
        title: "皮肤红疹",
        department: .dermatology,
        summary: "过敏性皮炎"
    )

    return NoteEditorView(
        eventId: mockEvent.id,
        initialContent: "这是一条已有的备注内容。",
        viewModel: MedicalDossierViewModel(),
        onSave: {}
    )
}
