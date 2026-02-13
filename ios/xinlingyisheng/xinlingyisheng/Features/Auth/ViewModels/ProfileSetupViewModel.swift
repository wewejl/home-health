import Foundation
import SwiftUI
import Combine

// MARK: - ProfileSetupViewModel
@MainActor
class ProfileSetupViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var nickname: String = ""
    @Published var selectedGender: Gender = .notSet
    @Published var birthday: Date = Calendar.current.date(byAdding: .year, value: -30, to: Date()) ?? Date()
    @Published var showBirthdayPicker: Bool = false
    @Published var emergencyContactName: String = ""
    @Published var emergencyContactPhone: String = ""
    @Published var emergencyContactRelation: String = ""
    
    @Published var isLoading: Bool = false
    @Published var showError: Bool = false
    @Published var errorMessage: String = ""
    @Published var isCompleted: Bool = false
    
    // MARK: - Gender Enum
    enum Gender: String, CaseIterable {
        case notSet = ""
        case male = "male"
        case female = "female"
        case other = "other"
        
        var displayName: String {
            switch self {
            case .notSet: return "请选择"
            case .male: return "男"
            case .female: return "女"
            case .other: return "其他"
            }
        }
    }
    
    // MARK: - Computed Properties
    var isFormValid: Bool {
        !nickname.trimmingCharacters(in: .whitespaces).isEmpty && selectedGender != .notSet
    }
    
    var formattedBirthday: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: birthday)
    }
    
    var displayBirthday: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy年MM月dd日"
        return formatter.string(from: birthday)
    }
    
    var isEmergencyContactValid: Bool {
        if emergencyContactPhone.isEmpty { return true }
        let phoneRegex = "^1[3-9]\\d{9}$"
        return emergencyContactPhone.range(of: phoneRegex, options: .regularExpression) != nil
    }
    
    // MARK: - Initialization
    init() {
        loadCurrentUserData()
    }
    
    private func loadCurrentUserData() {
        guard let user = AuthManager.shared.currentUser else { return }
        
        nickname = user.nickname ?? ""
        
        if let gender = user.gender {
            selectedGender = Gender(rawValue: gender) ?? .notSet
        }
        
        if let birthdayStr = user.birthday {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            if let date = formatter.date(from: birthdayStr) {
                birthday = date
            }
        }
        
        emergencyContactName = user.emergency_contact_name ?? ""
        emergencyContactPhone = user.emergency_contact_phone ?? ""
        emergencyContactRelation = user.emergency_contact_relation ?? ""
    }
    
    // MARK: - Public Methods
    func submitProfile() {
        guard isFormValid else {
            showErrorMessage("请填写昵称和性别")
            return
        }
        
        guard isEmergencyContactValid else {
            showErrorMessage("请输入正确的紧急联系人手机号")
            return
        }
        
        Task {
            await performSubmit()
        }
    }
    
    func skipSetup() {
        isCompleted = true
        logEvent("profile_setup_skipped")
    }
    
    // MARK: - Private Methods
    private func performSubmit() async {
        isLoading = true
        
        let request = ProfileUpdateRequest(
            nickname: nickname.trimmingCharacters(in: .whitespaces),
            avatar_url: nil,
            gender: selectedGender.rawValue.isEmpty ? nil : selectedGender.rawValue,
            birth_date: formattedBirthday,
            emergency_contact_phone: emergencyContactPhone.isEmpty ? nil : emergencyContactPhone,
            emergency_contact_relation: emergencyContactRelation.isEmpty ? nil : emergencyContactRelation
        )
        
        do {
            let updatedUser = try await APIService.shared.completeProfile(request: request)
            
            AuthManager.shared.updateUser(updatedUser)
            
            isLoading = false
            isCompleted = true
            
            logEvent("profile_setup_completed")
            
        } catch let error as APIError {
            isLoading = false
            showErrorMessage(error.errorDescription ?? "保存失败，请重试")
            logEvent("profile_setup_failed", data: ["error": error.errorDescription ?? "unknown"])
        } catch {
            isLoading = false
            showErrorMessage("网络错误，请重试")
            logEvent("profile_setup_failed", data: ["error": error.localizedDescription])
        }
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
        
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.error)
    }
    
    private func logEvent(_ event: String, data: [String: Any] = [:]) {
        // TODO: 接入正式埋点系统
        var logData: [String: Any] = ["event": event]
        logData.merge(data) { _, new in new }
        print("[ProfileSetupEvent] \(logData)")
    }
}
