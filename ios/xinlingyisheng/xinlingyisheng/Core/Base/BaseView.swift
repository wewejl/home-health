//
//  BaseView.swift
//

import SwiftUI

protocol BaseView: View {
    var emptyStateView: AnyView { get }
}

extension View {
    func hideKeyboard() {
        let keyWindow = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first?.windows.first
        keyWindow?.endEditing(true)
    }
}
