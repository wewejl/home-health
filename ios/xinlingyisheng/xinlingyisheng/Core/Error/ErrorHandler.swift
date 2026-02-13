//
//  ErrorHandler.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 统一错误处理

import SwiftUI

/// 错误处理管理器
///
/// 提供统一的错误处理方法，包括显示提示、记录日志等
///
class ErrorHandler: ObservableObject {

    // MARK: - Shared Instance

    static let shared = ErrorHandler()

    // MARK: - Published Properties

    @Published var error: AppError?
    @Published var isShowingError: Bool = false

    // MARK: - Public Methods

    /// 显示错误
    func show(_ error: AppError) {
        DispatchQueue.main.async { [weak self] in
            self?.error = error
            self?.isShowingError = true

            // 记录日志
            #if DEBUG
            print("[ErrorHandler] \(error.userFriendlyMessage)")
            #endif

            // 3秒后自动隐藏
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                self?.isShowingError = false
            }
        }
    }

    /// 清除错误
    func clear() {
        error = nil
        isShowingError = false
    }
}

// MARK: - View Extension

extension View {

    /// 错误提示修饰器
    func onError(
        _ error: AppError,
        presenting: Binding<Bool>,
        handler: @escaping () -> Void = {}
    ) -> some View {
        let errorBinding = ErrorHandler.shared

        // 显示错误
        let _ = DispatchQueue.main.sync {
            errorBinding.show(error)
            presenting.wrappedValue = true
        }

        // 处理确认
        let confirmButton = AlertButton(
            text: Text("确认"),
            action: {
                handler()
                presenting.wrappedValue = false
            }
        )

        return alert(
            isPresented: presenting,
            title: Text("提示"),
            message: Text(errorBinding.error?.userFriendlyMessage ?? "操作失败"),
            dismissButton: confirmButton
        )
    }
}

// MARK: - Preview Provider

#if DEBUG
struct ErrorHandler_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Error Handling")
                .font(.title2)
            Text("Network Error")
                .foregroundColor(.red)
            Text("Auth Error")
                .foregroundColor(.orange)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
