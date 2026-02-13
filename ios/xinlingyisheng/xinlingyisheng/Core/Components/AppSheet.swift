//
//  AppSheet.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一底部抽屉组件

import SwiftUI

/// 底部抽屉组件
///
/// 提供统一的底部抽屉展示，支持多种类型和高度选项
///
struct AppSheet: View {

    // MARK: - Types

    enum SheetType {
        case standard
        case fullScreen
        case fixedHeight(CGFloat)
    }

    // MARK: - Properties

    @Binding var isPresented: Bool
    var title: String?
    var content: () -> some View
    var type: SheetType = .standard
    var fixedHeight: CGFloat?

    // MARK: - Body

    var body: some View {
        if isPresented {
            switch type {
            case .standard:
                sheet(isPresented: $isPresented) {
                    SheetContent()
                }
            case .fullScreen:
                fullScreenCover(isPresented: $isPresented) {
                    SheetContent()
                }
            case .fixedHeight(let height):
                .sheet(isPresented: $isPresented) {
                    SheetContent()
                        .presentationDetents([.height(height)])
                }
            }
        } else {
            EmptyView()
        }
    }

    // MARK: - Sheet Content

    private func SheetContent() -> some View {
        VStack(spacing: AppSpacing.small) {
            if let title = title {
                HStack {
                    Text(title)
                        .font(.title3)
                        .foregroundColor(AppColors.textPrimary)
                    Spacer()
                    Button(action: {
                        isPresented = false
                    }) {
                        Image(systemName: "xmark")
                            .foregroundColor(AppColors.textSecondary)
                            .font(.caption2)
                    }
                }
                .padding(.horizontal, AppSpacing.standard)
            }

            content()
        }
        .padding(AppSpacing.standard)
    }

    // MARK: - Full Screen Cover

    private func fullScreenCover(isPresented: Binding<Bool>, content: @escaping () -> some View) -> some View {
        ZStack {
            Color.black
                .edgesIgnoringSafeArea(.all)
                .overlay(
                    content()
                        .padding(AppSpacing.standard)
                        .background(AppColors.cardBackground)
                        .cornerRadius(AppSpacing.cardCornerRadius, corners: [.topLeft, .topRight])
                )
        }
    }
}

// MARK: - Preview

#if DEBUG
struct AppSheet_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppSheet(
                isPresented: .constant(true),
                title: "标准抽屉",
                content: {
                    Text("抽屉内容")
                        .padding()
                }
            )

            AppSheet(
                isPresented: .constant(true),
                title: "全屏抽屉",
                type: .fullScreen,
                content: {
                    VStack {
                        Text("全屏内容")
                        Text("更多内容")
                    }
                        .padding()
                }
            )

            AppSheet(
                isPresented: .constant(true),
                title: "固定高度抽屉",
                type: .fixedHeight(300),
                content: {
                    Text("固定 300pt 高度")
                        .padding()
                }
            )
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
