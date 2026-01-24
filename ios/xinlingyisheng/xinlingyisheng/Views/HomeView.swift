import SwiftUI

// MARK: - 自适应布局助手
struct AdaptiveLayout {
    let screenWidth: CGFloat

    // 屏幕尺寸分类
    var isCompact: Bool { screenWidth < 380 }  // iPhone SE
    var isRegular: Bool { screenWidth >= 380 && screenWidth < 400 }  // iPhone 13/14
    var isLarge: Bool { screenWidth >= 400 }  // iPhone Pro Max

    // 相对尺寸 - 基于屏幕宽度的比例
    var iconScale: CGFloat {
        isCompact ? 0.85 : (isLarge ? 1.1 : 1.0)
    }

    var paddingScale: CGFloat {
        isCompact ? 0.8 : (isLarge ? 1.2 : 1.0)
    }

    var cardSpacing: CGFloat {
        isCompact ? 12 : 16
    }

    // 今日健康卡片高度 - 自适应
    var todayCardHeight: CGFloat {
        isCompact ? 100 : 120
    }

    // 快速卡片高度
    var quickCardLargeHeight: CGFloat {
        isCompact ? 130 : 150
    }

    var quickCardSmallHeight: CGFloat {
        isCompact ? 58 : 66
    }

    // 图标尺寸
    var iconLargeSize: CGFloat { (isCompact ? 42 : 48) * iconScale }
    var iconSmallSize: CGFloat { (isCompact ? 32 : 38) * iconScale }

    // 装饰光晕尺寸 - 相对屏幕宽度
    var decorativeCircleSize: CGFloat { screenWidth * 0.5 }

    // 内边距
    var horizontalPadding: CGFloat { isCompact ? 16 : 20 }

    // 文字尺寸
    var titleFontSize: CGFloat { isCompact ? 18 : 20 }
    var bodyFontSize: CGFloat { isCompact ? 15 : 17 }
    var captionFontSize: CGFloat { isCompact ? 11 : 12 }

    // 卡片内边距
    var cardInnerPadding: CGFloat { isCompact ? 12 : 16 }
}

// MARK: - 治愈系日式色彩系统
struct HealingColors {
    // 主色系 - 柔和的鼠尾草绿
    static let softSage = Color(red: 0.71, green: 0.82, blue: 0.76)          // #B5D1C2
    static let deepSage = Color(red: 0.45, green: 0.62, blue: 0.54)          // #739E89
    static let forestMist = Color(red: 0.32, green: 0.48, blue: 0.42)        // #517A6B

    // 温暖系 - 奶油与陶土
    static let warmCream = Color(red: 0.97, green: 0.95, blue: 0.91)         // #F7F2E8
    static let softPeach = Color(red: 0.96, green: 0.90, blue: 0.85)         // #F5E6D9
    static let terracotta = Color(red: 0.82, green: 0.52, blue: 0.42)        // #D1856B
    static let warmSand = Color(red: 0.88, green: 0.82, blue: 0.74)          // #E0D2BD

    // 点缀色
    static let mutedCoral = Color(red: 0.90, green: 0.62, blue: 0.55)        // #E69E8D
    static let dustyBlue = Color(red: 0.65, green: 0.72, blue: 0.80)         // #A6B8CC
    static let lavenderHaze = Color(red: 0.78, green: 0.73, blue: 0.85)      // #C7BAD9

    // 功能色
    static let background = warmCream
    static let cardBackground = Color.white
    static let textPrimary = Color(red: 0.22, green: 0.22, blue: 0.20)       // #383833
    static let textSecondary = Color(red: 0.42, green: 0.42, blue: 0.40)      // #6B6B66
    static let textTertiary = Color(red: 0.62, green: 0.62, blue: 0.60)      // #9E9E99
}

