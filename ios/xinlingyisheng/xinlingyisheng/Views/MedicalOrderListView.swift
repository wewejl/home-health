import SwiftUI

// MARK: - 医嘱任务列表视图（治愈系风格 + 响应式）

struct MedicalOrderListView: View {
    @StateObject private var viewModel = MedicalOrderViewModel()
    @State private var showTaskDetail: Bool = false
    @State private var selectedTask: TaskInstance?
    @State private var showAlerts: Bool = false

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingOrderBackground(layout: layout)

                ScrollView(.vertical, showsIndicators: false) {
                    LazyVStack(spacing: 0) {
                        // 顶部标题栏（替代导航栏）
                        headerSection(layout: layout)

                        // 顶部统计卡片
                        complianceHeader(layout: layout)

                        // 横向日期选择器
                        horizontalDatePickerSection(layout: layout)

                        // 任务列表
                        tasksSection(layout: layout)

                        Spacer(minLength: 32)
                    }
                }
            }
            .navigationBarHidden(true)
        }
        .overlay(alignment: .topTrailing) {
            // 预警按钮（替代 toolbar）
            Button {
                showAlerts.toggle()
            } label: {
                ZStack {
                    Circle()
                        .fill(HealingColors.terracotta.opacity(0.15))
                        .frame(width: 38, height: 38)
                        .shadow(color: Color.black.opacity(0.06), radius: 4, y: 2)

                    Image(systemName: "bell.badge")
                        .font(.system(size: UnifiedFont.subheadline))
                        .foregroundColor(HealingColors.terracotta)
                }
            }
            .padding(.trailing, ScaleFactor.padding(16))
            .padding(.top, ScaleFactor.padding(70))
        }
        .sheet(isPresented: $showTaskDetail) {
            if let task = selectedTask {
                SimplifiedTaskCompletionView(task: task, viewModel: viewModel)
            }
        }
        .sheet(isPresented: $showAlerts) {
            AlertsListView(alerts: viewModel.activeAlerts, viewModel: viewModel)
        }
        .onAppear {
            viewModel.refreshTasks()
        }
    }

    // MARK: - 顶部标题栏（响应式）
    private func headerSection(layout: AdaptiveLayout) -> some View {
        HStack {
            Text("医嘱任务")
                .font(.system(size: UnifiedFont.subheadline, weight: .bold))
                .foregroundColor(HealingColors.textPrimary)
            Spacer()
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing)
        .padding(.bottom, layout.cardSpacing / 2)
    }

    // MARK: - 依从性头部卡片（响应式）

    private func complianceHeader(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            // 今日完成率
            HStack(spacing: layout.cardSpacing) {
                VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                    Text("今日完成率")
                        .font(.system(size: UnifiedFont.footnote))
                        .foregroundColor(HealingColors.textSecondary)

                    Text("\(viewModel.todayRatePercent)%")
                        .font(.system(size: UnifiedFont.subheadline, weight: .bold))
                        .foregroundColor(rateColor)
                }

                Spacer()

                // 统计数据
                HStack(spacing: layout.cardSpacing) {
                    VStack(spacing: layout.cardSpacing / 3) {
                        Text("\(viewModel.todayCompletedCount)")
                            .font(.system(size: UnifiedFont.title3, weight: .bold))
                        Text("已完成")
                            .font(.system(size: UnifiedFont.caption1))
                            .foregroundColor(HealingColors.textTertiary)
                    }

                    VStack(spacing: layout.cardSpacing / 3) {
                        Text("\(viewModel.todayTasks.pending.count)")
                            .font(.system(size: UnifiedFont.title3, weight: .bold))
                            .foregroundColor(viewModel.todayTasks.pending.isEmpty ? HealingColors.textTertiary : HealingColors.textPrimary)
                        Text("待完成")
                            .font(.system(size: UnifiedFont.caption1))
                            .foregroundColor(HealingColors.textTertiary)
                    }

                    if viewModel.hasOverdueTasks {
                        VStack(spacing: layout.cardSpacing / 3) {
                            Text("\(viewModel.todayTasks.overdue.count)")
                                .font(.system(size: UnifiedFont.title3, weight: .bold))
                                .foregroundColor(HealingColors.terracotta)
                            Text("已超时")
                                .font(.system(size: UnifiedFont.caption1))
                                .foregroundColor(HealingColors.textTertiary)
                        }
                    }
                }
            }
            .padding(layout.cardInnerPadding)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .shadow(color: Color.black.opacity(0.04), radius: 10, x: 0, y: 4)
        }
        .padding(.horizontal, layout.horizontalPadding)
        .padding(.top, layout.cardSpacing)
    }

    // MARK: - 横向日期选择器（响应式）

    private func horizontalDatePickerSection(layout: AdaptiveLayout) -> some View {
        HorizontalDatePicker(
            selectedDate: $viewModel.selectedDate,
            onDateChanged: { newDate in
                viewModel.changeDate(to: newDate)
            }
        )
        .padding(.top, layout.cardSpacing)
    }

    // MARK: - 任务列表区域（响应式）

    private func tasksSection(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            // 待完成任务
            if !viewModel.todayTasks.pending.isEmpty {
                taskSection(
                    title: "待完成",
                    icon: "circle",
                    iconColor: HealingColors.warmSand,
                    tasks: viewModel.todayTasks.pending,
                    layout: layout
                )
            }

            // 已完成任务
            if !viewModel.todayTasks.completed.isEmpty {
                taskSection(
                    title: "已完成",
                    icon: "checkmark.circle.fill",
                    iconColor: HealingColors.forestMist,
                    tasks: viewModel.todayTasks.completed,
                    layout: layout
                )
            }

            // 已超时任务
            if !viewModel.todayTasks.overdue.isEmpty {
                taskSection(
                    title: "已超时",
                    icon: "exclamationmark.triangle.fill",
                    iconColor: HealingColors.terracotta,
                    tasks: viewModel.todayTasks.overdue,
                    layout: layout
                )
            }

            // 空状态
            if viewModel.todayTasks.pending.isEmpty &&
               viewModel.todayTasks.completed.isEmpty &&
               viewModel.todayTasks.overdue.isEmpty {
                emptyStateView(layout: layout)
            }
        }
        .padding(.horizontal, layout.horizontalPadding)
    }

    // MARK: - 任务分组（响应式）

    func taskSection(title: String, icon: String, iconColor: Color, tasks: [TaskInstance], layout: AdaptiveLayout) -> some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
            HStack(spacing: layout.cardSpacing / 2) {
                Image(systemName: icon)
                    .font(.system(size: UnifiedFont.footnote))
                    .foregroundColor(iconColor)
                Text(title)
                    .font(.system(size: UnifiedFont.body, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            ForEach(tasks) { task in
                TaskCard(task: task, layout: layout) {
                    showTaskDetail = true
                    selectedTask = task
                }
            }
        }
    }

    // MARK: - 空状态（响应式）

    private func emptyStateView(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)

                Image(systemName: "checkmark.circle")
                    .font(.system(size: UnifiedFont.body, weight: .light))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text("今日暂无任务")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)

            Text("享受健康生活")
                .font(.system(size: UnifiedFont.footnote))
                .foregroundColor(HealingColors.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, layout.cardInnerPadding * 6)
    }

    // MARK: - Computed Properties

    private var rateColor: Color {
        let rate = viewModel.todayRate
        if rate >= 0.8 {
            return HealingColors.forestMist
        } else if rate >= 0.6 {
            return HealingColors.warmSand
        } else {
            return HealingColors.terracotta
        }
    }
}

