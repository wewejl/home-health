import SwiftUI

// MARK: - 拍照操作菜单（底部Sheet）
/// 符合设计规范的底部操作菜单，提供拍照和从相册选择两种方式
struct PhotoActionSheet: View {
    @Binding var isPresented: Bool
    var onCamera: () -> Void
    var onLibrary: () -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("上传照片")
                    .font(.system(size: AdaptiveFont.title2, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Spacer()
                
                Button(action: { 
                    withAnimation(.easeOut(duration: 0.25)) {
                        isPresented = false 
                    }
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: ScaleFactor.size(24)))
                        .foregroundColor(DXYColors.textTertiary)
                }
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(16))
            
            Divider()
            
            // 选项列表
            VStack(spacing: 0) {
                // 拍照选项
                PhotoActionItem(
                    icon: "camera.fill",
                    iconColor: DXYColors.blue,
                    title: "拍照",
                    subtitle: "拍摄皮肤照片进行分析",
                    action: {
                        isPresented = false
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                            onCamera()
                        }
                    }
                )
                
                Divider()
                    .padding(.leading, ScaleFactor.padding(70))
                
                // 从相册选择
                PhotoActionItem(
                    icon: "photo.fill",
                    iconColor: DXYColors.teal,
                    title: "从相册选择",
                    subtitle: "选择已有照片",
                    action: {
                        isPresented = false
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                            onLibrary()
                        }
                    }
                )
            }
            
            // 隐私提示
            HStack(spacing: ScaleFactor.spacing(8)) {
                Image(systemName: "info.circle")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.orange)
                
                Text("照片仅保存在您的手机本地，不会上传到服务器")
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(DXYColors.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(ScaleFactor.padding(12))
            .background(DXYColors.orange.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(8)))
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(16))
        }
        .background(DXYColors.cardBackground)
        .clipShape(UnevenRoundedRectangle(topLeadingRadius: ScaleFactor.size(16), topTrailingRadius: ScaleFactor.size(16)))
    }
}

// MARK: - 操作选项项
struct PhotoActionItem: View {
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String
    var action: () -> Void
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: ScaleFactor.spacing(16)) {
                // 图标容器
                ZStack {
                    RoundedRectangle(cornerRadius: ScaleFactor.size(12))
                        .fill(iconColor.opacity(0.15))
                        .frame(width: ScaleFactor.size(48), height: ScaleFactor.size(48))
                    
                    Image(systemName: icon)
                        .font(.system(size: AdaptiveFont.title2))
                        .foregroundColor(iconColor)
                }
                
                // 文字内容
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    Text(title)
                        .font(.system(size: AdaptiveFont.body, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Text(subtitle)
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textSecondary)
                }
                
                Spacer()
                
                // 箭头
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(DXYColors.textTertiary)
            }
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(16))
            .background(isPressed ? DXYColors.background : Color.clear)
        }
        .buttonStyle(PlainButtonStyle())
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - PhotoActionSheet 容器视图
struct PhotoActionSheetContainer: View {
    @Binding var isPresented: Bool
    var onCamera: () -> Void
    var onLibrary: () -> Void
    
    var body: some View {
        ZStack(alignment: .bottom) {
            // 半透明背景遮罩
            if isPresented {
                Color.black.opacity(0.4)
                    .ignoresSafeArea()
                    .onTapGesture {
                        withAnimation(.easeOut(duration: 0.25)) {
                            isPresented = false
                        }
                    }
                    .transition(.opacity)
            }
            
            // 底部Sheet
            if isPresented {
                PhotoActionSheet(
                    isPresented: $isPresented,
                    onCamera: onCamera,
                    onLibrary: onLibrary
                )
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.35, dampingFraction: 0.85), value: isPresented)
    }
}

// MARK: - Preview
#Preview {
    ZStack {
        Color.gray.opacity(0.3)
            .ignoresSafeArea()
        
        PhotoActionSheetContainer(
            isPresented: .constant(true),
            onCamera: { print("Camera tapped") },
            onLibrary: { print("Library tapped") }
        )
    }
}
