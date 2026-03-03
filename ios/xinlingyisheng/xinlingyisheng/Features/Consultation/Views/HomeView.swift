import SwiftUI

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
    @State private var selectedTab = 3
    // 每个 tab 的导航路径，用于在切换 tab 时重置导航栈
    @State private var tab0Path: [String] = []
    @State private var tab1Path: [String] = []
    @State private var tab2Path: [String] = []
    @State private var tab3Path: [String] = []
    @State private var tab4Path: [String] = []

    // 上次选中的 tab，用于检测切换并重置导航路径
    @State private var previousTab: Int? = nil

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

            CompatibleNavigationStack(path: $tab1Path) {
                AIConsultationEntryView()
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
                MedicalFoldersView()
            }
            .tabItem {
                Image(systemName: selectedTab == 3 ? "folder.fill" : "folder")
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
        ZStack(alignment: .topLeading) {
            // 背景色 - 确保覆盖整个屏幕
            HealingColors.background
                .ignoresSafeArea()

            GeometryReader { geometry in
                let layout = AdaptiveLayout(screenWidth: geometry.size.width)

                ZStack(alignment: .topLeading) {
                    // 右上角装饰光晕 - 使用统一的相对偏移
                    Circle()
                        .fill(HealingColors.softSage.opacity(0.12))
                        .frame(width: layout.decorativeCircleSize, height: layout.decorativeCircleSize)
                        .offset(x: layout.topRightOffsetX, y: layout.topRightOffsetY)

                    // 左下角装饰光晕 - 使用统一的相对偏移
                    Circle()
                        .fill(HealingColors.mutedCoral.opacity(0.08))
                        .frame(width: layout.decorativeCircleSize * 0.9, height: layout.decorativeCircleSize * 0.9)
                        .offset(x: layout.bottomLeftOffsetX, y: layout.bottomLeftOffsetY)

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

                                // 健康资讯
                                HealingHealthTips(layout: layout)
                                    .fluidFadeIn(delay: 0.3)
                            }
                            .padding(.horizontal, layout.horizontalPadding)
                            .padding(.bottom, ScaleFactor.padding(140))
                        }
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
                            .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                            .foregroundColor(.white)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("灵犀健康")
                            .font(.system(size: UnifiedFont.title2, weight: .bold))
                            .foregroundColor(HealingColors.textPrimary)

                        Text("AI 健康管家 · 随时守护")
                            .font(.system(size: layout.captionFontSize, weight: .regular))
                            .foregroundColor(HealingColors.textTertiary)
                    }
                }

                // 问候语
                HStack(spacing: 6) {
                    Text(getGreeting())
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    Text("，" + userName)
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }
                .padding(.top, ScaleFactor.padding(4))
            }

            Spacer()

            // 右侧 - 操作按钮
            HStack(spacing: ScaleFactor.spacing(14)) {
                // 搜索按钮
                Button(action: {}) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.softSage.opacity(0.2))
                            .frame(width: layout.iconSmallSize + 2, height: layout.iconSmallSize + 2)

                        Image(systemName: "magnifyingglass")
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
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
                            .font(.system(size: AdaptiveFont.body, weight: .medium))
                            .foregroundColor(HealingColors.forestMist)

                        // 通知红点
                        Circle()
                            .fill(HealingColors.terracotta)
                            .frame(width: AdaptiveFont.custom(8), height: AdaptiveFont.custom(8))
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
    @State private var isPressed = false

    var body: some View {
        Button(action: { selectedTab = 1 }) {
            ZStack(alignment: .topLeading) {
                // 增强的渐变背景 - 三色渐变增加深度
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                HealingColors.deepSage,
                                HealingColors.forestMist,
                                HealingColors.deepSage.opacity(0.9)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )

                // 多层装饰圆圈 - 增加视觉层次
                Circle()
                    .fill(Color.white.opacity(0.12))
                    .frame(width: layout.todayCardHeight * 0.5, height: layout.todayCardHeight * 0.5)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                    .offset(x: -20, y: -10)

                Circle()
                    .fill(Color.white.opacity(0.06))
                    .frame(width: layout.todayCardHeight * 0.35, height: layout.todayCardHeight * 0.35)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
                    .offset(x: 15, y: 10)

                VStack(alignment: .leading, spacing: layout.cardSpacing / 2) {
                    // 顶部：日期与状态
                    HStack {
                        VStack(alignment: .leading, spacing: 0) {
                            Text("今日健康")
                                .font(.system(size: UnifiedFont.caption1, weight: .medium))
                                .foregroundColor(Color.white.opacity(0.8))

                            Text(currentDate + " · " + weekday)
                                .font(.system(size: AdaptiveFont.custom(9)))
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
                                .font(.system(size: AdaptiveFont.custom(9), weight: .medium))
                                .foregroundColor(Color.white.opacity(0.9))
                        }
                        .padding(.horizontal, ScaleFactor.padding(5))
                        .padding(.vertical, ScaleFactor.padding(2))
                        .background(Color.white.opacity(0.15))
                        .clipShape(Capsule())
                    }

                    Spacer()

                    // 中部：主标题
                    VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                        Text("身体不适?")
                            .font(.system(size: UnifiedFont.footnote, weight: .medium))
                            .foregroundColor(Color.white.opacity(0.85))

                        Text("立即咨询 AI 医生")
                            .font(.system(size: UnifiedFont.subheadline, weight: .bold))
                            .foregroundColor(.white)
                    }

                    // 底部：按钮
                    HStack(spacing: ScaleFactor.spacing(3)) {
                        Text("开始咨询")
                            .font(.system(size: UnifiedFont.caption1, weight: .semibold))
                            .foregroundColor(HealingColors.forestMist)

                        Image(systemName: "arrow.right")
                            .font(.system(size: AdaptiveFont.custom(9), weight: .semibold))
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
            .scaleEffect(isPressed ? 0.97 : 1.0)
            .shadow(
                color: HealingColors.forestMist.opacity(0.25),
                radius: isPressed ? 8 : 16,
                x: 0,
                y: isPressed ? 4 : 8
            )
        }
        .buttonStyle(ScaleButtonStyle())
        .onLongPressGesture(minimumDuration: 0, maximumDistance: .infinity, pressing: { pressing in
            withAnimation(.easeInOut(duration: 0.15)) {
                isPressed = pressing
            }
        }, perform: {})
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
                            .font(.system(size: UnifiedFont.caption1, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: UnifiedFont.caption1, weight: .semibold))
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
    @State private var isPressed = false

    var body: some View {
        GeometryReader { cardGeometry in
            ZStack(alignment: size == .large ? .bottomLeading : .leading) {
                // 卡片背景 - 增强玻璃拟态效果
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(HealingColors.cardBackground)
                    .background(
                        RoundedRectangle(cornerRadius: 22, style: .continuous)
                            .fill(color.opacity(0.05))
                            .blur(radius: 0)
                    )
                    .shadow(
                        color: Color.black.opacity(isPressed ? 0.06 : 0.08),
                        radius: isPressed ? 6 : 12,
                        x: 0,
                        y: isPressed ? 2 : 4
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 22, style: .continuous)
                            .stroke(
                                color.opacity(isPressed ? 0.15 : 0.08),
                                lineWidth: 1
                            )
                    )

                // 文字 - 左侧，使用自适应字体和间距
                HStack(alignment: .center, spacing: 8) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(title)
                            .font(.system(size: size == .large ? AdaptiveFont.custom(11) : AdaptiveFont.custom(10), weight: .semibold))
                            .foregroundColor(HealingColors.textPrimary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)

                        Text(subtitle)
                            .font(.system(size: UnifiedFont.caption1, weight: .regular))
                            .foregroundColor(HealingColors.textTertiary)
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)

                        if size == .large {
                            HStack(spacing: 2) {
                                Image(systemName: "chevron.right")
                                    .font(.system(size: AdaptiveFont.custom(8), weight: .semibold))
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
                                .font(.system(size: size == .large ? UnifiedFont.title3 : UnifiedFont.body, weight: .medium))
                                .foregroundColor(color)
                        }
                }
                .padding(layout.cardInnerPadding - 4)
            }
            .scaleEffect(isPressed ? 0.96 : 1.0)
        }
        .frame(height: size == .large ? layout.quickCardLargeHeight : layout.quickCardSmallHeight)
        .onLongPressGesture(minimumDuration: 0, maximumDistance: .infinity, pressing: { pressing in
            withAnimation(.easeInOut(duration: 0.12)) {
                isPressed = pressing
            }
        }, perform: {})
    }
}

