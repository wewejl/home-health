import SwiftUI

// MARK: - 图片预览界面
/// 符合设计规范的图片预览界面，支持缩放、添加备注、重拍和确认
struct PhotoPreviewView: View {
    let image: UIImage
    @Environment(\.dismiss) private var dismiss
    
    @State private var note: String = ""
    @State private var isUploading = false
    @State private var scale: CGFloat = 1.0
    @State private var lastScale: CGFloat = 1.0
    
    var onRetake: () -> Void
    var onConfirm: (UIImage, String) -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            // 图片预览区域（支持缩放）
            GeometryReader { geometry in
                ScrollView([.horizontal, .vertical], showsIndicators: false) {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .frame(width: geometry.size.width * scale)
                        .scaleEffect(scale)
                        .gesture(
                            MagnificationGesture()
                                .onChanged { value in
                                    let delta = value / lastScale
                                    lastScale = value
                                    scale = min(max(scale * delta, 1.0), 4.0)
                                }
                                .onEnded { _ in
                                    lastScale = 1.0
                                }
                        )
                        .gesture(
                            TapGesture(count: 2)
                                .onEnded {
                                    withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                                        scale = scale > 1.5 ? 1.0 : 2.5
                                    }
                                }
                        )
                }
                .frame(width: geometry.size.width, height: geometry.size.height)
            }
            .background(Color.black)
            
            // 底部操作区域
            VStack(spacing: 0) {
                // 备注输入区
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
                    Text("添加备注（可选）")
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.textSecondary)
                    
                    TextField("描述症状、持续时间等...", text: $note)
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.textPrimary)
                        .padding(.horizontal, ScaleFactor.padding(16))
                        .padding(.vertical, ScaleFactor.padding(12))
                        .background(DXYColors.searchBackground)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
                }
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.top, ScaleFactor.padding(16))
                
                // 操作按钮
                HStack(spacing: ScaleFactor.spacing(16)) {
                    // 重拍按钮
                    Button(action: {
                        dismiss()
                        onRetake()
                    }) {
                        Text("重拍")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                            .foregroundColor(DXYColors.textPrimary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, ScaleFactor.padding(14))
                            .background(DXYColors.tagBackground)
                            .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
                    }
                    .disabled(isUploading)
                    
                    // 确认使用按钮
                    Button(action: confirmUpload) {
                        HStack(spacing: ScaleFactor.spacing(8)) {
                            if isUploading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            }
                            Text(isUploading ? "保存中..." : "确认使用")
                                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, ScaleFactor.padding(14))
                        .background(isUploading ? DXYColors.primaryPurple.opacity(0.7) : DXYColors.primaryPurple)
                        .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(12)))
                    }
                    .disabled(isUploading)
                }
                .padding(.horizontal, ScaleFactor.padding(16))
                .padding(.top, ScaleFactor.padding(16))
                .padding(.bottom, ScaleFactor.padding(34))
            }
            .background(DXYColors.cardBackground)
        }
        .ignoresSafeArea(edges: .top)
    }
    
    // MARK: - 确认上传
    private func confirmUpload() {
        isUploading = true
        
        // 模拟保存到本地的操作
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            // 保存到本地（通过LocalImageManager）
            // 这里会在集成时调用 LocalImageManager.shared.saveImage()
            
            isUploading = false
            dismiss()
            onConfirm(image, note)
        }
    }
}

// MARK: - 图片预览导航包装器
struct PhotoPreviewNavigationView: View {
    let image: UIImage
    @Environment(\.dismiss) private var dismiss
    
    var onRetake: () -> Void
    var onConfirm: (UIImage, String) -> Void
    
    var body: some View {
        NavigationView {
            PhotoPreviewView(
                image: image,
                onRetake: onRetake,
                onConfirm: onConfirm
            )
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                            .foregroundColor(DXYColors.textPrimary)
                    }
                }
                
                ToolbarItem(placement: .principal) {
                    Text("照片预览")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                }
            }
        }
    }
}

// MARK: - 上传成功提示视图
struct UploadSuccessToast: View {
    @Binding var isShowing: Bool
    let message: String
    
    var body: some View {
        if isShowing {
            HStack(spacing: ScaleFactor.spacing(12)) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(DXYColors.teal)
                
                Text(message)
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
            }
            .padding(.horizontal, ScaleFactor.padding(20))
            .padding(.vertical, ScaleFactor.padding(14))
            .background(
                RoundedRectangle(cornerRadius: ScaleFactor.size(12))
                    .fill(DXYColors.cardBackground)
                    .shadow(color: Color.black.opacity(0.1), radius: 12, x: 0, y: 4)
            )
            .transition(.move(edge: .top).combined(with: .opacity))
            .onAppear {
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    withAnimation(.easeOut(duration: 0.3)) {
                        isShowing = false
                    }
                }
            }
        }
    }
}

// MARK: - Preview
#Preview {
    PhotoPreviewView(
        image: UIImage(systemName: "photo")!,
        onRetake: { print("Retake") },
        onConfirm: { _, note in print("Confirm with note: \(note)") }
    )
}
