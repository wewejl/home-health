//
//  xinlingyishengApp.swift
//  xinlingyisheng
//
//  Created by zhuxinye on 2025/12/26.
//

import SwiftUI

@main
struct xinlingyishengApp: App {
    init() {
        // 设置全局背景色 - 确保所有页面一致
        setupGlobalAppearance()
    }

    var body: some Scene {
        WindowGroup {
            ZStack {
                // 全局背景色 - 确保覆盖整个屏幕
                AppColor.background
                    .ignoresSafeArea(.all)

                ContentView()
            }
        }
    }

    private func setupGlobalAppearance() {
        // 设置 TabBar 全局外观
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(AppColor.background)
        appearance.shadowColor = UIColor.black.withAlphaComponent(0.05)

        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(AppColor.primaryPurple)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(AppColor.primaryPurple),
            .font: UIFont.systemFont(ofSize: 11, weight: .medium)
        ]

        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(AppColor.textTertiary).withAlphaComponent(0.8)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(AppColor.textTertiary).withAlphaComponent(0.8),
            .font: UIFont.systemFont(ofSize: 11, weight: .regular)
        ]

        appearance.inlineLayoutAppearance.selected.iconColor = UIColor(AppColor.primaryPurple)
        appearance.inlineLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(AppColor.primaryPurple)]
        appearance.inlineLayoutAppearance.normal.iconColor = UIColor(AppColor.textTertiary)
        appearance.inlineLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(AppColor.textTertiary)]

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance

        // 设置 NavigationBar 全局外观
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(AppColor.background)
        navAppearance.shadowColor = UIColor.clear

        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
        UINavigationBar.appearance().compactAppearance = navAppearance
    }
}