// MARK: - AI 问诊入口视图（简化版，直接进入全科问诊）
struct AIConsultationEntryView: View {
    @State private var showConsultation = false

    var body: some View {
        ZStack {
            HealingColors.background
                .ignoresSafeArea()

            VStack(spacing: 24) {
                Spacer()

                // AI 医生图标
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [HealingColors.softSage.opacity(0.3), HealingColors.deepSage.opacity(0.2)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 120, height: 120)

                    Image(systemName: "heart.text.square.fill")
                        .font(.system(size: 50))
                        .foregroundColor(HealingColors.forestMist)
                }
                .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 20)

                VStack(spacing: 12) {
                    Text("AI 全科医生")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(HealingColors.textPrimary)

                    Text("24小时在线，随时为您服务")
                        .font(.system(size: 16))
                        .foregroundColor(HealingColors.textSecondary)
                }

                Spacer()

                // 开始问诊按钮
                Button(action: { showConsultation = true }) {
                    HStack(spacing: 10) {
                        Image(systemName: "message.fill")
                        Text("开始问诊")
                            .font(.system(size: 18, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .background(
                        LinearGradient(
                            colors: [HealingColors.deepSage, HealingColors.forestMist],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: HealingColors.forestMist.opacity(0.4), radius: 15, y: 5)
                }
                .padding(.horizontal, 32)
                .padding(.bottom, 40)
            }
        }
        .navigationBarHidden(true)
        .navigationDestinationCompat(isPresented: $showConsultation) {
            // 全科智能体问诊，不需要 doctorId
            ModernConsultationView(
                doctorId: nil,
                doctorName: "AI全科医生",
                department: "全科",
                doctorTitle: "智能助理",
                doctorBio: "我是您的AI全科健康助手，可以帮您解答各类健康问题"
            )
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
                            .font(.system(size: UnifiedFont.caption1, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: UnifiedFont.caption1, weight: .semibold))
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
    @State private var isPressed = false

    var body: some View {
        HStack(spacing: layout.cardSpacing - 2) {
            // 图标 - 自适应尺寸，增强效果
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                color.opacity(isPressed ? 0.25 : 0.18),
                                color.opacity(isPressed ? 0.12 : 0.08)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 44 * layout.iconScale, height: 44 * layout.iconScale)
                    .shadow(
                        color: color.opacity(isPressed ? 0.25 : 0.15),
                        radius: isPressed ? 6 : 3,
                        x: 0,
                        y: 1
                    )

                Image(systemName: icon)
                    .font(.system(size: AdaptiveFont.body, weight: .medium))
                    .foregroundColor(color)
            }
            .scaleEffect(isPressed ? 0.92 : 1.0)

            // 文字 - 自适应字体
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: AdaptiveFont.custom(10), weight: .semibold))
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
                .shadow(
                    color: Color.black.opacity(isPressed ? 0.06 : 0.05),
                    radius: isPressed ? 6 : 10,
                    x: 0,
                    y: isPressed ? 2 : 3
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(color.opacity(isPressed ? 0.12 : 0.06), lineWidth: 1)
                )
        )
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .onLongPressGesture(minimumDuration: 0, maximumDistance: .infinity, pressing: { pressing in
            withAnimation(.easeInOut(duration: 0.12)) {
                isPressed = pressing
            }
        }, perform: {})
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
            // 背景色 - 确保覆盖整个屏幕
            HealingColors.background
                .ignoresSafeArea(.all)

            VStack(spacing: 24) {
                ZStack {
                    Circle()
                        .fill(HealingColors.softSage.opacity(0.3))
                        .frame(width: layout.iconLargeSize * 1.7, height: layout.iconLargeSize * 1.7)

                    Image(systemName: SFSymbolResolver.resolve(icon))
                        .font(.system(size: UnifiedFont.title2, weight: .medium))
                        .foregroundColor(HealingColors.forestMist)
                }

                Text(title)
                    .font(.system(size: AdaptiveFont.body, weight: .bold))
                    .foregroundColor(HealingColors.textPrimary)

                Text("功能开发中，敬请期待")
                    .font(.system(size: UnifiedFont.footnote, weight: .regular))
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
