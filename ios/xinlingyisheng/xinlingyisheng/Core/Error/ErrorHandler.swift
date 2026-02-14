//
//  ErrorHandler.swift
//  灵犀健康
//

import SwiftUI
import Combine

class ErrorHandler: ObservableObject {
    static let shared = ErrorHandler()

    @Published var error: AppError?
    @Published var isShowingError: Bool = false

    func show(_ error: AppError) {
        DispatchQueue.main.async { [weak self] in
            self?.error = error
            self?.isShowingError = true

            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                self?.isShowingError = false
            }
        }
    }

    func clear() {
        error = nil
        isShowingError = false
    }
}

#if DEBUG
struct ErrorHandler_Previews: PreviewProvider {
    static var previews: some View {
        Text("Error Handler")
            .font(.title2)
    }
}
#endif
