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

    var buttonType: ButtonType = .primary
    var buttonSize: ButtonSize = .medium
    var isEnabled: Bool = true

    var action: () -> Void = {}
    var isLoading: Bool = false

    // MARK: - Body

    var body: some View {
        Button(action: action) {
            ZStack {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                } else {
                    title
                }
            }
        } label: {
            Text(title)
                .font(.body)
        }
        .buttonStyle(AppButton.buttonStyle(for: buttonType))
        .disabled(!isEnabled)
        .controlSize(AppButton.controlSize(for: buttonSize))
    }

    // MARK: - Helper Methods

    private static func buttonStyle(for type: ButtonType) -> some PrimitiveButtonStyle {
        switch type {
        case .primary:
            return .bordered
        case .secondary:
            return .bordered
        case .tertiary:
            return .bordered
        case .danger:
            return .bordered
        case .success:
            return .bordered
        }
    }

    private static func controlSize(for size: ButtonSize) -> ControlSize {
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

// MARK: - Button Styles

extension AppButton {

    /// 主按钮样式
    static func primaryStyle() -> some PrimitiveButtonStyle {
        var configuration = PrimitiveButtonStyleConfiguration.bordered
        configuration.base.backgroundColor = .white
        configuration.base.foregroundColor = AppColors.primary

        let title = PrimitiveButtonStyleConfiguration.Label.Title("title")
        configuration.base.title = AttributedString(title)

        return PrimitiveButtonStyle(style: configuration)
    }

    /// 次要按钮样式
    static func secondaryStyle() -> some PrimitiveButtonStyle {
        var configuration = PrimitiveButtonStyleConfiguration.bordered
        configuration.base.backgroundColor = AppColors.cardBackground
        configuration.base.foregroundColor = AppColors.textPrimary

        let title = PrimitiveButtonStyleConfiguration.Label.Title("title")
        configuration.base.title = AttributedString(title)

        return PrimitiveButtonStyle(style: configuration)
    }
}

// MARK: - Preview

#if DEBUG
struct AppButton_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppButton(title: "主按钮", type: .primary) {
                Text("Primary")
            }
            AppButton(title: "次按钮", type: .secondary) {
                Text("Secondary")
            }
            AppButton(title: "危险按钮", type: .danger) {
                Text("Danger")
            }
            AppButton(title: "成功按钮", type: .success) {
                Text("Success")
            }
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
