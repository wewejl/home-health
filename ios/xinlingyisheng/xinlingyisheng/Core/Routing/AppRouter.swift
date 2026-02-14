//
//  AppRouter.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一应用路由管理

import SwiftUI

/// 应用路由管理
///
/// 集中管理所有应用路由，使用 enum 类型安全
/// 支持参数传递和深度链接
///
enum AppRouter: Identifiable {
    case home
    case askDoctor
    case consultations
    case medicalDossier
    case knowledge
    case profile
    case settings

    var id: String {
        switch self {
        case .home:
            return "home"
        case .askDoctor:
            return "askDoctor"
        case .consultations:
            return "consultations"
        case .medicalDossier:
            return "medicalDossier"
        case .knowledge:
            return "knowledge"
        case .profile:
            return "profile"
        case .settings:
            return "settings"
        }
    }
}

// MARK: - Router Environment Key

private struct RouterKey: EnvironmentKey {
    static var defaultValue: AppRouter? { nil }
}

// MARK: - Router View Modifier

extension View {
    /// 路由到指定页面
    /// - Parameter router: 要导航的路由
    func navigate(to router: AppRouter) -> some View {
        switch router {
        case .home:
            return AnyView(Text("Home"))
        case .askDoctor:
            return AnyView(Text("Ask Doctor"))
        case .consultations:
            return AnyView(Text("Consultations"))
        case .medicalDossier:
            return AnyView(Text("Medical Dossier"))
        case .knowledge:
            return AnyView(Text("Knowledge"))
        case .profile:
            return AnyView(Text("Profile"))
        case .settings:
            return AnyView(Text("Settings"))
        }
    }
}

// MARK: - Preview Provider

#if DEBUG
struct AppRouter_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Home")
            Text("Ask Doctor")
            Text("Consultations")
            Text("Medical Dossier")
            Text("Knowledge")
            Text("Profile")
            Text("Settings")
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