// MARK: - 治愈系医嘱背景 - 和首页一致
struct HealingOrderBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 纯色背景 - 和首页一致
            HealingColors.background
                .ignoresSafeArea()

            // 右上角装饰光晕
            Circle()
                .fill(HealingColors.softSage.opacity(0.06))
                .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                .offset(x: layout.decorativeCircleSize * 0.3, y: -layout.decorativeCircleSize * 0.1)
        }
    }
}

// MARK: - 任务卡片视图（响应式）

struct TaskCard: View {
    let task: TaskInstance
    let layout: AdaptiveLayout
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                HStack {
                    VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                        Text(task.order_title ?? "未命名任务")
                            .font(.system(size: UnifiedFont.subheadline, weight: .semibold))
                            .foregroundColor(HealingColors.textPrimary)

                        if let orderType = task.order_type, let type = OrderType(rawValue: orderType) {
                            HStack(spacing: layout.cardSpacing / 3) {
                                Label(type.displayName, systemImage: type.iconName)
                                    .font(.system(size: UnifiedFont.caption1))
                                    .foregroundColor(HealingColors.textSecondary)
                            }
                        }
                    }

                    Spacer()

                    Text(task.scheduled_time)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textTertiary)
                }

                // 额外信息
                if task.isCompleted, let completedAt = task.completed_at {
                    Text(completedAt)
                        .font(.system(size: UnifiedFont.caption1))
                        .foregroundColor(HealingColors.textTertiary)
                }
            }
            .padding(layout.cardInnerPadding)
            .background(HealingColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 预警列表视图（响应式）

struct AlertsListView: View {
    let alerts: [Alert]
    let viewModel: MedicalOrderViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            NavigationView {
                ZStack {
                    HealingColors.background
                        .ignoresSafeArea()

                    if alerts.isEmpty {
                        emptyState(layout: layout)
                    } else {
                        ScrollView {
                            LazyVStack(spacing: layout.cardSpacing / 2) {
                                ForEach(alerts) { alert in
                                    AlertCard(alert: alert, viewModel: viewModel, layout: layout)
                                }
                            }
                            .padding(layout.horizontalPadding)
                        }
                    }
                }
                .navigationBarHidden(true)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("关闭") { dismiss() }
                    }
                }
            }
        }
    }

    private func emptyState(layout: AdaptiveLayout) -> some View {
        VStack(spacing: layout.cardSpacing) {
            ZStack {
                Circle()
                    .fill(HealingColors.forestMist.opacity(0.1))
                    .frame(width: layout.iconLargeSize * 2, height: layout.iconLargeSize * 2)

                Image(systemName: "checkmark.shield")
                    .font(.system(size: UnifiedFont.body, weight: .light))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text("暂无预警")
                .font(.system(size: UnifiedFont.body, weight: .semibold))
                .foregroundColor(HealingColors.textPrimary)
        }
    }
}

