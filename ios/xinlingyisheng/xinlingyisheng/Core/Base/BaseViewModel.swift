//
//  BaseViewModel.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 基础 ViewModel 类

import SwiftUI
import Combine

/// 基础 ViewModel
///
/// 为所有 ViewModel 提供通用属性和方法
///
class BaseViewModel: ObservableObject {

    // MARK: - Published Properties

    @Published var isLoading: Bool = false

    @Published var isRefreshing: Bool = false

    @Published var error: AppError?

    // MARK: - Computed Properties

    /// 是否正在加载
    var isWorking: Bool {
        isLoading || isRefreshing
    }

    // MARK: - Public Methods

    /// 开始加载
    func startLoading() {
        isLoading = true
    error = nil
    }

    /// 结束加载
    func stopLoading() {
        isLoading = false
    }

    /// 设置错误
    func setError(_ error: AppError?) {
        self.error = error
    }

    /// 清除错误
    func clearError() {
        error = nil
    }
}
