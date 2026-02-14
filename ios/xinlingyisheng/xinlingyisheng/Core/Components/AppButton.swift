//
//  AppButton.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一按钮组件

import SwiftUI

/// 统一按钮组件
///
/// 提供标准按钮样式，支持多种类型和状态
///
struct AppButton: View {

    // MARK: - Types

    enum ButtonType {
        case primary
        case secondary
        case tertiary
        case danger
        case success
    }

    enum ButtonSize {
        case small
        case medium
        case large
    }

    // MARK: - Properties

    let title: String
    let buttonType: ButtonType
    let buttonSize: ButtonSize
    let isEnabled: Bool
    let isLoading: Bool
    let action: () -> Void

    // MARK: - Body

    var body: some View {
        Button(action: action) {
            HStack {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                } else {
                    Text(title)
                }
            }
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!isEnabled)
        .controlSize(controlSize(for: buttonSize))
    }

    // MARK: - Initializer

    init(
        title: String,
        type buttonType: ButtonType = .primary,
        size buttonSize: ButtonSize = .medium,
        isEnabled: Bool = true,
        isLoading: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.buttonType = buttonType
        self.buttonSize = buttonSize
        self.isEnabled = isEnabled
        self.isLoading = isLoading
        self.action = action
    }

    // MARK: - Helper Methods

    private func controlSize(for size: ButtonSize) -> ControlSize {
        switch size {
        case .small:
            return .small
        case .medium:
            return .regular
        case .large:
            return .large
        }
    }
}

// MARK: - Preview

#if DEBUG
struct AppButton_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppButton(title: "主按钮") {}
            AppButton(title: "次按钮") {}
            AppButton(title: "危险按钮") {}
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
