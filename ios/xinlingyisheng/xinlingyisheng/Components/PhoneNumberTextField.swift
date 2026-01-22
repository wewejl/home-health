import SwiftUI

// MARK: - 手机号输入框 - 自适应布局
struct PhoneNumberTextField: View {
    @Binding var phoneNumber: String
    @Binding var displayNumber: String
    var isFocused: Bool = false
    var onComplete: (() -> Void)?

    @FocusState private var textFieldIsFocused: Bool

    private var iconSize: CGFloat {
        DeviceType.isCompactWidth ? 16 : 18
    }

    private var fontSize: CGFloat {
        DeviceType.isCompactWidth ? 15 : 16
    }

    private var horizontalPadding: CGFloat {
        DeviceType.isCompactWidth ? 14 : 18
    }

    private var verticalPadding: CGFloat {
        DeviceType.isCompactWidth ? 12 : 14
    }

    var body: some View {
        HStack(spacing: AdaptiveSpacing.item) {
            Image(systemName: "phone.fill")
                .font(.system(size: iconSize, weight: .medium))
                .foregroundColor(textFieldIsFocused ? PremiumColorTheme.primaryColor : PremiumColorTheme.textSecondary)
                .frame(width: 24)

            TextField("请输入手机号", text: $displayNumber)
                .font(.system(size: fontSize, weight: .regular, design: .rounded))
                .keyboardType(.phonePad)
                .textContentType(.telephoneNumber)
                .focused($textFieldIsFocused)
                .onChangeCompat(of: displayNumber) { newValue in
                    handlePhoneInput(newValue)
                }
                .onAppear {
                    if isFocused {
                        textFieldIsFocused = true
                    }
                }
                .onChangeCompat(of: isFocused) { newValue in
                    textFieldIsFocused = newValue
                }
        }
        .padding(.horizontal, horizontalPadding)
        .padding(.vertical, verticalPadding)
        .frame(maxWidth: .infinity)
        .frame(minHeight: LayoutConstants.inputHeight)
        .background(
            RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusSmall, style: .continuous)
                .fill(Color.dynamicColor(
                    light: Color.white.opacity(0.5),
                    dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.5)
                ))
                .overlay(
                    RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusSmall, style: .continuous)
                        .stroke(
                            textFieldIsFocused ? PremiumColorTheme.primaryColor : Color.clear,
                            lineWidth: 1.5
                        )
                )
        )
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusSmall, style: .continuous))
        .onTapGesture {
            textFieldIsFocused = true
        }
    }
    
    private func handlePhoneInput(_ input: String) {
        let digits = input.filter { $0.isNumber }
        let limitedDigits = String(digits.prefix(11))
        phoneNumber = limitedDigits
        displayNumber = formatPhoneNumber(limitedDigits)
        
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
