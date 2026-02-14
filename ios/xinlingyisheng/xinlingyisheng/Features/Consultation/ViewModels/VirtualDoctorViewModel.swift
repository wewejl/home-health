import Foundation
import Combine

/// 虚拟医生管理 ViewModel
@MainActor
class VirtualDoctorViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var doctors: [VirtualDoctor] = []
    @Published var personalities: [PersonalityConfig] = []
    @Published var specialties: [SpecialtyConfig] = []
    @Published var selectedDoctor: VirtualDoctorDetail?
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Dependencies
    private let apiService: VirtualDoctorAPIService

    init(apiService: VirtualDoctorAPIService = .shared) {
        self.apiService = apiService
    }

    // MARK: - Load Operations

    /// 加载虚拟医生列表
    func loadDoctors(departmentId: Int? = nil, personalityType: String? = nil) {
        Task {
            await loadDoctorsAsync(departmentId: departmentId, personalityType: personalityType)
        }
    }

    /// 加载性格类型列表
    func loadPersonalities() {
        Task {
            await loadPersonalitiesAsync()
        }
    }

    /// 加载科室类型列表
    func loadSpecialties() {
        Task {
            await loadSpecialtiesAsync()
        }
    }

    /// 加载医生详情
    func loadDoctorDetail(id: Int) {
        Task {
            await loadDoctorDetailAsync(id: id)
        }
    }

    // MARK: - Async Methods

    private func loadDoctorsAsync(departmentId: Int? = nil, personalityType: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiService.listVirtualDoctors(
                departmentId: departmentId,
                personalityType: personalityType
            )
            doctors = response.doctors
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "加载医生列表失败: \(error.localizedDescription)"
        }
    }

    private func loadPersonalitiesAsync() async {
        isLoading = true
        errorMessage = nil

        do {
            personalities = try await apiService.listPersonalities()
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "加载性格类型失败: \(error.localizedDescription)"
        }
    }

    private func loadSpecialtiesAsync() async {
        isLoading = true
        errorMessage = nil

        do {
            specialties = try await apiService.listSpecialties()
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "加载科室类型失败: \(error.localizedDescription)"
        }
    }

    private func loadDoctorDetailAsync(id: Int) async {
        isLoading = true
        errorMessage = nil

        do {
            selectedDoctor = try await apiService.getVirtualDoctorDetail(id: id)
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "加载医生详情失败: \(error.localizedDescription)"
        }
    }

    // MARK: - Helper Methods

    /// 根据代码获取性格配置
    func getPersonalityConfig(code: String) -> PersonalityConfig? {
        personalities.first { $0.code == code }
    }

    /// 根据代码获取科室配置
    func getSpecialtyConfig(code: String) -> SpecialtyConfig? {
        specialties.first { $0.code == code }
    }

    /// 获取性格显示名称
    func getPersonalityName(code: String) -> String {
        PersonalityType(rawValue: code)?.displayName ?? code
    }

    /// 格式化问候语
    func formatGreeting(template: String, doctorName: String) -> String {
        template.replacingOccurrences(of: "{name}", with: doctorName)
    }

    /// 清除错误
    func clearError() {
        errorMessage = nil
    }
}
