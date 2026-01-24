import SwiftUI

// MARK: - 验证码输入组件 - 自适应布局
struct VerificationCodeInput: View {
    @Binding var code: String
    let codeLength: Int
    var onComplete: ((String) -> Void)?
    var style: VerificationCodeStyle = VerificationCodeStyle.default
    var isExternallyFocused: Bool = false  // 外部传入的焦点状态

    @FocusState private var isFocused: Bool

    init(
        code: Binding<String>,
        codeLength: Int = 6,
        onComplete: ((String) -> Void)? = nil,
        style: VerificationCodeStyle = .default,
        isExternallyFocused: Bool = false
    ) {
        self._code = code
        self.codeLength = codeLength
        self.onComplete = onComplete
        self.style = style
        self.isExternallyFocused = isExternallyFocused
    }

    var body: some View {
        GeometryReader { geometry in
            let availableWidth = geometry.size.width
            let spacing = calculateSpacing(for: availableWidth)
            let boxSize = calculateBoxSize(for: availableWidth, spacing: spacing)

            ZStack {
                // 隐藏的 TextField 用于接收输入
                TextField("", text: $code)
                    .keyboardType(.numberPad)
                    .textContentType(.oneTimeCode)
                    .focused($isFocused)
                    .opacity(0)
                    .frame(width: 0, height: 0)
                    .accessibility(hidden: true)
                    .onChangeCompat(of: code) { newValue in
                        let filtered = newValue.filter { $0.isNumber }
                        if filtered.count > codeLength {
                            code = String(filtered.prefix(codeLength))
                        } else if filtered != newValue {
                            code = filtered
                        }
                        if code.count == codeLength {
                            onComplete?(code)
                        }
                    }
                    .onAppear {
                        if isExternallyFocused {
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                                isFocused = true
                            }
                        }
                    }
                    .onChangeCompat(of: isExternallyFocused) { newValue in
                        if newValue {
                            isFocused = true
                        }
                    }

                // 显示的数字格子
                HStack(spacing: spacing) {
                    ForEach(0..<codeLength, id: \.self) { index in
                        CodeDigitBox(
                            digit: getDigit(at: index),
                            isActive: code.count == index && isFocused,
                            isFilled: code.count > index,
                            isCompleted: code.count == codeLength,
                            style: style,
                            boxWidth: boxSize.width,
                            boxHeight: boxSize.height
                        )
                    }
                }
                .frame(width: availableWidth, height: boxSize.height)
                .contentShape(Rectangle())
                .simultaneousGesture(
                    TapGesture()
                        .onEnded { _ in
                            isFocused = true
                        }
                )
            }
            .frame(width: availableWidth, height: boxSize.height)
        }
        .frame(height: calculateFixedHeight())
    }

    private func calculateSpacing(for width: CGFloat) -> CGFloat {
        if width < ScaleFactor.size(280) { return ScaleFactor.spacing(4) }
        else if width < ScaleFactor.size(320) { return ScaleFactor.spacing(6) }
        else if width < ScaleFactor.size(360) { return ScaleFactor.spacing(8) }
        return ScaleFactor.spacing(10)
    }
    
    private func calculateBoxSize(for width: CGFloat, spacing: CGFloat) -> CGSize {
        let totalSpacing = spacing * CGFloat(codeLength - 1)
        let availableForBoxes = width - totalSpacing
        let boxWidth = max(ScaleFactor.size(28), availableForBoxes / CGFloat(codeLength))
        let boxHeight = min(ScaleFactor.size(54), max(ScaleFactor.size(44), boxWidth * 1.2))
        return CGSize(width: boxWidth, height: boxHeight)
    }

    private func calculateFixedHeight() -> CGFloat {
        if DeviceType.isVeryCompactWidth { return ScaleFactor.size(46) }
        if DeviceType.isCompactWidth { return ScaleFactor.size(50) }
        if DeviceType.isStandardWidth { return ScaleFactor.size(52) }
        return ScaleFactor.size(54)
    }
    
    private func getDigit(at index: Int) -> String {
        guard index < code.count else { return "" }
        let startIndex = code.index(code.startIndex, offsetBy: index)
        return String(code[startIndex])
    }
}

// MARK: - 单个数字格子
struct CodeDigitBox: View {
    let digit: String
    let isActive: Bool
    let isFilled: Bool
    let isCompleted: Bool
    let style: VerificationCodeStyle
    let boxWidth: CGFloat
    let boxHeight: CGFloat
    
    private var cornerRadius: CGFloat { min(ScaleFactor.size(12), boxWidth * 0.25) }
    private var fontSize: CGFloat { min(AdaptiveFont.title2, max(AdaptiveFont.body, boxWidth * 0.5)) }
    
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .fill(style.baseFill)
                .overlay(
                    RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                        .stroke(borderColor, lineWidth: isActive ? 2 : 1)
                )
                .frame(width: boxWidth, height: boxHeight)
            
            if digit.isEmpty && isActive {
                Rectangle()
                    .fill(style.activeBorder)
                    .frame(width: 2, height: boxHeight * 0.45)
                    .blinkingCursor()
            } else {
                Text(digit)
                    .font(.system(size: fontSize, weight: .semibold, design: .rounded))
                    .foregroundColor(style.textColor)
            }
        }
        .animation(.easeInOut(duration: 0.15), value: isActive)
        .animation(.easeInOut(duration: 0.15), value: isFilled)
        .animation(.spring(response: 0.35, dampingFraction: 0.7), value: isCompleted)
    }
    
    private var borderColor: Color {
        if isCompleted { return style.successBorder ?? style.filledBorder }
        if isActive { return style.activeBorder }
        return isFilled ? style.filledBorder : style.emptyBorder
    }
}

// MARK: - 样式定义
struct VerificationCodeStyle {
    let baseFill: Color
    let emptyBorder: Color
    let activeBorder: Color
    let filledBorder: Color
    let successBorder: Color?
    let textColor: Color
    
    static let `default` = VerificationCodeStyle(
        baseFill: Color.dynamicColor(
            light: Color.white.opacity(0.6),
            dark: Color(red: 0.18, green: 0.18, blue: 0.22).opacity(0.6)
        ),
        emptyBorder: Color.gray.opacity(0.2),
        activeBorder: AppColor.primaryPurple,
        filledBorder: AppColor.primaryPurple.opacity(0.5),
        successBorder: AppColor.successGreen,
        textColor: AppColor.textPrimary
    )
}

// MARK: - 光标闪烁动画
struct BlinkingCursor: ViewModifier {
    @State private var isVisible = true
    
    func body(content: Content) -> some View {
        content
            .opacity(isVisible ? 1 : 0)
            .onAppear {
                withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true)) {
                    isVisible.toggle()
                }
            }
    }
}

extension View {
    func blinkingCursor() -> some View {
        modifier(BlinkingCursor())
    }
}

#Preview {
    VStack(spacing: 20) {
        VerificationCodeInput(code: .constant("123"))
            .frame(maxWidth: 320)
        VerificationCodeInput(code: .constant("123456"))
            .frame(maxWidth: 280)
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