// MARK: - DXYColors 兼容层
struct DXYColors {
    static let primaryPurple = HealingColors.forestMist
    static let lightPurple = HealingColors.softSage.opacity(0.3)
    static let teal = HealingColors.deepSage
    static let blue = HealingColors.dustyBlue
    static let orange = HealingColors.terracotta
    static let background = HealingColors.background
    static let cardBackground = HealingColors.cardBackground
    static let searchBackground = HealingColors.warmSand
    static let tagBackground = HealingColors.warmSand.opacity(0.6)
    static let textPrimary = HealingColors.textPrimary
    static let textSecondary = HealingColors.textSecondary
    static let textTertiary = HealingColors.textTertiary
    static let promotionPurple = HealingColors.softSage.opacity(0.25)
    static let promotionOrange = HealingColors.mutedCoral.opacity(0.25)
}

// MARK: - 流畅进入动画
struct FluidFadeIn: ViewModifier {
    var delay: Double = 0
    var duration: Double = 0.8

    @State private var opacity: Double = 0
    @State private var offset: CGFloat = 20

    func body(content: Content) -> some View {
        content
            .opacity(opacity)
            .offset(y: offset)
            .animation(.spring(response: duration, dampingFraction: 0.8).delay(delay), value: opacity)
            .animation(.spring(response: duration, dampingFraction: 0.8).delay(delay), value: offset)
            .onAppear {
                opacity = 1
                offset = 0
            }
    }
}

extension View {
    func fluidFadeIn(delay: Double = 0, duration: Double = 0.8) -> some View {
        self.modifier(FluidFadeIn(delay: delay, duration: duration))
    }
}

// MARK: - 脉冲动画
struct PulseAnimation: ViewModifier {
    @State private var isPulsing = false

    func body(content: Content) -> some View {
        content
            .scaleEffect(isPulsing ? 1.05 : 1.0)
            .animation(.easeInOut(duration: 2).repeatForever(autoreverses: true), value: isPulsing)
            .onAppear {
                isPulsing = true
            }
    }
}

extension View {
    func pulsing() -> some View {
        self.modifier(PulseAnimation())
    }
}

// MARK: - 主 HomeView
struct HomeView: View {
    @State private var selectedTab = 0
    // 每个 tab 的导航路径，用于在切换 tab 时重置导航栈
    @State private var tab0Path: [String] = []
    @State private var tab1Path: [String] = []
    @State private var tab2Path: [String] = []
    @State private var tab3Path: [String] = []
    @State private var tab4Path: [String] = []

    // 上次选中的 tab，用于检测切换并重置导航路径
    @State private var previousTab: Int? = nil

    init() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(HealingColors.warmCream)
        appearance.shadowColor = UIColor.black.withAlphaComponent(0.05)

