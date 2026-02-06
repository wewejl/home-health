//
//  SplashView.swift
//  xinlingyisheng
//
//  Created by Claude on 2025/01/31.
//  品牌启动动画 - 治愈系风格
//

import SwiftUI

struct SplashView: View {
    // MARK: - Animation States
    @State private var logoScale: CGFloat = 0.3
    @State private var logoOpacity: Double = 0
    @State private var textOpacity: Double = 0
    @State private var backgroundOpacity: Double = 0
    @State private var taglineOpacity: Double = 0
    @State private var decorativeOpacity: Double = 0

    // Animation completion callback
    var onAnimationComplete: () -> Void

    // MARK: - Body
    var body: some View {
        ZStack {
            // 治愈系渐变背景
            HealingColorTheme.primaryGradient
                .ignoresSafeArea()
                .opacity(backgroundOpacity)

            // 装饰光晕 - 右上角
            Circle()
                .fill(HealingColors.deepSage.opacity(0.15))
                .frame(width: 200, height: 200)
                .offset(x: 100, y: -80)
                .opacity(decorativeOpacity)

            // 装饰光晕 - 左下角
            Circle()
                .fill(HealingColors.mutedCoral.opacity(0.1))
                .frame(width: 150, height: 150)
                .offset(x: -80, y: 100)
                .opacity(decorativeOpacity)

            // Logo 和文字
            VStack(spacing: ScaleFactor.spacing(24)) {
                Spacer()

                // 心形 Logo
                ZStack {
                    // 外圈光晕
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [
                                    HealingColors.softSage.opacity(0.3),
                                    HealingColors.deepSage.opacity(0.1)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 120, height: 120)

                    // 主圆圈
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color.white, HealingColors.softSage],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 96, height: 96)
                        .shadow(
                            color: HealingColors.forestMist.opacity(0.3),
                            radius: ScaleFactor.size(20),
                            y: ScaleFactor.size(10)
                        )

                    // 心形图标
                    Image(systemName: "heart.fill")
                        .font(.system(size: UnifiedFont.title3, weight: .medium))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [HealingColors.deepSage, HealingColors.forestMist],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
                .scaleEffect(logoScale)
                .opacity(logoOpacity)

                // 品牌名称
                VStack(spacing: ScaleFactor.spacing(8)) {
                    Text("灵犀健康")
                        .font(.system(size: UnifiedFont.title1, weight: .bold))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [HealingColors.textPrimary, HealingColors.forestMist],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .opacity(textOpacity)

                    Text("AI 健康管家 · 随时守护")
                        .font(.system(size: UnifiedFont.footnote, weight: .regular))
                        .foregroundColor(HealingColors.textSecondary)
                        .opacity(taglineOpacity)
                }

                Spacer()
            }
            .contentShape(Rectangle())
            .onTapGesture {
                // 点击跳过动画
                skipAnimation()
            }
        }
        .onAppear {
            startAnimation()
        }
    }

    // MARK: - Animation Sequence
    private func startAnimation() {
        // 1. 背景淡入 (0.0s - 0.4s)
        withAnimation(.easeOut(duration: 0.4)) {
            backgroundOpacity = 1.0
        }

        // 2. 装饰元素淡入 (0.1s - 0.5s)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            withAnimation(.easeOut(duration: 0.4)) {
                decorativeOpacity = 1.0
            }
        }

        // 3. Logo 缩放淡入 (0.3s - 0.9s)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.75)) {
                logoScale = 1.0
                logoOpacity = 1.0
            }
        }

        // 4. 品牌名称淡入 (0.7s - 1.1s)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
            withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
                textOpacity = 1.0
            }
        }

        // 5. 副标题淡入 (0.9s - 1.2s)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.9) {
            withAnimation(.spring(response: 0.5, dampingFraction: 0.85)) {
                taglineOpacity = 1.0
            }
        }

        // 6. 动画完成，显示主界面 (2.0s)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            onAnimationComplete()
        }
    }

    // MARK: - Skip Animation
    private func skipAnimation() {
        // 立即显示所有元素
        withAnimation(.easeInOut(duration: 0.2)) {
            backgroundOpacity = 1.0
            decorativeOpacity = 1.0
            logoScale = 1.0
            logoOpacity = 1.0
            textOpacity = 1.0
            taglineOpacity = 1.0
        }

        // 短暂延迟后完成
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            onAnimationComplete()
        }
    }
}

// MARK: - Preview
#Preview {
    SplashView {
        print("Animation complete")
    }
}
