import SwiftUI

// MARK: - 疾病详情页（1:1 还原竞品设计）
struct DiseaseDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let diseaseId: Int
    let diseaseName: String
    
    @State private var disease: DiseaseDetailModel?
    @State private var isLoading = true
    @State private var selectedTab = 0
    @State private var isFavorited = false
    
    private let tabs = ["简介", "症状", "病因", "诊断", "治疗", "护理"]
    
    var body: some View {
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // 顶部导航栏
                navigationBar
                
                if isLoading {
                    Spacer()
                    ProgressView("加载中...")
                    Spacer()
                } else if let disease = disease {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(alignment: .leading, spacing: 0) {
                            // 健康百科标签
                            trustBadge
                            
                            // 疾病名称
                            diseaseHeader(disease)
                            
                            // 作者信息
                            authorInfo(disease)
                            
                            // Tab 导航
                            tabBar
                            
                            // 内容区域
                            contentSection(disease)
                        }
                    }
                    
                    // 底部工具栏
                    bottomToolbar
                } else {
                    Spacer()
                    VStack(spacing: ScaleFactor.spacing(12)) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: AdaptiveFont.custom(36)))
                            .foregroundColor(DXYColors.textTertiary)
                        Text("加载失败")
                            .font(.system(size: AdaptiveFont.subheadline))
                            .foregroundColor(DXYColors.textTertiary)
                        Button("重试") {
                            loadDiseaseDetail()
                        }
                        .foregroundColor(DXYColors.primaryPurple)
                    }
                    Spacer()
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            loadDiseaseDetail()
        }
    }
    
    // MARK: - 顶部导航栏
    private var navigationBar: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
                    .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                    .contentShape(Rectangle())
            }
            
            Spacer()
            
            HStack(spacing: ScaleFactor.spacing(16)) {
                Button(action: {}) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: AdaptiveFont.title3))
                        .foregroundColor(DXYColors.textSecondary)
                }
                
                Button(action: {}) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: AdaptiveFont.title3))
                        .foregroundColor(DXYColors.textSecondary)
                }
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, AdaptiveSpacing.item)
        .background(Color.white)
    }
    
    // MARK: - 信任标签
    private var trustBadge: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            Text("健康百科")
                .font(.system(size: AdaptiveFont.caption, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, ScaleFactor.padding(8))
                .padding(.vertical, ScaleFactor.padding(3))
                .background(DXYColors.primaryPurple)
                .clipShape(RoundedRectangle(cornerRadius: ScaleFactor.size(3)))
            
            Text("三甲医生专业编审 · 鑫琳医生官方出品")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textSecondary)
            
            Image(systemName: "chevron.right")
                .font(.system(size: AdaptiveFont.custom(10)))
                .foregroundColor(DXYColors.textTertiary)
            
            Spacer()
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, AdaptiveSpacing.item)
        .background(Color.white)
    }
    
    // MARK: - 疾病名称头部
    private func diseaseHeader(_ disease: DiseaseDetailModel) -> some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            Text(disease.name)
                .font(.system(size: AdaptiveFont.title1, weight: .bold))
                .foregroundColor(DXYColors.textPrimary)
            
            HStack(spacing: ScaleFactor.spacing(8)) {
                Text("就诊科室：")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textSecondary)
                
                Button(action: {}) {
                    HStack(spacing: ScaleFactor.spacing(4)) {
                        Text(disease.recommended_department ?? disease.department_name ?? "未知科室")
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.primaryPurple)
                        Image(systemName: "chevron.right")
                            .font(.system(size: AdaptiveFont.custom(10)))
                            .foregroundColor(DXYColors.primaryPurple)
                    }
                }
            }
            
            if let updatedAt = disease.updated_at {
                Text(formatDate(updatedAt) + " 修订")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textTertiary)
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, AdaptiveSpacing.item)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
    }
    
    // MARK: - 作者信息
    private func authorInfo(_ disease: DiseaseDetailModel) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 16) {
                if let authorName = disease.author_name {
                    AuthorCard(
                        avatar: disease.author_avatar,
                        name: authorName,
                        title: disease.author_title ?? "",
                        role: "词条作者"
                    )
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.vertical, AdaptiveSpacing.item)
        }
        .background(Color.white)
    }
    
    // MARK: - Tab 导航栏
    private var tabBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: ScaleFactor.spacing(24)) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                    Button(action: { selectedTab = index }) {
                        VStack(spacing: ScaleFactor.spacing(8)) {
                            Text(tab)
                                .font(.system(size: AdaptiveFont.subheadline, weight: selectedTab == index ? .semibold : .regular))
                                .foregroundColor(selectedTab == index ? DXYColors.textPrimary : DXYColors.textSecondary)
                            
                            Rectangle()
                                .fill(selectedTab == index ? DXYColors.primaryPurple : Color.clear)
                                .frame(height: ScaleFactor.size(2))
                        }
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
        }
        .padding(.top, LayoutConstants.compactSpacing)
        .background(Color.white)
    }
    
    // MARK: - 内容区域
    private func contentSection(_ disease: DiseaseDetailModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            let content: String? = {
                switch selectedTab {
                case 0: return disease.overview
                case 1: return disease.symptoms
                case 2: return disease.causes
                case 3: return disease.diagnosis
                case 4: return disease.treatment
                case 5: return disease.care
                default: return nil
                }
            }()
            
            if let content = content, !content.isEmpty {
                ContentCard(title: tabs[selectedTab], content: content)
            } else {
                VStack(spacing: ScaleFactor.spacing(12)) {
                    Image(systemName: "doc.text")
                        .font(.system(size: AdaptiveFont.custom(36)))
                        .foregroundColor(DXYColors.textTertiary)
                    Text("暂无\(tabs[selectedTab])内容")
                        .font(.system(size: AdaptiveFont.subheadline))
                        .foregroundColor(DXYColors.textTertiary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, ScaleFactor.padding(60))
            }
        }
        .padding(.top, AdaptiveSpacing.item)
    }
    
    // MARK: - 底部工具栏
    private var bottomToolbar: some View {
        HStack(spacing: 0) {
            ToolbarButton(icon: "list.bullet", title: "目录") {}
            ToolbarButton(icon: "text.bubble", title: "评价反馈") {}
            ToolbarButton(
                icon: isFavorited ? "star.fill" : "star",
                title: "收藏",
                isActive: isFavorited
            ) {
                isFavorited.toggle()
            }
        }
        .padding(.vertical, LayoutConstants.compactSpacing)
        .background(Color.white)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: -2)
    }
    
    // MARK: - 数据加载
    private func loadDiseaseDetail() {
        isLoading = true
        
        Task {
            do {
                let detail = try await APIService.shared.getDiseaseDetail(diseaseId: diseaseId)
                await MainActor.run {
                    disease = detail
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }
    
    // MARK: - 辅助方法
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy年MM月dd日"
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - 作者卡片
struct AuthorCard: View {
    let avatar: String?
    let name: String
    let title: String
    let role: String
    
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(10)) {
            // 头像
            if let avatar = avatar, !avatar.isEmpty {
                AsyncImage(url: URL(string: avatar)) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    Image(systemName: "person.circle.fill")
                        .font(.system(size: AdaptiveFont.custom(40)))
                        .foregroundColor(DXYColors.textTertiary)
                }
                .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
                .clipShape(Circle())
            } else {
                Image(systemName: "person.circle.fill")
                    .font(.system(size: AdaptiveFont.custom(44)))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                HStack(spacing: ScaleFactor.spacing(4)) {
                    Text(name)
                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                        .foregroundColor(DXYColors.textPrimary)
                    
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(Color.yellow)
                    
                    Text(role)
                        .font(.system(size: AdaptiveFont.caption))
                        .foregroundColor(DXYColors.textTertiary)
                }
                
                Text(title)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textSecondary)
                    .lineLimit(1)
            }
        }
        .padding(.vertical, ScaleFactor.padding(4))
    }
}

