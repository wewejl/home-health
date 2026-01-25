import SwiftUI

struct GlassmorphicCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .background(
                ZStack {
                    RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusLarge, style: .continuous)
                        .fill(AppColor.cardBackground.opacity(0.75))
                        .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 5)
                        .shadow(color: Color.black.opacity(0.03), radius: 20, x: 0, y: 10)

                    RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusLarge, style: .continuous)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(0.3),
                                    Color.white.opacity(0.1)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 1
                        )
                }
            )
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: LayoutConstants.cornerRadiusLarge, style: .continuous))
    }
}
