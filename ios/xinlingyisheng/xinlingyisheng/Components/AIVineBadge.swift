import SwiftUI

struct AIVineBadge: View {
    var size: CGFloat
    @State private var glowPulse = false
    @State private var vineRotate = false
    
    var body: some View {
        ZStack {
            aiCore
            
            vineElements
        }
    }
    
    private var aiCore: some View {
        ZStack {
            Circle()
                .fill(Color.white.opacity(0.25))
                .frame(width: size * 0.42, height: size * 0.42)
                .scaleEffect(glowPulse ? 1.15 : 1.0)
                .opacity(glowPulse ? 0.6 : 0.9)
                .animation(
                    .easeInOut(duration: 2.0).repeatForever(autoreverses: true),
                    value: glowPulse
                )
            
            Circle()
                .fill(Color.white.opacity(0.9))
                .frame(width: size * 0.32, height: size * 0.32)
                .overlay(
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: size * 0.18, weight: .medium))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [
                                    PremiumColorTheme.primaryColor,
                                    PremiumColorTheme.secondaryColor
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                )
                .shadow(color: Color.white.opacity(0.5), radius: 8, x: 0, y: 0)
        }
        .onAppear {
            glowPulse = true
        }
    }
    
    private var vineElements: some View {
        ZStack {
            ForEach(0..<3, id: \.self) { index in
                VineCurve(
                    size: size,
                    rotation: Double(index) * 120,
                    delay: Double(index) * 0.3
                )
            }
        }
        .rotationEffect(.degrees(vineRotate ? 360 : 0))
        .animation(
            .linear(duration: 20).repeatForever(autoreverses: false),
            value: vineRotate
        )
        .onAppear {
            vineRotate = true
        }
    }
}

struct VineCurve: View {
    var size: CGFloat
    var rotation: Double
    var delay: Double
    @State private var animate = false
    
    var body: some View {
        Path { path in
            let center = CGPoint(x: size / 2, y: size / 2)
            let radius = size * 0.35
            
            path.move(to: center)
            
            let startAngle = Angle(degrees: -90)
            let endAngle = Angle(degrees: 30)
            
            path.addArc(
                center: center,
                radius: radius,
                startAngle: startAngle,
                endAngle: endAngle,
                clockwise: false
            )
        }
        .trim(from: 0, to: animate ? 1 : 0)
        .stroke(
            LinearGradient(
                colors: [
                    Color.white.opacity(0.8),
                    Color.white.opacity(0.3)
                ],
                startPoint: .leading,
                endPoint: .trailing
            ),
            style: StrokeStyle(lineWidth: 2.5, lineCap: .round)
        )
        .rotationEffect(.degrees(rotation))
        .animation(
            .easeInOut(duration: 1.5).delay(delay).repeatForever(autoreverses: true),
            value: animate
        )
        .onAppear {
            animate = true
        }
    }
}

#Preview {
    ZStack {
        LinearGradient(
            colors: [Color.purple, Color.blue],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
        
        AIVineBadge(size: 100)
    }
}
