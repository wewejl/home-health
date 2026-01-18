//
//  ContentView.swift
//  xinlingyisheng
//
//  Created by zhuxinye on 2025/12/26.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var showProfileSetup = false
    
    var body: some View {
        Group {
            if authManager.isLoggedIn {
                HomeView()
                    .onAppear {
                        // 登录后检查是否需要完善资料
                        checkProfileSetupNeeded()
                    }
            } else {
                LoginView(onLoginSuccess: {
                    // 登录成功后检查是否需要完善资料
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        checkProfileSetupNeeded()
                    }
                })
            }
        }
        .alert("提示", isPresented: $authManager.showLogoutAlert) {
            Button("确定", role: .cancel) {
                authManager.showLogoutAlert = false
            }
        } message: {
            Text(authManager.logoutReason)
        }
        .sheet(isPresented: $showProfileSetup) {
            ProfileSetupView(
                onComplete: {
                    showProfileSetup = false
                },
                allowSkip: true
            )
            .interactiveDismissDisabled(false)
        }
        .onReceive(NotificationCenter.default.publisher(for: AuthManager.profileNeedsSetupNotification)) { _ in
            // 收到需要完善资料的通知时显示资料完善页面
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                showProfileSetup = true
            }
        }
    }
    
    private func checkProfileSetupNeeded() {
        if authManager.needsProfileSetup {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                showProfileSetup = true
            }
        }
    }
}

#Preview {
    ContentView()
}
