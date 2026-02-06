//
//  xinlingyishengApp.swift
//  xinlingyisheng
//
//  Created by zhuxinye on 2025/12/26.
//

import SwiftUI

@main
struct xinlingyishengApp: App {
    @Environment(\.scenePhase) private var scenePhase

    init() {
        // 设置全局背景色 - 确保所有页面一致
        setupGlobalAppearance()
    }

    var body: some Scene {
        WindowGroup {
            ZStack {
                // 全局背景色 - 确保覆盖整个屏幕
                DXYColors.background
                    .ignoresSafeArea(.all)

                ContentView()
            }
        }
        .onChange(of: scenePhase) { oldPhase, newPhase in
            handleScenePhaseChange(from: oldPhase, to: newPhase)
        }
    }

    private func handleScenePhaseChange(from oldPhase: ScenePhase, to newPhase: ScenePhase) {
        Task { @MainActor in
            switch newPhase {
            case .background:
                // App 进入后台，断开连接节省资源
                PressAndHoldVoiceService.shared.disconnect()
                #if DEBUG
                print("[App] 进入后台，断开 ASR 连接")
                #endif

            case .inactive:
                // App 即将进入非活跃状态
                break

            case .active:
                // App 恢复活跃，连接会在下次使用时自动建立
                #if DEBUG
                print("[App] 恢复前台")
                #endif

            @unknown default:
                break
            }
        }
    }

    private func setupGlobalAppearance() {
        // 设置 TabBar 全局外观
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(DXYColors.background)
        appearance.shadowColor = UIColor.black.withAlphaComponent(0.05)

        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(DXYColors.primaryPurple)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(DXYColors.primaryPurple),
            .font: UIFont.systemFont(ofSize: 11, weight: .medium)
        ]

        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(DXYColors.textTertiary).withAlphaComponent(0.8)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(DXYColors.textTertiary).withAlphaComponent(0.8),
            .font: UIFont.systemFont(ofSize: 11, weight: .regular)
        ]

        appearance.inlineLayoutAppearance.selected.iconColor = UIColor(DXYColors.primaryPurple)
        appearance.inlineLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(DXYColors.primaryPurple)]
        appearance.inlineLayoutAppearance.normal.iconColor = UIColor(DXYColors.textTertiary)
        appearance.inlineLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(DXYColors.textTertiary)]

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance

        // 设置 NavigationBar 全局外观
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(DXYColors.background)
        navAppearance.shadowColor = UIColor.clear

        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
        UINavigationBar.appearance().compactAppearance = navAppearance
    }
}
