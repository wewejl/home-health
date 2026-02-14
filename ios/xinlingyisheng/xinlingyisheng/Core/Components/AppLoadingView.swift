//
//  AppLoadingView.swift
//  灵犀健康
//

import SwiftUI

struct AppLoadingView: View {
    let isLoading: Bool
    let message: String?

    var body: some View {
        if isLoading {
            VStack(spacing: AppSpacing.small) {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
                
                if let message = message {
                    Text(message)
                        .font(.caption)
                }
            }
        } else {
            EmptyView()
        }
    }

    init(isLoading: Bool = true, message: String? = nil) {
        self.isLoading = isLoading
        self.message = message
    }
}

#if DEBUG
struct AppLoadingView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            AppLoadingView(message: "加载中...")
            AppLoadingView()
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
