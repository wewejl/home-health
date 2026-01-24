import SwiftUI

struct AnyShape: Shape {
    private let pathBuilder: @Sendable (CGRect) -> Path

    init<S: Shape & Sendable>(_ shape: S) {
        self.pathBuilder = { rect in
            shape.path(in: rect)
        }
    }

    func path(in rect: CGRect) -> Path {
        pathBuilder(rect)
    }
}

enum LogoStyle: String, CaseIterable, Identifiable {
    case heartPulse = "心脉徽章"
    case stethoscope = "听诊守护"
    case crossShield = "十字护盾"
    case aiVine = "智能藤蔓"

    var id: String { rawValue }
}

// MARK: - Logo 视图 - 自适应布局
struct LogoView: View {
    var style: LogoStyle = .heartPulse
    var size: CGFloat = ScaleFactor.size(80)
    @State private var isAnimating = false

    var body: some View {
        ZStack {
            backgroundShape
            logoSymbol
        }
        .frame(width: size, height: size)
        .scaleEffect(isAnimating ? 1.0 : 0.9)
        .opacity(isAnimating ? 1.0 : 0.85)
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.6)) {
                isAnimating = true
            }
        }
    }

    private var shapeForStyle: AnyShape {
        switch style {
        case .heartPulse:
            return AnyShape(Circle())
        case .stethoscope:
            return AnyShape(RoundedRectangle(cornerRadius: size * 0.3, style: .continuous))
        case .crossShield:
            return AnyShape(RoundedRectangle(cornerRadius: size * 0.2, style: .continuous))
        case .aiVine:
            return AnyShape(Circle())
        }
    }

    private var backgroundShape: some View {
        let baseShape = shapeForStyle
        return baseShape
        .fill(
            LinearGradient(
                colors: AppColor.gradientColors,
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .shadow(color: AppColor.primaryPurple.opacity(0.4), radius: ScaleFactor.size(20), x: 0, y: ScaleFactor.size(10))
        .overlay(
            baseShape
                .stroke(
                LinearGradient(
                    colors: [
                        Color.white.opacity(0.45),
                        Color.white.opacity(0.1)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: ScaleFactor.size(2)
            )
        )
    }

    @ViewBuilder
    private var logoSymbol: some View {
        switch style {
        case .heartPulse:
            HeartPulseIcon(size: size * 0.65)
                .foregroundColor(.white)
        case .stethoscope:
            StethoscopeBadge(size: size)
        case .crossShield:
            CrossShieldBadge(size: size)
        case .aiVine:
            AIVineBadge(size: size)
        }
    }
}

struct HeartPulseIcon: View {
    var size: CGFloat

    var body: some View {
        ZStack {
            Image(systemName: "heart.fill")
                .font(.system(size: size * 0.55, weight: .semibold))
                .offset(y: -size * 0.08)

            HStack(spacing: size * 0.12) {
                PulseLine(height: size * 0.35, delay: 0.0)
                PulseLine(height: size * 0.45, delay: 0.12)
                PulseLine(height: size * 0.30, delay: 0.24)
            }
            .offset(y: size * 0.25)
        }
        .frame(width: size, height: size)
    }
}

struct StethoscopeBadge: View {
    var size: CGFloat

    var body: some View {
        VStack(spacing: size * 0.08) {
            Image(systemName: "stethoscope")
                .font(.system(size: size * 0.45, weight: .medium))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(Color.white, Color.white.opacity(0.85))

            Capsule()
                .fill(Color.white.opacity(0.9))
                .frame(width: size * 0.45, height: size * 0.08)
                .overlay(
                    Text("MD")
                        .font(.system(size: size * 0.18, weight: .semibold, design: .rounded))
                        .foregroundColor(AppColor.primaryPurple.opacity(0.9))
                )
        }
    }
}

struct CrossShieldBadge: View {
    var size: CGFloat
    @State private var breathe = false

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.18, style: .continuous)
                .fill(Color.white.opacity(0.15))
                .frame(width: size * 0.75, height: size * 0.75)
                .scaleEffect(breathe ? 1.05 : 0.95)
                .animation(
                    .easeInOut(duration: 1.6).repeatForever(autoreverses: true),
                    value: breathe
                )

            Image(systemName: "cross.case.fill")
                .font(.system(size: size * 0.45, weight: .semibold))
                .foregroundStyle(
                    LinearGradient(
                        colors: [Color.white, Color.white.opacity(0.8)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .shadow(color: AppColor.primaryPurple.opacity(0.5), radius: ScaleFactor.size(8), x: 0, y: ScaleFactor.size(6))
        }
        .onAppear {
            breathe = true
        }
    }
}

struct PulseLine: View {
    var height: CGFloat
    var delay: Double
    @State private var animate = false

    var body: some View {
        RoundedRectangle(cornerRadius: ScaleFactor.size(1.5))
            .fill(Color.white.opacity(0.9))
            .frame(width: ScaleFactor.size(2.5), height: animate ? height : height * 0.3)
            .animation(
                Animation.easeInOut(duration: 0.8)
                    .repeatForever(autoreverses: true)
                    .delay(delay),
                value: animate
            )
            .onAppear {
                animate = true
            }
    }
}

struct AIVineBadge: View {
    var size: CGFloat
    @State private var rotate = false

    var body: some View {
        ZStack {
            // AI 神经网络点阵效果
            ForEach(0..<8) { i in
                let angle = Double(i) * .pi / 4
                let radius = size * 0.28
                let x = cos(angle) * radius
                let y = sin(angle) * radius

                Circle()
                    .fill(Color.white.opacity(0.7))
                    .frame(width: size * 0.08, height: size * 0.08)
                    .offset(x: x, y: y)
                    .scaleEffect(rotate ? 1.1 : 0.9)
                    .animation(
                        Animation.easeInOut(duration: 1.2)
                            .repeatForever(autoreverses: true)
                            .delay(Double(i) * 0.1),
                        value: rotate
                    )

                // 连接线
                if i < 4 {
                    Path { path in
                        path.move(to: CGPoint(x: 0, y: 0))
                        path.addLine(to: CGPoint(x: x, y: y))
                    }
                    .stroke(Color.white.opacity(0.25), lineWidth: ScaleFactor.size(1))
                }
            }

            // 中心医疗十字
            PlusSignView(size: size * 0.4)
                .foregroundColor(.white)
                .shadow(color: Color.white.opacity(0.5), radius: ScaleFactor.size(8), x: 0, y: ScaleFactor.size(4))
        }
        .frame(width: size, height: size)
        .onAppear {
            rotate = true
        }
    }
}

// 医疗十字组件
struct PlusSignView: View {
    var size: CGFloat
    var thickness: CGFloat = 0.2

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let height = geometry.size.height
            let t = width * thickness

            ZStack {
                RoundedRectangle(cornerRadius: t * 0.5)
                    .frame(width: t, height: height)
                RoundedRectangle(cornerRadius: t * 0.5)
                    .frame(width: width, height: t)
            }
        }
        .frame(width: size, height: size)
    }
}

struct MinimalistLogoView: View {
    var size: CGFloat = ScaleFactor.size(80)
    var style: LogoStyle = .heartPulse

    var body: some View {
        LogoView(style: style, size: size)
    }
}

#Preview {
    VStack(spacing: 32) {
        ForEach(LogoStyle.allCases) { style in
            VStack(spacing: 8) {
                LogoView(style: style, size: 96)
                Text(style.rawValue)
                    .font(.caption)
            }
        }
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