        // 选中的 Tab
        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(HealingColors.forestMist)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(HealingColors.forestMist),
            .font: UIFont.systemFont(ofSize: 11, weight: .medium)
        ]

        // 未选中的 Tab
        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(HealingColors.textTertiary).withAlphaComponent(0.8)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(HealingColors.textTertiary).withAlphaComponent(0.8),
            .font: UIFont.systemFont(ofSize: 11, weight: .regular)
        ]

        // Inline layout (iPad)
        appearance.inlineLayoutAppearance.selected.iconColor = UIColor(HealingColors.forestMist)
        appearance.inlineLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(HealingColors.forestMist)]
        appearance.inlineLayoutAppearance.normal.iconColor = UIColor(HealingColors.textTertiary)
        appearance.inlineLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(HealingColors.textTertiary)]

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            // 首页 - 使用 path 管理导航栈
            CompatibleNavigationStack(path: $tab0Path) {
                HealingHomeContentView(
                    selectedTab: $selectedTab,
                    showDrugList: $showDrugList,
                    showDiseaseList: $showDiseaseList
                )
                .navigationDestinationCompat(isPresented: $showDrugList) {
                    DrugListView().navigationBarBackgroundHidden()
                }
                .navigationDestinationCompat(isPresented: $showDiseaseList) {
                    DiseaseListView().navigationBarBackgroundHidden()
                }
            }
            .tabItem {
                Image(systemName: selectedTab == 0 ? "heart.fill" : "heart")
                Text("首页")
            }
            .tag(0)

            CompatibleNavigationStack {
                AskDoctorView()
            }
            .tabItem {
                Image(systemName: selectedTab == 1 ? "message.badge.fill" : "message.badge")
                Text("问医生")
            }
            .tag(1)

            CompatibleNavigationStack {
                MedicalOrderListView()
            }
            .tabItem {
                Image(systemName: selectedTab == 2 ? "checkmark.seal.fill" : "checkmark.seal")
                Text("医嘱")
            }
            .tag(2)

            CompatibleNavigationStack {
                MedicalDossierView()
            }
            .tabItem {
                Image(systemName: selectedTab == 3 ? "folder.badge.fill" : "folder.badge")
                Text("病历")
            }
            .tag(3)

            CompatibleNavigationStack {
                ProfileView()
            }
            .tabItem {
                Image(systemName: selectedTab == 4 ? "person.circle.fill" : "person.circle")
                Text("我的")
            }
            .tag(4)
        }
        .tint(HealingColors.forestMist)
        .onChangeCompat(of: selectedTab) { newValue in
            // 切换 tab 时，重置目标 tab 的导航路径
            resetNavigationPath(for: newValue)
        }
    }

    // 重置指定 tab 的导航路径
    private func resetNavigationPath(for tab: Int) {
        switch tab {
        case 0:
            tab0Path.removeAll()
            // 重置首页的导航状态，确保回到首页根视图
            showDrugList = false
            showDiseaseList = false
        case 1:
            tab1Path.removeAll()
        case 2:
            tab2Path.removeAll()
        case 3:
            tab3Path.removeAll()
        case 4:
            tab4Path.removeAll()
        default:
            break
        }
    }

    // 首页的导航状态
    @State private var showDrugList = false
    @State private var showDiseaseList = false
}

// MARK: - 治愈系首页内容
struct HealingHomeContentView: View {
    @Binding var selectedTab: Int
    @Binding var showDrugList: Bool
    @Binding var showDiseaseList: Bool
    @State private var searchText = ""
    @State private var scrollOffset: CGFloat = 0

    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack(alignment: .topLeading) {
                // 背景装饰 - 柔和的光晕
                HealingColors.background
                    .ignoresSafeArea()

                // 右上角装饰光晕 - 使用相对尺寸
                Circle()
                    .fill(HealingColors.softSage.opacity(0.12))
                    .frame(width: layout.decorativeCircleSize, height: layout.decorativeCircleSize)
                    .offset(x: layout.decorativeCircleSize * 0.5, y: -layout.decorativeCircleSize * 0.25)
                    .ignoresSafeArea()

                // 左下角装饰光晕 - 使用相对尺寸
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.9, height: layout.decorativeCircleSize * 0.9)
                    .offset(x: -layout.decorativeCircleSize * 0.3, y: geometry.size.height * 0.5)
                    .ignoresSafeArea()

                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        // 顶部间距 - 自适应
                        Spacer().frame(height: layout.cardSpacing)

                        // 主内容区
                        VStack(spacing: layout.cardSpacing + 8) {
                            // 头部问候区
                            HealingGreetingHeader(searchText: $searchText, layout: layout)
                                .fluidFadeIn(delay: 0)

                            // 今日健康卡片 - 传递布局参数
                            HealingTodayCard(selectedTab: $selectedTab, layout: layout)
                                .fluidFadeIn(delay: 0.1)

                            // 快速功能 - 传递布局参数和导航绑定
                            HealingQuickActions(
                                selectedTab: $selectedTab,
                                showDrugList: $showDrugList,
                                showDiseaseList: $showDiseaseList,
                                layout: layout
                            )
                            .fluidFadeIn(delay: 0.2)

                            // 科室导航 - 传递布局参数
                            HealingDepartmentSection(layout: layout)
                                .fluidFadeIn(delay: 0.3)

                            // 健康资讯
                            HealingHealthTips(layout: layout)
                                .fluidFadeIn(delay: 0.4)
                        }
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.bottom, 140)
                    }
                }
            }
        }
        .navigationBarHidden(true)
    }
}

