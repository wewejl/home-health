import SwiftUI

// MARK: - 药品详情页
struct DrugDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let drugId: Int
    let drugName: String
    
    @State private var drug: DrugDetailModel?
    @State private var isLoading = true
    @State private var selectedTab = 0
    @State private var isFavorited = false
    
    private let tabs = ["功效作用", "用药禁忌", "用法用量"]
    
    var body: some View {
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                navigationBar
                
                if isLoading {
                    Spacer()
                    ProgressView("加载中...")
                    Spacer()
                } else if let drug = drug {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(alignment: .leading, spacing: 0) {
                            trustBadge
                            drugHeader(drug)
                            safetyLabels(drug)
                            tabBar
                            contentSection(drug)
                        }
                    }
                    
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
                            loadDrugDetail()
                        }
                        .foregroundColor(DXYColors.primaryPurple)
                    }
                    Spacer()
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            loadDrugDetail()
        }
    }
    
    // MARK: - 顶部导航栏
    private var navigationBar: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3, weight: .medium))
                    .foregroundColor(DXYColors.textPrimary)
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
    
    // MARK: - 药品名称头部
    private func drugHeader(_ drug: DrugDetailModel) -> some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(8)) {
            Text(drug.name)
                .font(.system(size: AdaptiveFont.title1, weight: .bold))
                .foregroundColor(DXYColors.textPrimary)
            
            if let commonBrands = drug.common_brands, !commonBrands.isEmpty {
                Text("常见商品名：\(commonBrands)")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textSecondary)
            }
            
            if let reviewerInfo = drug.reviewer_info {
                HStack(spacing: ScaleFactor.spacing(6)) {
                    if let authorAvatar = drug.author_avatar, !authorAvatar.isEmpty {
                        AsyncImage(url: URL(string: authorAvatar)) { image in
                            image
                                .resizable()
                                .scaledToFill()
                        } placeholder: {
                            Image(systemName: "person.circle.fill")
                                .font(.system(size: AdaptiveFont.title2))
                                .foregroundColor(DXYColors.textTertiary)
                        }
                        .frame(width: ScaleFactor.size(20), height: ScaleFactor.size(20))
                        .clipShape(Circle())
                    }
                    
                    Text(reviewerInfo)
                        .font(.system(size: AdaptiveFont.footnote))
                        .foregroundColor(DXYColors.textTertiary)
                    
                    Image(systemName: "chevron.right")
                        .font(.system(size: AdaptiveFont.custom(10)))
                        .foregroundColor(DXYColors.textTertiary)
                }
            }
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.vertical, AdaptiveSpacing.item)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
    }
    
    // MARK: - 安全标签
    private func safetyLabels(_ drug: DrugDetailModel) -> some View {
        HStack(spacing: 0) {
            // 孕期安全
            SafetyLabelView(
                icon: "doc.text",
                title: "孕期较安全",
                subtitle: drug.pregnancy_desc ?? "妊娠分级 \(drug.pregnancy_level ?? "-")"
            )
            
            Divider()
                .frame(height: ScaleFactor.size(40))
            
            // 哺乳期安全
            SafetyLabelView(
                icon: "lock.shield",
                title: "哺乳期较安全",
                subtitle: drug.lactation_desc ?? "哺乳分级 \(drug.lactation_level ?? "-")"
            )
            
            Divider()
                .frame(height: ScaleFactor.size(40))
            
            // 儿童可用
            SafetyLabelView(
                icon: "person.2",
                title: drug.children_usable ? "儿童可用" : "儿童慎用",
                subtitle: drug.children_desc ?? "儿童用药参考"
            )
        }
        .padding(.vertical, AdaptiveSpacing.item)
        .background(Color.white)
    }
    
    // MARK: - Tab 导航栏
    private var tabBar: some View {
        HStack(spacing: 0) {
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
                .frame(maxWidth: .infinity)
            }
        }
        .padding(.top, LayoutConstants.compactSpacing)
        .background(Color.white)
    }
    
    // MARK: - 内容区域
    private func contentSection(_ drug: DrugDetailModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            let content: String? = {
                switch selectedTab {
                case 0: return drug.indications
                case 1: return drug.contraindications
                case 2: return drug.dosage
                default: return nil
                }
            }()
            
            if let content = content, !content.isEmpty {
                DrugContentCard(title: tabs[selectedTab], content: content)
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
            DrugToolbarButton(icon: "list.bullet", title: "目录") {}
            DrugToolbarButton(icon: "text.bubble", title: "评价反馈") {}
            DrugToolbarButton(
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
    private func loadDrugDetail() {
        isLoading = true
        
        Task {
            do {
                let detail = try await APIService.shared.getDrugDetail(drugId: drugId)
                await MainActor.run {
                    drug = detail
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }
}

// MARK: - 安全标签视图
struct SafetyLabelView: View {
    let icon: String
    let title: String
    let subtitle: String
    
    var body: some View {
        VStack(spacing: ScaleFactor.spacing(4)) {
            Image(systemName: icon)
                .font(.system(size: AdaptiveFont.title2))
                .foregroundColor(DXYColors.primaryPurple)
            
            Text(title)
                .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                .foregroundColor(DXYColors.textPrimary)
            
            HStack(spacing: ScaleFactor.spacing(2)) {
                Text(subtitle)
                    .font(.system(size: AdaptiveFont.custom(10)))
                    .foregroundColor(DXYColors.textTertiary)
                
                Image(systemName: "chevron.right")
                    .font(.system(size: AdaptiveFont.custom(8)))
                    .foregroundColor(DXYColors.textTertiary)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - 药品内容卡片
struct DrugContentCard: View {
    let title: String
    let content: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack {
                Text(title)
                    .font(.system(size: AdaptiveFont.title3, weight: .bold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Text("INDICATIONS")
                    .font(.system(size: AdaptiveFont.custom(10)))
                    .foregroundColor(DXYColors.textTertiary)
                    .padding(.leading, ScaleFactor.padding(4))
            }
            
            Rectangle()
                .fill(DXYColors.textPrimary)
                .frame(height: ScaleFactor.size(2))
                .frame(width: ScaleFactor.size(20))
            
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
        var result = text
        result = result.replacingOccurrences(of: "**", with: "")
        result = result.replacingOccurrences(of: "__", with: "")
        result = result.replacingOccurrences(of: "##", with: "")
        result = result.replacingOccurrences(of: "#", with: "")
        result = result.replacingOccurrences(of: "- ", with: "• ")
        return result
    }
}

// MARK: - 药品底部工具栏按钮
struct DrugToolbarButton: View {
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
        DrugDetailView(drugId: 1, drugName: "阿奇霉素")
    }
}
