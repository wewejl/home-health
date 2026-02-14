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
struct AppSheet<Content: View>: View {

    // MARK: - Types

    enum SheetType {
        case standard
        case fullScreen
        case fixedHeight(CGFloat)
    }

    // MARK: - Properties

    let isPresented: Binding<Bool>
    let title: String?
    let content: Content
    let type: SheetType

    // MARK: - Body

    var body: some View {
        EmptyView()
    }
}

// MARK: - Preview

#if DEBUG
struct AppSheet_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Sheet Component")
                .font(.title2)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