// MARK: - 问候头部
struct HealingGreetingHeader: View {
    @Binding var searchText: String
    let layout: AdaptiveLayout
    @State private var userName = "朋友"

    var body: some View {
        HStack(alignment: .center) {
            // 左侧 - 品牌与问候
            VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                HStack(spacing: layout.cardSpacing / 2) {
                    // 品牌 Logo - 自适应尺寸
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [HealingColors.softSage, HealingColors.deepSage],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 32 * layout.iconScale, height: 32 * layout.iconScale)

                        Image(systemName: "heart.fill")
                            .font(.system(size: 13 * layout.iconScale, weight: .medium))
                            .foregroundColor(.white)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("鑫琳医生")
                            .font(.system(size: layout.titleFontSize - 2, weight: .bold))
                            .foregroundColor(HealingColors.textPrimary)

                        Text("AI 健康管家 · 随时守护")
                            .font(.system(size: layout.captionFontSize, weight: .regular))
                            .foregroundColor(HealingColors.textTertiary)
                    }
                }

                // 问候语
                HStack(spacing: 6) {
                    Text(getGreeting())
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    Text("，" + userName)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }
                .padding(.top, 4)
            }

            Spacer()

            // 右侧 - 操作按钮
            HStack(spacing: 14) {
                // 搜索按钮
                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.softSage.opacity(0.2))
                            .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(HealingColors.forestMist)
                    }
                }
                .buttonStyle(ScaleButtonStyle())

                // 通知按钮
                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.softSage.opacity(0.2))
                            .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                        Image(systemName: "bell")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(HealingColors.forestMist)

                        // 通知红点
                        Circle()
                            .fill(HealingColors.terracotta)
                            .frame(width: layout.captionFontSize - 4, height: layout.captionFontSize - 4)
                            .offset(x: 12, y: -12)
                    }
                }
                .buttonStyle(ScaleButtonStyle())
            }
        }
    }

    private func getGreeting() -> String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 0..<6: return "夜深了"
        case 6..<9: return "早安"
        case 9..<12: return "上午好"
        case 12..<14: return "午安"
        case 14..<18: return "下午好"
        case 18..<22: return "晚上好"
        default: return "夜安"
        }
    }
}

// MARK: - 今日健康卡片
struct HealingTodayCard: View {
    @Binding var selectedTab: Int
    let layout: AdaptiveLayout
    @State private var currentDate: String = ""
    @State private var weekday: String = ""

