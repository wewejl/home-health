import Foundation
import SwiftUI
import Combine

// MARK: - 医嘱执行监督 ViewModel

@MainActor
class MedicalOrderViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var showError: Bool = false

    @Published var orders: [MedicalOrder] = []
    @Published var todayTasks: GroupedTasks = GroupedTasks()
    @Published var weeklyCompliance: WeeklyComplianceResponse?
    @Published var alerts: [Alert] = []
    @Published var familyBonds: [FamilyBond] = []

    @Published var selectedDate: Date = Date()

    // MARK: - Private Properties
    private var loadTasksTask: Task<Void, Never>?

    // MARK: - Computed Properties
    var todayTasksCount: Int { todayTasks.totalCount }
    var todayCompletedCount: Int { todayTasks.completedCount }
    var todayRate: Double { todayTasks.rate }
    var todayRatePercent: Int { Int(todayTasks.rate * 100) }

    var hasPendingTasks: Bool { !todayTasks.pending.isEmpty }
    var hasOverdueTasks: Bool { !todayTasks.overdue.isEmpty }
    var activeAlerts: [Alert] { alerts.filter { !$0.is_acknowledged } }

    // MARK: - Initialization

    init() {
        loadTodayTasks()
        loadWeeklyCompliance()
        loadAlerts()
    }

    // MARK: - Public Methods

    /// 加载今日任务
    func loadTodayTasks() {
        isLoading = true
        loadTasksTask?.cancel()

        loadTasksTask = Task {
            do {
                let dateFormatter = DateFormatter()
                dateFormatter.dateFormat = "yyyy-MM-dd"
                let dateString = dateFormatter.string(from: selectedDate)

                let response: TaskListResponse = try await APIService.shared.getDailyTasks(date: dateString)

                guard !Task.isCancelled else { return }

                todayTasks = GroupedTasks(
                    pending: response.pending,
                    completed: response.completed,
                    overdue: response.overdue
                )

                isLoading = false

            } catch let error as APIError {
                guard !Task.isCancelled else { return }
                isLoading = false
                showErrorMessage(error.localizedDescription)
            } catch {
                guard !Task.isCancelled else { return }
                isLoading = false
                showErrorMessage(error.localizedDescription)
            }
        }
    }

    /// 刷新今日任务
    func refreshTasks() {
        loadTodayTasks()
    }

    /// 切换日期
    func changeDate(to newDate: Date) {
        selectedDate = newDate
        loadTodayTasks()
    }

    /// 完成任务打卡
    func completeTask(
        taskId: Int,
        type: CompletionType,
        value: [String: String]? = nil,
        photoURL: String? = nil,
        notes: String? = nil
    ) async -> Bool {
        isLoading = true
        defer { isLoading = false }

        do {
            let request = CompletionRecordRequest(
                task_instance_id: taskId,
                completion_type: type.rawValue,
                value: value,
                photo_url: photoURL,
                notes: notes
            )

            _ = try await APIService.shared.completeTask(request: request)

            // 刷新任务列表
            loadTodayTasks()

            return true

        } catch let error as APIError {
            showErrorMessage(error.localizedDescription)
            return false
        } catch {
            showErrorMessage(error.localizedDescription)
            return false
        }
    }

    /// 加载周依从性
    func loadWeeklyCompliance() {
        Task {
            do {
                let response: WeeklyComplianceResponse = try await APIService.shared.getWeeklyCompliance()
                weeklyCompliance = response
            } catch {
                print("[MedicalOrderViewModel] Failed to load weekly compliance: \(error)")
            }
        }
    }

    /// 加载预警列表
    func loadAlerts() {
        Task {
            do {
                let response: [Alert] = try await APIService.shared.getAlerts(activeOnly: true)
                alerts = response
            } catch {
                print("[MedicalOrderViewModel] Failed to load alerts: \(error)")
            }
        }
    }

    /// 确认预警
    func acknowledgeAlert(alertId: Int) async -> Bool {
        do {
            _ = try await APIService.shared.acknowledgeAlert(alertId: alertId)
            // 重新加载预警列表
            loadAlerts()
            return true
        } catch {
            showErrorMessage("确认预警失败")
            return false
        }
    }

    /// 加载医嘱列表
    func loadOrders() {
        Task {
            do {
                let response: [MedicalOrder] = try await APIService.shared.getMedicalOrders()
                orders = response
            } catch {
                print("[MedicalOrderViewModel] Failed to load orders: \(error)")
            }
        }
    }

    /// 激活医嘱
    func activateOrder(orderId: Int) async -> Bool {
        isLoading = true
        defer { isLoading = false }

        do {
            let request = ActivateOrderRequest(confirm: true)
            let _: MedicalOrder = try await APIService.shared.activateOrder(orderId: orderId, request: request)
            await loadOrders()
            return true
        } catch {
            showErrorMessage("激活失败")
            return false
        }
    }

    // MARK: - Private Methods

    private func showErrorMessage(_ error: APIError) {
        errorMessage = error.errorDescription ?? "操作失败"
        showError = true

        // 触发震动反馈
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.error)
    }

    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true

        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.error)
    }

    // MARK: - Cleanup

    func cleanup() {
        loadTasksTask?.cancel()
        loadTasksTask = nil
    }

    deinit {
        loadTasksTask?.cancel()
    }
}

// MARK: - GroupedTasks is defined in MedicalOrderModels.swift
