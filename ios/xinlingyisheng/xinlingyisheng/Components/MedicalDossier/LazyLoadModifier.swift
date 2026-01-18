import SwiftUI

struct LazyLoadModifier: ViewModifier {
    @State private var isVisible = false
    
    func body(content: Content) -> some View {
        GeometryReader { geometry in
            if isVisible {
                content
            } else {
                Color.clear
                    .onAppear {
                        withAnimation(.easeIn(duration: 0.2)) {
                            isVisible = true
                        }
                    }
            }
        }
    }
}

extension View {
    func lazyLoad() -> some View {
        modifier(LazyLoadModifier())
    }
}

struct AnimatedAppearModifier: ViewModifier {
    let delay: Double
    @State private var isVisible = false
    
    func body(content: Content) -> some View {
        content
            .opacity(isVisible ? 1 : 0)
            .offset(y: isVisible ? 0 : 20)
            .onAppear {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.8).delay(delay)) {
                    isVisible = true
                }
            }
    }
}

extension View {
    func animatedAppear(delay: Double = 0) -> some View {
        modifier(AnimatedAppearModifier(delay: delay))
    }
}

struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = 0
    
    func body(content: Content) -> some View {
        content
            .overlay(
                GeometryReader { geometry in
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0),
                            Color.white.opacity(0.5),
                            Color.white.opacity(0)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                    .frame(width: geometry.size.width * 2)
                    .offset(x: -geometry.size.width + phase * geometry.size.width * 3)
                    .animation(
                        Animation.linear(duration: 1.5).repeatForever(autoreverses: false),
                        value: phase
                    )
                }
            )
            .mask(content)
            .onAppear {
                phase = 1
            }
    }
}

extension View {
    func shimmer() -> some View {
        modifier(ShimmerModifier())
    }
}

struct SkeletonCardView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack(spacing: ScaleFactor.spacing(12)) {
                Circle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: ScaleFactor.size(36), height: ScaleFactor.size(36))
                
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.gray.opacity(0.2))
                        .frame(width: 120, height: 16)
                    
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.gray.opacity(0.15))
                        .frame(width: 180, height: 12)
                }
                
                Spacer()
                
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.gray.opacity(0.15))
                    .frame(width: 60, height: 24)
            }
            
            RoundedRectangle(cornerRadius: 4)
                .fill(Color.gray.opacity(0.15))
                .frame(height: 14)
            
            RoundedRectangle(cornerRadius: 4)
                .fill(Color.gray.opacity(0.1))
                .frame(width: 200, height: 14)
            
            HStack(spacing: ScaleFactor.spacing(12)) {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.gray.opacity(0.1))
                    .frame(width: 50, height: 24)
                
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.gray.opacity(0.1))
                    .frame(width: 50, height: 24)
            }
        }
        .padding(ScaleFactor.padding(16))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
        .shimmer()
    }
}

struct LoadingListView: View {
    let count: Int
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            ForEach(0..<count, id: \.self) { _ in
                SkeletonCardView()
            }
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        SkeletonCardView()
        LoadingListView(count: 3)
    }
    .padding()
    .background(DXYColors.background)
}
