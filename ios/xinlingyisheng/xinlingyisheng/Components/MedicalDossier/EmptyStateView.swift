import SwiftUI

struct DossierEmptyStateView: View {
    var onStartConsultation: (() -> Void)?
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(24)) {
            Spacer()
            
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: ScaleFactor.size(64)))
                .foregroundColor(DXYColors.textTertiary)
            
            VStack(spacing: ScaleFactor.spacing(8)) {
                Text("还没有病历记录")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textSecondary)
                
                Text("与 AI 医生对话后，病历会自动生成")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
                    .multilineTextAlignment(.center)
            }
            
            if let action = onStartConsultation {
                Button(action: action) {
                    HStack(spacing: ScaleFactor.spacing(8)) {
                        Text("开始问诊")
                            .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        Image(systemName: "arrow.right")
                            .font(.system(size: AdaptiveFont.subheadline, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, ScaleFactor.padding(24))
                    .padding(.vertical, ScaleFactor.padding(14))
                    .background(DXYColors.primaryPurple)
                    .clipShape(Capsule())
                }
                .padding(.top, ScaleFactor.padding(8))
            }
            
            Spacer()
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
}

struct SearchEmptyStateView: View {
    let searchText: String
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: ScaleFactor.size(48)))
                .foregroundColor(DXYColors.textTertiary)
            
            Text("未找到相关病历")
                .font(.system(size: AdaptiveFont.body, weight: .medium))
                .foregroundColor(DXYColors.textSecondary)
            
            Text("尝试搜索其他关键词")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, ScaleFactor.padding(60))
    }
}

#Preview {
    VStack {
        DossierEmptyStateView(onStartConsultation: {})
        
        Divider()
        
        SearchEmptyStateView(searchText: "test")
    }
    .background(DXYColors.background)
}