    var body: some View {
        Button(action: { selectedTab = 1 }) {
            ZStack(alignment: .topLeading) {
                // 渐变背景
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                HealingColors.deepSage,
                                HealingColors.forestMist
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )

                // 装饰圆圈 - 自适应尺寸
                Circle()
                    .fill(Color.white.opacity(0.08))
                    .frame(width: layout.todayCardHeight * 0.45, height: layout.todayCardHeight * 0.45)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)

                VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                    // 顶部：日期与状态
                    HStack {
                        VStack(alignment: .leading, spacing: 0) {
                            Text("今日健康")
                                .font(.system(size: layout.captionFontSize - 1, weight: .medium))
                                .foregroundColor(Color.white.opacity(0.8))

                            Text(currentDate + " · " + weekday)
                                .font(.system(size: layout.captionFontSize - 3, weight: .regular))
                                .foregroundColor(Color.white.opacity(0.6))
                        }

                        Spacer()

                        // 在线状态
                        HStack(spacing: 2) {
                            Circle()
                                .fill(HealingColors.softSage)
                                .frame(width: 4, height: 4)
                                .pulsing()

                            Text("在线")
                                .font(.system(size: layout.captionFontSize - 3, weight: .medium))
                                .foregroundColor(Color.white.opacity(0.9))
                        }
                        .padding(.horizontal, 5)
                        .padding(.vertical, 2)
                        .background(Color.white.opacity(0.15))
                        .clipShape(Capsule())
                    }

                    Spacer()

                    // 中部：主标题
                    VStack(alignment: .leading, spacing: 2) {
                        Text("身体不适?")
                            .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                            .foregroundColor(Color.white.opacity(0.85))

                        Text("立即咨询 AI 医生")
                            .font(.system(size: layout.bodyFontSize - 1, weight: .bold))
                            .foregroundColor(.white)
                    }

                    // 底部：按钮
                    HStack(spacing: 3) {
                        Text("开始咨询")
                            .font(.system(size: layout.captionFontSize, weight: .semibold))
                            .foregroundColor(HealingColors.forestMist)

                        Image(systemName: "arrow.right")
                            .font(.system(size: layout.captionFontSize - 3, weight: .semibold))
                            .foregroundColor(HealingColors.forestMist)
                    }
                    .padding(.horizontal, layout.cardSpacing - 2)
                    .padding(.vertical, layout.cardSpacing / 2)
                    .background(Color.white)
                    .clipShape(Capsule())
                }
                .padding(layout.cardInnerPadding - 2)
            }
            .frame(height: layout.todayCardHeight)
        }
        .buttonStyle(ScaleButtonStyle())
        .onAppear {
            updateDate()
        }
    }

    private func updateDate() {
        let date = Date()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "M月d日"
        currentDate = dateFormatter.string(from: date)

        let weekday = Calendar.current.component(.weekday, from: date)
        let weekdays = ["", "周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        self.weekday = weekdays[weekday]
    }
}

// MARK: - 快速功能 - 不对称布局
struct HealingQuickActions: View {
    @Binding var selectedTab: Int
    @Binding var showDrugList: Bool
    @Binding var showDiseaseList: Bool
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: layout.cardSpacing - 2) {
            // 标题行
            HStack {
                Text("快速服务")
                    .font(.system(size: layout.bodyFontSize, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                Button(action: {}) {
                    HStack(spacing: 4) {
                        Text("更多")
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: layout.captionFontSize - 2, weight: .semibold))
                    }
                    .foregroundColor(HealingColors.forestMist)
                }
            }

            // 不对称卡片布局 - 使用自适应间距
            HStack(alignment: .top, spacing: layout.cardSpacing - 2) {
                // 左侧大卡片 - 查疾病
                Button(action: { showDiseaseList = true }) {
                    QuickActionCard(
                        icon: "stethoscope",
                        title: "查疾病",
                        subtitle: "权威百科",
                        color: HealingColors.dustyBlue,
                        size: .large,
                        layout: layout
                    )
                }
                .buttonStyle(ScaleButtonStyle())

                // 右侧两个小卡片
                VStack(spacing: layout.cardSpacing - 2) {
                    // 查药品
                    Button(action: { showDrugList = true }) {
                        QuickActionCard(
                            icon: "pills.fill",
                            title: "查药品",
                            subtitle: "7万+说明",
                            color: HealingColors.mutedCoral,
                            size: .small,
                            layout: layout
                        )
                    }
                    .buttonStyle(ScaleButtonStyle())

                    // 我的医嘱
                    Button(action: { selectedTab = 2 }) {
                        QuickActionCard(
                            icon: "text.badge.checkmark",
                            title: "我的医嘱",
                            subtitle: "按时服药",
                            color: HealingColors.lavenderHaze,
                            size: .small,
                            layout: layout
                        )
                    }
                    .buttonStyle(ScaleButtonStyle())
                }
            }
        }
    }
}

