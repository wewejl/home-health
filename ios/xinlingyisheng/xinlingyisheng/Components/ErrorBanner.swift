//
//  ErrorBanner.swift
//

import SwiftUI

struct ErrorBanner: View {
    let error: String?
    let onDismiss: () -> Void

    var body: some View {
        if let error = error {
            HStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)
                Text(error)
                    .font(.subheadline)
                Spacer()
                Button("关闭") { onDismiss() }
            }
            .padding()
            .background(Color.red.opacity(0.1))
        }
    }
}

#if DEBUG
struct ErrorBanner_Previews: PreviewProvider {
    static var previews: some View {
        ErrorBanner(error: "发生错误", onDismiss: {})
            .padding()
    }
}
#endif
