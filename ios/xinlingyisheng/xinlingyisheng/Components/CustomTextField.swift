import SwiftUI

// MARK: - 登录表单焦点枚举
enum LoginField: Hashable {
    case phone
    case code
}

// MARK: - 自定义文本输入框 - 自适应布局
struct CustomTextField: View {
    let icon: String
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboardType: UIKeyboardType = .default
    var isFocused: Bool = false

    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.body, weight: .medium))
                .foregroundColor(isFocused ? AppColor.primaryPurple : AppColor.textSecondary)
                .frame(width: ScaleFactor.size(24))

            if isSecure {
                SecureField(placeholder, text: $text)
                    .font(.system(size: AdaptiveFont.body, weight: .regular, design: .rounded))
                    .keyboardType(keyboardType)
            } else {
                TextField(placeholder, text: $text)
                    .font(.system(size: AdaptiveFont.body, weight: .regular, design: .rounded))
                    .keyboardType(keyboardType)
            }
        }
        .padding(.horizontal, ScaleFactor.padding(18))
        .padding(.vertical, ScaleFactor.padding(14))
        .background(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous)
                .fill(AppColor.cardBackground.opacity(0.7))
                .overlay(
                    RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous)
                        .stroke(
                            isFocused ? AppColor.primaryPurple : Color.clear,
                            lineWidth: ScaleFactor.size(1.5)
                        )
                )
        )
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }
}
