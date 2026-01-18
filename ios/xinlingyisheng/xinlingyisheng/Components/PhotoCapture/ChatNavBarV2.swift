import SwiftUI

// MARK: - 重构版导航栏 V2
/// 符合设计规范的导航栏，移除了AI诊室入口
/// 保留核心功能：返回、医生信息、病历生成、更多菜单
struct ChatNavBarV2: View {
    let doctorName: String
    let department: String?
    let dismiss: DismissAction
    var onGenerateDossier: (() -> Void)? = nil
    var canGenerateDossier: Bool = true  // 控制按钮是否可用
    var dossierButtonTooltip: String = "根据本次对话生成结构化病历"  // 按钮提示
    var onViewDossier: (() -> Void)? = nil
    var onShareConversation: (() -> Void)? = nil
    var onClearConversation: (() -> Void)? = nil
    
    @State private var showMenu = false
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 返回按钮
            backButton
            
            // 医生信息
            doctorInfo
            
            Spacer()
            
            // 右侧工具按钮
            rightToolButtons
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DXYColors.cardBackground)
    }
    
    // MARK: - 返回按钮
    private var backButton: some View {
        Button(action: { dismiss() }) {
            Image(systemName: "chevron.left")
                .font(.system(size: AdaptiveFont.title3, weight: .medium))
                .foregroundColor(DXYColors.textPrimary)
                .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                .contentShape(Rectangle())
        }
    }
    
    // MARK: - 医生信息
    private var doctorInfo: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            // 头像
            Circle()
                .fill(DXYColors.primaryPurple.opacity(0.2))
                .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))
                .overlay(
                    Image(systemName: "person.fill")
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.primaryPurple)
                )
            
            // 名称和标签
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                Text("\(doctorName)医生")
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                    .lineLimit(1)
                
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Image(systemName: "cpu")
                        .font(.system(size: ScaleFactor.size(10)))
                    Text("AI分身")
                        .font(.system(size: AdaptiveFont.caption))
                }
                .foregroundColor(DXYColors.primaryPurple)
            }
        }
        .frame(maxWidth: ScaleFactor.size(140), alignment: .leading)
    }
    
    // MARK: - 右侧工具按钮
    private var rightToolButtons: some View {
        HStack(spacing: ScaleFactor.spacing(16)) {
            // 生成病历按钮（仅当有回调时显示）
            if let onGenerate = onGenerateDossier {
                Button(action: {
                    onGenerate()
                }) {
                    Image(systemName: "doc.text.fill")
                        .font(.system(size: AdaptiveFont.title3))
                        .foregroundColor(canGenerateDossier ? DXYColors.primaryPurple : DXYColors.textTertiary)
                        .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                        .contentShape(Rectangle())
                }
                .disabled(!canGenerateDossier)
                .opacity(canGenerateDossier ? 1.0 : 0.5)
                .accessibilityLabel("生成病历")
                .accessibilityHint(dossierButtonTooltip)
            }
            
            // 更多菜单
            Menu {
                if let onViewDossier = onViewDossier {
                    Button(action: onViewDossier) {
                        Label("查看病历", systemImage: "folder.fill")
                    }
                }
                
                if let onShare = onShareConversation {
                    Button(action: onShare) {
                        Label("分享对话", systemImage: "square.and.arrow.up")
                    }
                }
                
                if let onClear = onClearConversation {
                    Button(role: .destructive, action: onClear) {
                        Label("清空对话", systemImage: "trash")
                    }
                }
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.system(size: AdaptiveFont.title3))
                    .foregroundColor(DXYColors.textSecondary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("更多选项")
        }
    }
}

// MARK: - 简化版导航栏（仅返回和标题）
struct SimpleChatNavBar: View {
    let title: String
    let subtitle: String?
    let dismiss: DismissAction
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 返回按钮
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
            }
            
            // 标题
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                Text(title)
                    .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                
                if let subtitle = subtitle {
                    Text(subtitle)
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(DXYColors.textSecondary)
                }
            }
            
            Spacer()
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
        .background(DXYColors.cardBackground)
    }
}

// MARK: - 透明导航栏（用于相机等全屏界面）
struct TransparentNavBar: View {
    let dismiss: DismissAction
    var rightButton: (() -> AnyView)? = nil
    
