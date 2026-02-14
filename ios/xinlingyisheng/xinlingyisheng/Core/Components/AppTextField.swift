//
//  AppTextField.swift
//  灵犀健康
//

import SwiftUI

struct AppTextField: View {
    @Binding var text: String
    let title: String?
    let placeholder: String?
    let isError: Bool
    let errorMessage: String?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.small) {
            if let title = title {
                Text(title)
                    .font(.caption2)
                    .foregroundColor(AppColors.textSecondary)
            }

            TextField(placeholder ?? "", text: $text)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding(.vertical, 4)

            if let errorMessage = errorMessage, isError {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundColor(AppColors.error)
            }
        }
    }

    init(
        title: String? = nil,
        text: Binding<String>,
        placeholder: String? = nil,
        isError: Bool = false,
        errorMessage: String? = nil
    ) {
        self._text = text
        self.title = title
        self.placeholder = placeholder
        self.isError = isError
        self.errorMessage = errorMessage
    }
}

#if DEBUG
struct AppTextField_Previews: PreviewProvider {
    static var previews: some View {
        AppTextField(
            title: "用户名",
            text: .constant(""),
            placeholder: "请输入用户名"
        )
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
