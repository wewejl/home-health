import SwiftUI

/// 统一的错误提示横幅
struct ErrorBanner: View {
    let error: Error?
    let onDismiss: () -> Void

    var body: some View {
        if let appError = error?.toAppError {
            HStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)

                VStack(alignment: .leading, spacing: 4) {
                    Text(appError.errorDescription ?? "未知错误")
                        .font(.subheadline)
                        .foregroundColor(.primary)

                    if let suggestion = appError.recoverySuggestion {
                        Text(suggestion)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .background(Color.red.opacity(0.1))
            .cornerRadius(8)
        }
    }
}

// MARK: - Error Extension

extension Error {
    /// 转换为 AppError
    var toAppError: AppError {
        if let appError = self as? AppError {
            return appError
        }
        if let apiError = self as? APIError {
            return apiError.toAppError
        }
        return .unknown
    }
}

// MARK: - Preview

struct ErrorBanner_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            ErrorBanner(error: AppError.networkUnavailable) {}
            ErrorBanner(error: AppError.unauthorized) {}
            ErrorBanner(error: AppError.timeout) {}
        }
        .padding()
    }
}
