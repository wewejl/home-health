//
//  OneClickLoginView.swift
//  鑫琳医生 - 一键登录界面
//
//  阿里云号码认证一键登录
//

import SwiftUI

struct OneClickLoginView: View {
    @StateObject private var authService = OneClickAuthService.shared
    @State private var showLoginMethodSelection = false
    @State private var showVerificationLogin = false
    @State private var showPasswordLogin = false
    @State private var isLoading = false
    @State private var errorMessage: String?

    // 检查网络环境（仅移动网络支持一键登录）
    private var isCellularNetwork: Bool {
        // TODO: 实际应检查网络类型
        return true  // 开发模式默认返回 true
    }

    var body: some View {
        VStack(spacing: 0) {
            // 顶部Logo和标题
            Spacer()
                .frame(height: 80)

            // Logo
            Image(systemName: "heart.fill")
                .font(.system(size: 60))
                .foregroundStyle(
                    LinearGradient(
                        colors: [Color(hex: "3B82F6"), Color(hex: "8B5CF6")],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            Text("鑫琳医生")
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(.primary)
                .padding(.top, 16)

            Text("智能健康管理")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .padding(.top, 4)

            Spacer()

            // 一键登录按钮
            if isCellularNetwork {
                Button(action: handleOneClickLogin) {
                    ZStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            HStack(spacing: 8) {
                                Image(systemName: "antenna.radiowaves.left.and.right")
                                    .font(.system(size: 20))
                                Text("一键登录")
                                }
                                .font(.headline)
                                .foregroundColor(.white)
                        }
                    }
                    .frame(height: 50)
                    .frame(maxWidth: .infinity)
                    .background(
                        LinearGradient(
                            colors: [Color(hex: "3B82F6"), Color(hex: "8B5CF6")],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(12)
                }
                .disabled(isLoading)
                .padding(.horizontal, 24)
            } else {
                // 非移动网络提示
                VStack(spacing: 12) {
                    Image(systemName: "wifi.slash")
                        .font(.system(size: 40))
                        .foregroundColor(.orange)

                    Text("请使用移动数据网络")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Text("一键登录功能仅支持 4G/5G 网络")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding()
            }

            // 错误提示
            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.top, 8)
            }

            // 其他登录方式
            VStack(spacing: 16) {
                Divider()
                    .padding(.vertical, 8)

                HStack(spacing: 8) {
                    Button("验证码登录") {
                        showVerificationLogin = true
                    }
                    .font(.subheadline)
                    .foregroundColor(.blue)

                    Text("|")
                        .foregroundColor(.secondary)

                    Button("密码登录") {
                        showPasswordLogin = true
                    }
                    .font(.subheadline)
                    .foregroundColor(.blue)
                }

                // 协议同意
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.square.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.blue)

                    Text("我已阅读并同意")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Button("用户协议") {}
                        .font(.caption)
                        .foregroundColor(.blue)

                    Text("和")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Button("隐私政策") {}
                        .font(.caption)
                        .foregroundColor(.blue)
                }
                .padding(.bottom, 32)
            }
            .padding(.horizontal, 24)
        }
        .navigationBarHidden(true)
        .alert("登录失败", isPresented: .constant(errorMessage != nil)) {
            Button("确定") {
                errorMessage = nil
            }
        } message: {
            if let error = errorMessage {
                Text(error)
            }
        }
    }

    // MARK: - 一键登录处理
    private func handleOneClickLogin() {
        isLoading = true
        errorMessage = nil

        Task {
            do {
                let result = try await OneClickAuthService.shared.oneClickLogin()

                // 登录成功
                await MainActor.run {
                    AuthManager.shared.login(
                        token: result.token,
                        refreshToken: result.refreshToken,
                        user: result.user,
                        isNewUser: result.isNewUser
                    )
                    isLoading = false
                }

            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription
                }
            }
        }
    }
}
// MARK: - Preview
#Preview {
    NavigationView {
        OneClickLoginView()
    }
}