// MARK: - 内容卡片
struct ContentCard: View {
    let title: String
    let content: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack {
                Text(title)
                    .font(.system(size: AdaptiveFont.title3, weight: .bold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Text(title.uppercased())
                    .font(.system(size: AdaptiveFont.custom(10)))
                    .foregroundColor(DXYColors.textTertiary)
                    .padding(.leading, ScaleFactor.padding(4))
            }
            
            Rectangle()
                .fill(DXYColors.textPrimary)
                .frame(height: ScaleFactor.size(2))
                .frame(width: ScaleFactor.size(20))
            
            // 简单的 Markdown 渲染（仅支持段落）
            Text(parseMarkdown(content))
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
                .lineSpacing(ScaleFactor.spacing(6))
        }
        .padding(LayoutConstants.horizontalPadding)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall))
        .padding(.horizontal, LayoutConstants.horizontalPadding)
    }
    
    private func parseMarkdown(_ text: String) -> String {
        // 简单处理：移除 Markdown 标记
        var result = text
        result = result.replacingOccurrences(of: "**", with: "")
        result = result.replacingOccurrences(of: "__", with: "")
        result = result.replacingOccurrences(of: "##", with: "")
        result = result.replacingOccurrences(of: "#", with: "")
        result = result.replacingOccurrences(of: "- ", with: "• ")
        return result
    }
}

// MARK: - 底部工具栏按钮
struct ToolbarButton: View {
    let icon: String
    let title: String
    var isActive: Bool = false
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: ScaleFactor.spacing(4)) {
                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.title2))
                    .foregroundColor(isActive ? DXYColors.primaryPurple : DXYColors.textSecondary)
                
                Text(title)
                    .font(.system(size: AdaptiveFont.caption))
                    .foregroundColor(isActive ? DXYColors.primaryPurple : DXYColors.textSecondary)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Preview
#Preview {
    CompatibleNavigationStack {
        DiseaseDetailView(diseaseId: 1, diseaseName: "婴儿湿疹")
    }
}
