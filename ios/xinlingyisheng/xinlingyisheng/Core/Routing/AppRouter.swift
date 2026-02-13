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
    static var currentValue: AppRouter?
}

// MARK: - Router View Modifier

extension View {
    /// 路由到指定页面
    /// - Parameter router: 要导航的路由
    func navigate(to router: AppRouter) -> some View {
        switch router {
        case .home:
            return AnyView(HomeView())
        case .askDoctor:
            return AnyView(AskDoctorView())
        case .consultations:
            return AnyView(SessionHistoryView())
        case .medicalDossier:
            return AnyView(MedicalDossierView())
        case .knowledge:
            return AnyView(DepartmentDetailView())
        case .profile:
            return AnyView(ProfileView())
        case .settings:
            return AnyView(Text("Settings"))
        }
    }
}

// MARK: - Navigation Path Modifier

extension View {
    /// 添加导航路径到页面，支持返回
    func navigationPath(to router: AppRouter) -> some View {
        switch router {
        case .home:
            return AnyView(NavigationPath { HomeView() })
        case .askDoctor:
            return AnyView(NavigationPath { AskDoctorView() })
        case .consultations:
            return AnyView(NavigationPath { SessionHistoryView() })
        case .medicalDossier:
            return AnyView(NavigationPath { MedicalDossierView() })
        case .knowledge:
            return AnyView(NavigationPath { DepartmentDetailView() })
        case .profile:
            return AnyView(NavigationPath { ProfileView() })
        case .settings:
            return AnyView(NavigationPath { Text("Settings") })
        }
    }
}

// MARK: - Sheet Presentation Modifier

extension View {
    /// 显示抽屉
    func presentSheet<Sheet: View>(
        isPresented: Binding<Bool>,
        content: () -> Sheet
    ) -> some View {
        Sheet(
            isPresented: isPresented,
            onDismiss: {
                isPresented.wrappedValue = false
            },
            content: content
        )
    }
}

// MARK: - Alert Presentation Modifier

extension View {
    /// 显示警告
    func showAlert(
        isShowing: Binding<Bool>,
        title: String,
        message: String
    ) -> some View {
        Alert(
            title: Text(title),
            message: Text(message),
            isPresented: isShowing,
            dismissButton: .default(Text("确认"))
        )
    }
}

// MARK: - Preview Provider

#if DEBUG
struct AppRouter_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Home").tag(AppRouter.home)
            Text("Ask Doctor").tag(AppRouter.askDoctor)
            Text("Consultations").tag(AppRouter.consultations)
            Text("Medical Dossier").tag(AppRouter.medicalDossier)
            Text("Knowledge").tag(AppRouter.knowledge)
            Text("Profile").tag(AppRouter.profile)
            Text("Settings").tag(AppRouter.settings)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
