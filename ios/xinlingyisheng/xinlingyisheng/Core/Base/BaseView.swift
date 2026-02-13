//
//  BaseView.swift
//  灵犀健康
//
//  创建日期: 2026-02-14
//  用途: 基础 View 协议

import SwiftUI

/// 基础 View 协议
///
/// 为所有 View 提供通用属性和方法
///
protocol BaseView: View {

    /// 空状态视图
    var emptyStateView: some View {
        EmptyStateView(icon: "doc.text.magnifyingglass", title: "暂无数据")
    }
}

extension View {

    /// 隐藏键盘
    func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil)
    }

    /// 条件显示
    @ViewBuilder func ifShow(_ condition: Bool) -> some View {
        if condition {
            self
        } else {
            EmptyView()
        }
    }

    /// 条件隐藏
    @ViewBuilder func ifHide(_ condition: Bool) -> some View {
        if !condition {
            self
        } else {
            EmptyView()
        }
    }
    }
}

// MARK: - Preview Provider

#if DEBUG
struct BaseView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Base View")
                .font(.title2)
            Text("Empty State View").render {
                EmptyStateView(icon: "doc.text.magnifyingglass", title: "暂无数据")
            }
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