// MARK: - 预警卡片（响应式）

struct AlertCard: View {
    let alert: Alert
    let viewModel: MedicalOrderViewModel
    let layout: AdaptiveLayout

    var body: some View {
        HStack(alignment: .top, spacing: layout.cardSpacing / 2) {
            Image(systemName: alert.iconName)
                .font(.system(size: UnifiedFont.title3))
                .foregroundColor(Color(alert.severityColor))
                .frame(width: layout.iconLargeSize + 4)

            VStack(alignment: .leading, spacing: layout.cardSpacing / 3) {
                Text(alert.title)
                    .font(.system(size: UnifiedFont.subheadline, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Text(alert.message)
                    .font(.system(size: UnifiedFont.footnote))
                    .foregroundColor(HealingColors.textSecondary)

                Text(alert.created_at)
                    .font(.system(size: UnifiedFont.caption1))
                    .foregroundColor(HealingColors.textTertiary)
            }

            Spacer()

            if !alert.is_acknowledged {
                Button("确认") {
                    Task {
                        await viewModel.acknowledgeAlert(alertId: alert.id)
                    }
                }
                .font(.system(size: UnifiedFont.caption1, weight: .medium))
                .foregroundColor(HealingColors.forestMist)
                .padding(.horizontal, layout.cardInnerPadding)
                .padding(.vertical, layout.cardSpacing / 2)
                .background(HealingColors.forestMist.opacity(0.15))
                .clipShape(Capsule())
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.03), radius: 6, x: 0, y: 2)
    }
}

// MARK: - Preview

#Preview {
    MedicalOrderListView()
}
