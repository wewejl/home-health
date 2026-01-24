import SwiftUI

// MARK: - 病历详情包装视图（治愈系风格）
struct EventDetailWrapperView: View {
    let eventId: String
    @StateObject private var viewModel = MedicalDossierViewModel()
    @State private var event: MedicalEvent?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            Group {
                if isLoading {
                    HealingEventWrapperLoadingView(layout: layout)
                } else if let event = event {
                    EventDetailView(event: event, viewModel: viewModel)
                } else {
                    HealingEventWrapperErrorView(
                        errorMessage: errorMessage,
                        layout: layout
                    ) {
                        Task {
                            await loadEvent()
                        }
                    } onDismiss: {
                        dismiss()
                    }
                }
            }
            .task {
                await loadEvent()
            }
        }
    }

    private func loadEvent() async {
        isLoading = true
        errorMessage = nil

        do {
            let detailDTO = try await MedicalEventAPIService.shared.fetchEventDetail(eventId: eventId)
            self.event = detailDTO.toMedicalEvent()
            isLoading = false
        } catch {
            print("[EventDetailWrapper] 加载事件详情失败: \(error)")
            errorMessage = "加载失败，请重试"
            isLoading = false
        }
    }
}

// MARK: - 治愈系加载视图
struct HealingEventWrapperLoadingView: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 治愈系背景
            HealingEventWrapperBackground(layout: layout)

            VStack(spacing: layout.cardSpacing) {
                Spacer()

                // 加载动画
                ZStack {
                    Circle()
                        .stroke(HealingColors.forestMist.opacity(0.2), lineWidth: 3)
                        .frame(width: layout.iconLargeSize * 1.2, height: layout.iconLargeSize * 1.2)

                    Circle()
                        .fill(HealingColors.forestMist.opacity(0.1))
                        .frame(width: 50 + CGFloat(sin(Date().timeIntervalSince1970) * 10) * 10)
                        .animation(.easeInOut(duration: 1).repeatForever(autoreverses: true), value: true)
                }

                Text("正在加载病历详情...")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)

                Spacer()
            }
        }
    }
}

// MARK: - 治愈系错误视图
struct HealingEventWrapperErrorView: View {
    let errorMessage: String?
    let layout: AdaptiveLayout
    let onRetry: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        ZStack {
            // 治愈系背景
            HealingEventWrapperBackground(layout: layout)

            VStack(spacing: layout.cardSpacing) {
                Spacer()

                // 错误图标
                ZStack {
                    Circle()
                        .fill(HealingColors.terracotta.opacity(0.15))
                        .frame(width: layout.iconLargeSize * 1.6, height: layout.iconLargeSize * 1.6)

                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: layout.bodyFontSize + 12, weight: .light))
                        .foregroundColor(HealingColors.terracotta)
                }

                // 错误消息
                Text(errorMessage ?? "加载失败")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("请检查网络连接后重试")
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textSecondary)

                // 操作按钮
                HStack(spacing: layout.cardSpacing) {
                    Button(action: onRetry) {
                        Text("重试")
                            .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, layout.cardInnerPadding)
                            .background(
                                LinearGradient(
                                    colors: [HealingColors.forestMist, HealingColors.deepSage],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 2)
                    }

                    Button(action: onDismiss) {
                        Text("返回")
                            .font(.system(size: layout.bodyFontSize - 1))
                            .foregroundColor(HealingColors.textSecondary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, layout.cardInnerPadding)
                            .background(HealingColors.cardBackground)
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 14, style: .continuous)
                                    .stroke(HealingColors.textTertiary.opacity(0.3), lineWidth: 1)
                            )
                    }
                }
                .padding(.horizontal, layout.horizontalPadding * 2)

                Spacer()
            }
        }
    }
}

// MARK: - 治愈系包装器背景
struct HealingEventWrapperBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.softSage.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geo.size.width * 0.4, y: geo.size.height * 0.2)
                    .ignoresSafeArea()
            }
        }
    }
}

#Preview {
    CompatibleNavigationStack {
        EventDetailWrapperView(eventId: "123")
    }
}
