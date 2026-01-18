import SwiftUI

// MARK: - 登录表单焦点枚举
enum LoginField: Hashable {
    case phone
    case code
}

struct CustomTextField: View {
    let icon: String
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboardType: UIKeyboardType = .default
    var isFocused: Bool = false
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(isFocused ? PremiumColorTheme.primaryColor : PremiumColorTheme.textSecondary)
                .frame(width: 24)
            
            if isSecure {
                SecureField(placeholder, text: $text)
                    .font(.system(size: 16, weight: .regular, design: .rounded))
                    .keyboardType(keyboardType)
            } else {
                TextField(placeholder, text: $text)
                    .font(.system(size: 16, weight: .regular, design: .rounded))
                    .keyboardType(keyboardType)
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Color.dynamicColor(
                    light: Color.white.opacity(0.5),
                    dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                ))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(
                            isFocused ? PremiumColorTheme.primaryColor : Color.clear,
                            lineWidth: 1.5
                        )
                )
        )
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}
