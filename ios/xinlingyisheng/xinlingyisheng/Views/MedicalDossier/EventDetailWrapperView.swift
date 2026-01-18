import SwiftUI

struct EventDetailWrapperView: View {
    let eventId: String
    @StateObject private var viewModel = MedicalDossierViewModel()
    @State private var event: MedicalEvent?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        Group {
            if isLoading {
                loadingView
            } else if let event = event {
                EventDetailView(event: event, viewModel: viewModel)
            } else {
                errorView
            }
        }
        .task {
            await loadEvent()
        }
    }
    
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            
            Text("正在加载病历详情...")
                .font(.system(size: 14))
                .foregroundColor(DXYColors.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(DXYColors.background)
    }
    
    private var errorView: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(DXYColors.textTertiary)
            
            Text(errorMessage ?? "加载失败")
                .font(.system(size: 16))
                .foregroundColor(DXYColors.textSecondary)
            
            Button(action: {
                Task {
                    await loadEvent()
                }
            }) {
                Text("重试")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 10)
                    .background(DXYColors.teal)
                    .clipShape(Capsule())
            }
            
            Button(action: { dismiss() }) {
                Text("返回")
                    .font(.system(size: 14))
                    .foregroundColor(DXYColors.textSecondary)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(DXYColors.background)
    }
    
    private func loadEvent() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let detailDTO = try await MedicalEventAPIService.shared.fetchEventDetail(eventId: eventId)
            self.event = detailDTO.toMedicalEvent()
            isLoading = false
        } catch {
            print("[EventDetailWrapper] 加载事件详情失败: \(error)")
            errorMessage = "加载失败，请重试"
            isLoading = false
        }
    }
}

#Preview {
    NavigationStack {
        EventDetailWrapperView(eventId: "123")
    }
}