// MARK: - 快速功能卡片
enum CardSize {
    case large
    case small
}

struct QuickActionCard: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    let size: CardSize
    let layout: AdaptiveLayout

    var body: some View {
        GeometryReader { cardGeometry in
            ZStack(alignment: size == .large ? .bottomLeading : .leading) {
                // 卡片背景
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(HealingColors.cardBackground)
                    .shadow(color: Color.black.opacity(0.04), radius: 12, x: 0, y: 4)

                // 文字 - 左侧，使用自适应字体和间距
                HStack(alignment: .center, spacing: 8) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(title)
                            .font(.system(size: size == .large ? layout.bodyFontSize - 3 : layout.bodyFontSize - 4, weight: .semibold))
                            .foregroundColor(HealingColors.textPrimary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)

                        Text(subtitle)
                            .font(.system(size: layout.captionFontSize - 1, weight: .regular))
                            .foregroundColor(HealingColors.textTertiary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)

                        if size == .large {
                            HStack(spacing: 2) {
                                Image(systemName: "chevron.right")
                                    .font(.system(size: layout.captionFontSize - 4, weight: .semibold))
                                    .foregroundColor(color.opacity(0.7))
                            }
                        }
                    }

                    Spacer()

                    // 图标 - 右侧，自适应尺寸
                    Circle()
                        .fill(color.opacity(0.12))
                        .frame(
                            width: size == .large ? layout.iconLargeSize : layout.iconSmallSize,
                            height: size == .large ? layout.iconLargeSize : layout.iconSmallSize
                        )
                        .overlay {
                            Image(systemName: icon)
                                .font(.system(size: size == .large ? 18 : 14, weight: .medium))
                                .foregroundColor(color)
                        }
                }
                .padding(layout.cardInnerPadding - 4)
            }
        }
        .frame(height: size == .large ? layout.quickCardLargeHeight : layout.quickCardSmallHeight)
    }
}

// MARK: - 科室导航
struct HealingDepartmentSection: View {
    let layout: AdaptiveLayout
    @State private var departments: [DepartmentModel] = []
    @State private var isLoading = false
    @State private var selectedDepartment: DepartmentModel?

