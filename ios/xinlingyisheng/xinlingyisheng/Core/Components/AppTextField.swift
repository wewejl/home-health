//
//  AppTextField.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一文本输入框组件

import SwiftUI

/// 统一文本输入框组件
///
/// 提供标准输入框样式，支持多种类型和状态
///
struct AppTextField: View {

    // MARK: - Types

    enum TextFieldType {
        case standard
        case underlined
        case filled
    }

    // MARK: - Properties

    var type: TextFieldType = .standard
    var title: String?
    var text: Binding<String>
    var placeholder: String?
    var isSecure: Bool = false
    var isError: Bool = false
    var errorMessage: String?
    var keyboardType: UIKeyboardType = .default
    var autocapitalizationType: UITextAutocapitalizationType = .none

    // MARK: - Body

    var body: some View {
        TextFieldConfig(
            text: text,
            placeholder: placeholder,
            isSecure: isSecure,
            keyboardType: keyboardType,
            autocapitalizationType: autocapitalizationType,
            title: title,
            type: type,
            isError: isError,
            errorMessage: errorMessage
        )
    }
}

// MARK: - TextField Configuration View

struct TextFieldConfig: View {

    var type: AppTextField.TextFieldType
    var title: String?
    var text: Binding<String>
    var placeholder: String?
    var isSecure: Bool
    var isError: Bool
    var errorMessage: String?
    var keyboardType: UIKeyboardType
    var autocapitalizationType: UITextAutocapitalizationType

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.micro) {
            HStack(spacing: AppSpacing.small) {
                if let title = title {
                    Text(title)
                        .font(.caption2)
                        .foregroundColor(AppColors.textSecondary)
                }

                Spacer()

                if isError {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundColor(AppColors.error)
                        .font(.caption2)
                }
            }
            .padding(.horizontal, AppSpacing.small)

            if let errorMessage = errorMessage, isError {
                HStack(spacing: AppSpacing.micro) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(AppColors.error)
                        .font(.caption2)

                    Text(errorMessage)
                        .font(.caption1)
                        .foregroundColor(AppColors.error)
                }
                .padding(.horizontal, AppSpacing.small)
            }
        }
    }
}

// MARK: - Text Field Styles

extension AppTextField {

    private var textFieldStyle: some TextFieldStyle {
        switch type {
        case .standard:
            return StandardTextFieldStyle(isError: isError)
        case .underlined:
            return UnderlinedTextFieldStyle(isError: isError)
        case .filled:
            return FilledTextFieldStyle(isError: isError)
        }
    }
}

// MARK: - Standard TextField Style

struct StandardTextFieldStyle: TextFieldStyle {
    var isError: Bool

    func _body(configuration: TextField<Self.Configuration>) -> some View {
        configuration
            .padding(AppSpacing.small)
            .background(AppColors.cardBackground)
            .cornerRadius(AppSpacing.tiny)
            .overlay(
                RoundedRectangle(cornerRadius: AppSpacing.tiny)
                    .strokeBorder(isError ? AppColors.error : AppColors.borderLight, lineWidth: 1)
            )
            .foregroundColor(AppColors.textPrimary)
    }
}

// MARK: - Underlined TextField Style

struct UnderlinedTextFieldStyle: TextFieldStyle {
    var isError: Bool

    func _body(configuration: TextField<Self.Configuration>) -> some View {
        configuration
            .padding(AppSpacing.small)
            .background(AppColors.cardBackground)
            .foregroundColor(AppColors.textPrimary)
    }
}

// MARK: - Filled TextField Style

struct FilledTextFieldStyle: TextFieldStyle {
    var isError: Bool

    func _body(configuration: TextField<Self.Configuration>) -> some View {
        configuration
            .padding(AppSpacing.small)
            .background(isError ? AppColors.error.opacity(0.1) : AppColors.primary.opacity(0.1))
            .cornerRadius(AppSpacing.tiny)
            .foregroundColor(AppColors.textPrimary)
    }
}

// MARK: - Preview

#if DEBUG
struct AppTextField_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppTextField(
                title: "标准输入",
                text: .constant(""),
                placeholder: "请输入"
            )

            AppTextField(
                title: "下划线输入",
                text: .constant(""),
                placeholder: "请输入",
                type: .underlined
            )

            AppTextField(
                title: "填允输入",
                text: .constant(""),
                placeholder: "请输入",
                type: .filled
            )
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