    var body: some View {
        HStack {
            // 关闭按钮
            Button(action: { dismiss() }) {
                Image(systemName: "xmark")
                    .font(.system(size: ScaleFactor.size(20), weight: .medium))
                    .foregroundColor(.white)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .background(Color.black.opacity(0.5))
                    .clipShape(Circle())
            }
            
            Spacer()
            
            // 右侧按钮（可选）
            if let rightButtonView = rightButton {
                rightButtonView()
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.top, ScaleFactor.padding(8))
    }
}

// MARK: - 病历生成确认弹窗
struct DossierGenerationAlert: View {
    @Binding var isPresented: Bool
    var onGenerate: () -> Void
    var onCancel: () -> Void = {}
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(20)) {
            // 图标
            ZStack {
                Circle()
                    .fill(DXYColors.primaryPurple.opacity(0.15))
                    .frame(width: ScaleFactor.size(64), height: ScaleFactor.size(64))
                
                Image(systemName: "doc.text.fill")
                    .font(.system(size: ScaleFactor.size(28)))
                    .foregroundColor(DXYColors.primaryPurple)
            }
            
            // 标题
            Text("是否生成本次问诊病历？")
                .font(.system(size: AdaptiveFont.title2, weight: .semibold))
                .foregroundColor(DXYColors.textPrimary)
            
            // 描述
            Text("系统将根据本次对话内容自动生成结构化病历，方便您后续查看和管理。")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textSecondary)
                .multilineTextAlignment(.center)
                .lineSpacing(ScaleFactor.spacing(4))
            
            // 按钮组
            HStack(spacing: ScaleFactor.spacing(12)) {
                // 稍后再说
                Button(action: {
                    isPresented = false
                    onCancel()
                }) {
                    Text("稍后再说")
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, ScaleFactor.padding(14))
                        .background(DXYColors.tagBackground)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
                }
                
                // 立即生成
                Button(action: {
                    isPresented = false
                    onGenerate()
                }) {
                    Text("立即生成")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, ScaleFactor.padding(14))
                        .background(DXYColors.primaryPurple)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
                }
            }
        }
        .padding(ScaleFactor.padding(24))
        .background(DXYColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(20)))
        .shadow(color: Color.black.opacity(0.15), radius: 20, x: 0, y: 10)
        .padding(.horizontal, ScaleFactor.padding(32))
    }
}

// MARK: - 病历生成确认弹窗容器
struct DossierGenerationAlertContainer: View {
    @Binding var isPresented: Bool
    var onGenerate: () -> Void
    var onCancel: () -> Void = {}
    
    var body: some View {
        ZStack {
            if isPresented {
                // 背景遮罩
                Color.black.opacity(0.4)
                    .ignoresSafeArea()
                    .onTapGesture {
                        withAnimation(.easeOut(duration: 0.2)) {
                            isPresented = false
                        }
                    }
                    .transition(.opacity)
                
                // 弹窗
                DossierGenerationAlert(
                    isPresented: $isPresented,
                    onGenerate: onGenerate,
                    onCancel: onCancel
                )
                .transition(.scale(scale: 0.9).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.35, dampingFraction: 0.8), value: isPresented)
    }
}

// MARK: - Preview
#Preview {
    struct PreviewWrapper: View {
        @Environment(\.dismiss) var dismiss
        
        var body: some View {
            VStack(spacing: 20) {
                // V2导航栏
                ChatNavBarV2(
                    doctorName: "张医生",
                    department: "皮肤科",
                    dismiss: dismiss,
                    onGenerateDossier: { print("Generate") },
                    onViewDossier: { print("View") },
                    onShareConversation: { print("Share") },
                    onClearConversation: { print("Clear") }
                )
                
                Divider()
                
                // 简化导航栏
                SimpleChatNavBar(
                    title: "照片预览",
                    subtitle: "支持双指缩放",
                    dismiss: dismiss
                )
                
                Spacer()
                
                // 病历生成弹窗
                DossierGenerationAlert(
                    isPresented: .constant(true),
                    onGenerate: { print("Generate") }
                )
            }
            .background(Color.gray.opacity(0.1))
        }
    }
    
    return NavigationView {
        PreviewWrapper()
    }
}