    let columns = [
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible())
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing + 2) {
            // 标题
            HStack {
                Text("科室导航")
                    .font(.system(size: layout.bodyFontSize, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                Button(action: {}) {
                    HStack(spacing: 4) {
                        Text("全部")
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: layout.captionFontSize - 2, weight: .semibold))
                    }
                    .foregroundColor(HealingColors.forestMist)
                }
            }

            // 科室网格
            if isLoading {
                ProgressView()
                    .tint(HealingColors.forestMist)
                    .frame(height: 120)
            } else if departments.isEmpty {
                // 空状态占位
                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach(placeholderDepartments.prefix(8), id: \.self) { name in
                        DepartmentGridItem(name: name, icon: placeholderIcon(for: name), layout: layout)
                    }
                }
            } else {
                LazyVGrid(columns: columns, spacing: 16) {
                    ForEach(displayDepartments) { dept in
                        DepartmentGridItem(
                            name: dept.name,
                            icon: SFSymbolResolver.resolve(dept.icon),
                            layout: layout
                        )
                        .contentShape(Rectangle())
                        .onTapGesture {
                            selectedDepartment = dept
                        }
                    }

                    DepartmentGridItem(name: "更多", icon: "ellipsis", layout: layout)
                }
            }
        }
        .navigationDestinationCompat(item: $selectedDepartment) { dept in
            DepartmentDetailView(departmentName: dept.name, departmentId: dept.id)
        }
        .onAppear {
            loadDepartments()
        }
    }

    private var displayDepartments: [DepartmentModel] {
        Array(departments.prefix(7))
    }

    private var placeholderDepartments: [String] {
        ["内科", "外科", "儿科", "妇科", "皮肤科", "骨科", "眼科", "耳鼻喉"]
    }

    private func placeholderIcon(for name: String) -> String {
        switch name {
        case "内科": return "lungs.fill"
        case "外科": return "cross.case.fill"
        case "儿科": return "figure.child"
        case "妇科": return "figure.woman"
        case "皮肤科": return "face.smiling"
        case "骨科": return "bone"
        case "眼科": return "eye.fill"
        case "耳鼻喉": return "ear.fill"
        default: return "staroflife.fill"
        }
    }

    private func loadDepartments() {
        guard departments.isEmpty else { return }
        isLoading = true

        Task {
            do {
                let depts = try await APIService.shared.getDepartments()
                await MainActor.run {
                    departments = depts
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

// MARK: - 科室网格项
struct DepartmentGridItem: View {
    let name: String
    let icon: String
    let layout: AdaptiveLayout

    var body: some View {
        VStack(spacing: 10) {
            // 图标背景
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(HealingColors.softSage.opacity(0.2))
                    .frame(width: layout.iconLargeSize + 4, height: layout.iconLargeSize + 4)

                Image(systemName: icon)
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(HealingColors.forestMist)
            }

            Text(name)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(HealingColors.textPrimary)
        }
    }
}

// MARK: - 健康贴士
struct HealingHealthTips: View {
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack {
                Text("健康小贴士")
                    .font(.system(size: layout.bodyFontSize, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                Button(action: {}) {
                    HStack(spacing: 4) {
                        Text("更多")
                            .font(.system(size: layout.captionFontSize, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: layout.captionFontSize - 2, weight: .semibold))
                    }
                    .foregroundColor(HealingColors.forestMist)
                }
            }

            // 贴士卡片
            VStack(spacing: layout.cardSpacing - 2) {
                HealthTipCard(
                    icon: "drop.degreesign.fill",
                    title: "今日提醒",
                    tip: "记得多喝水，建议每天 8 杯水保持身体水分",
                    color: HealingColors.dustyBlue,
                    layout: layout
                )

                HealthTipCard(
                    icon: "bed.double.fill",
                    title: "睡眠建议",
                    tip: "保持规律作息，建议每天 7-8 小时睡眠",
                    color: HealingColors.lavenderHaze,
                    layout: layout
                )
            }
        }
    }
}

// MARK: - 健康贴士卡片
struct HealthTipCard: View {
    let icon: String
    let title: String
    let tip: String
    let color: Color
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing - 2) {
            // 图标 - 自适应尺寸
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(color.opacity(0.15))
                    .frame(width: 44 * layout.iconScale, height: 44 * layout.iconScale)

                Image(systemName: icon)
                    .font(.system(size: 17 * layout.iconScale, weight: .medium))
                    .foregroundColor(color)
            }

            // 文字 - 自适应字体
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: layout.bodyFontSize - 4, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Text(tip)
                    .font(.system(size: layout.captionFontSize, weight: .regular))
                    .foregroundColor(HealingColors.textSecondary)
                    .lineLimit(2)
            }

            Spacer()
        }
        .padding(layout.cardInnerPadding)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(HealingColors.cardBackground)
                .shadow(color: Color.black.opacity(0.03), radius: 8, x: 0, y: 2)
        )
    }
}

// MARK: - 按钮样式
struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

// MARK: - 占位视图
struct PlaceholderView: View {
    let title: String
    let icon: String
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            HealingColors.background
                .ignoresSafeArea()

            VStack(spacing: 24) {
                ZStack {
                    Circle()
                        .fill(HealingColors.softSage.opacity(0.3))
                        .frame(width: layout.iconLargeSize * 1.7, height: layout.iconLargeSize * 1.7)

                    Image(systemName: SFSymbolResolver.resolve(icon))
                        .font(.system(size: 32, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }

                Text(title)
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("功能开发中，敬请期待")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(HealingColors.textTertiary)
            }
        }
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Preview
#Preview {
    HomeView()
}
