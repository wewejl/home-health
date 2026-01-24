import SwiftUI

// MARK: - 手机号输入框 - 自适应布局
struct PhoneNumberTextField: View {
    @Binding var phoneNumber: String
    @Binding var displayNumber: String
    var isFocused: Bool = false
    var onPhoneChange: ((String, String) -> Void)? = nil  // phone, display
    var onComplete: (() -> Void)?

    @FocusState private var textFieldIsFocused: Bool

    private var iconSize: CGFloat {
        DeviceType.isCompactWidth ? AdaptiveSize.iconMedium * 0.9 : AdaptiveSize.iconMedium
    }

    private var fontSize: CGFloat {
        DeviceType.isCompactWidth ? AdaptiveFont.body - 1 : AdaptiveFont.body
    }

    private var horizontalPadding: CGFloat {
        DeviceType.isCompactWidth ? ScaleFactor.padding(14) : ScaleFactor.padding(18)
    }

    private var verticalPadding: CGFloat {
        DeviceType.isCompactWidth ? ScaleFactor.padding(12) : ScaleFactor.padding(14)
    }

    var body: some View {
        HStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: "phone.fill")
                .font(.system(size: iconSize, weight: .medium))
                .foregroundColor(textFieldIsFocused ? PremiumColorTheme.primaryColor : PremiumColorTheme.textSecondary)
                .frame(width: ScaleFactor.size(24))

            TextField("请输入手机号", text: $displayNumber)
                .font(.system(size: fontSize, weight: .regular, design: .rounded))
                .keyboardType(.phonePad)
                .textContentType(.telephoneNumber)
                .focused($textFieldIsFocused)
                .onChangeCompat(of: displayNumber) { newValue in
                    handlePhoneInput(newValue)
                }
        }
        .padding(.horizontal, horizontalPadding)
        .padding(.vertical, verticalPadding)
        .frame(maxWidth: .infinity)
        .frame(minHeight: LayoutConstants.inputHeight)
        .background(
            RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                .fill(Color.dynamicColor(
                    light: Color.white.opacity(0.5),
                    dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                ))
                .overlay(
                    RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous)
                        .stroke(
                            textFieldIsFocused ? PremiumColorTheme.primaryColor : Color.clear,
                            lineWidth: ScaleFactor.size(1.5)
                        )
                )
        )
        .contentShape(Rectangle())
        .simultaneousGesture(
            TapGesture()
                .onEnded { _ in
                    textFieldIsFocused = true
                }
        )
        .onAppear {
            if isFocused {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                    textFieldIsFocused = true
                }
            }
        }
        .onChangeCompat(of: isFocused) { newValue in
            textFieldIsFocused = newValue
        }
    }

    private func handlePhoneInput(_ input: String) {
        let digits = input.filter { $0.isNumber }
        let limitedDigits = String(digits.prefix(11))
        let formatted = formatPhoneNumber(limitedDigits)

        // 通知外部变化，不直接修改绑定
        onPhoneChange?(limitedDigits, formatted)

        // 输入满11位时触发完成回调
        if limitedDigits.count == 11 {
            onComplete?()
        }
    }

    private func formatPhoneNumber(_ digits: String) -> String {
        var result = ""
        for (index, char) in digits.enumerated() {
            if index == 3 || index == 7 {
                result += " "
            }
            result += String(char)
        }
        return result
    }
}

#Preview {
    VStack(spacing: 20) {
        PhoneNumberTextField(
            phoneNumber: .constant("13812345678"),
            displayNumber: .constant("138 1234 5678"),
            isFocused: true
        )
        PhoneNumberTextField(
            phoneNumber: .constant(""),
            displayNumber: .constant(""),
            isFocused: false
        )
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
