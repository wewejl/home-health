import SwiftUI

// MARK: - 全局布局常量
struct LayoutConstants {
    // 最大内容宽度 - 根据设备类型自适应
    static var maxContentWidth: CGFloat {
        if DeviceType.isPad {
            return 540
        }
        if DeviceType.isVeryCompactWidth {
            return 280  // iPhone SE
        }
        if DeviceType.isCompactWidth {
            return 330  // iPhone mini
        }
        if DeviceType.isStandardWidth {
            return 360  // iPhone 14等标准尺寸
        }
        return 400  // Pro Max等大屏设备
    }
    static let phoneContentWidth: CGFloat = 360
    
    // 水平边距 - 遵循8pt网格系统
    static let horizontalPadding: CGFloat = 16      // 2 × 8pt
    static let horizontalPaddingLarge: CGFloat = 24 // 3 × 8pt
    
    // 卡片内边距 - 遵循8pt网格系统
    static let cardPadding: CGFloat = 16            // 2 × 8pt
    static let cardPaddingLarge: CGFloat = 24       // 3 × 8pt
    
    // 间距 - 遵循8pt网格系统
    static let sectionSpacing: CGFloat = 24         // 3 × 8pt
    static let itemSpacing: CGFloat = 16            // 2 × 8pt
    static let compactSpacing: CGFloat = 8          // 1 × 8pt
    
    // 圆角 - 遵循8pt网格系统
    static let cornerRadius: CGFloat = 16           // 2 × 8pt
    static let cornerRadiusSmall: CGFloat = 8       // 1 × 8pt
    static let cornerRadiusLarge: CGFloat = 24      // 3 × 8pt
    
    // 按钮高度 - 遵循8pt网格系统
    static let buttonHeight: CGFloat = 48           // 6 × 8pt (Apple推荐最小触摸目标44pt)
    static let buttonHeightSmall: CGFloat = 40      // 5 × 8pt
    
    // 输入框高度 - 遵循8pt网格系统
    static let inputHeight: CGFloat = 48            // 6 × 8pt
}

// MARK: - 响应式布局修饰符
struct ResponsiveLayout: ViewModifier {
    var maxWidth: CGFloat = LayoutConstants.maxContentWidth
    var horizontalPadding: CGFloat = LayoutConstants.horizontalPadding
    
    func body(content: Content) -> some View {
        content
            .frame(maxWidth: maxWidth)
            .padding(.horizontal, horizontalPadding)
            .frame(maxWidth: .infinity)
    }
}

extension View {
    func responsiveLayout(
        maxWidth: CGFloat = LayoutConstants.maxContentWidth,
        horizontalPadding: CGFloat = LayoutConstants.horizontalPadding
    ) -> some View {
        modifier(ResponsiveLayout(maxWidth: maxWidth, horizontalPadding: horizontalPadding))
    }
}

// MARK: - 安全区域适配
struct SafeAreaLayout: ViewModifier {
    var edges: Edge.Set = .all
    
    func body(content: Content) -> some View {
        GeometryReader { geometry in
            content
                .padding(.top, edges.contains(.top) ? geometry.safeAreaInsets.top : 0)
                .padding(.bottom, edges.contains(.bottom) ? geometry.safeAreaInsets.bottom : 0)
        }
    }
}

// MARK: - 设备类型检测
struct DeviceType {
    static var isPhone: Bool {
        UIDevice.current.userInterfaceIdiom == .phone
    }
    
    static var isPad: Bool {
        UIDevice.current.userInterfaceIdiom == .pad
    }
    
    // iPhone SE (1st/2nd/3rd gen): 320pt
    static var isVeryCompactWidth: Bool {
        UIScreen.main.bounds.width <= 320
    }
    
    // iPhone 12 mini, 13 mini: 360pt
    static var isCompactWidth: Bool {
        UIScreen.main.bounds.width > 320 && UIScreen.main.bounds.width < 375
    }
    
    // iPhone 12/13/14/15 standard: 390pt
    // iPhone 11/XR: 414pt
    static var isStandardWidth: Bool {
        UIScreen.main.bounds.width >= 375 && UIScreen.main.bounds.width < 430
    }
    
    // iPhone 12/13/14/15 Pro Max: 430pt
    static var isRegularWidth: Bool {
        UIScreen.main.bounds.width >= 430
    }
    
    // 屏幕宽度
    static var screenWidth: CGFloat {
        UIScreen.main.bounds.width
    }
    
    // 屏幕高度
    static var screenHeight: CGFloat {
        UIScreen.main.bounds.height
    }
}

// MARK: - 响应式缩放系统（统一字体和布局系统）
/// 使用固定的字体和布局大小，确保所有页面在所有设备上保持完全一致的视觉效果
struct ScaleFactor {
    // 基准宽度：iPhone 14/15 (390pt) - 最常见的设备尺寸
    private static let baseWidth: CGFloat = 390.0

    /// 当前设备相对于基准设备的缩放比例（仅用于参考）
    static var width: CGFloat {
        DeviceType.screenWidth / baseWidth
    }

    /// 字体大小 - 不缩放，所有设备保持一致
    /// - Parameter size: 字体大小
    /// - Returns: 原始字体大小（不进行任何缩放）
    static func font(_ size: CGFloat) -> CGFloat {
        size  // 字体不缩放，保持所有设备一致
    }

    /// 尺寸（宽度、高度、圆角等）- 不缩放，保持所有设备一致
    /// - Parameter size: 基准尺寸
    /// - Returns: 原始尺寸（不进行任何缩放）
    static func size(_ size: CGFloat) -> CGFloat {
        size  // 不缩放，保持所有设备一致
    }

    /// 间距 - 不缩放，保持所有设备一致
    /// - Parameter spacing: 基准间距
    /// - Returns: 原始间距（不进行任何缩放）
    static func spacing(_ spacing: CGFloat) -> CGFloat {
        spacing  // 不缩放，保持所有设备一致
    }

    /// 内边距 - 不缩放，保持所有设备一致
    /// - Parameter padding: 基准内边距
    /// - Returns: 原始内边距（不进行任何缩放）
    static func padding(_ padding: CGFloat) -> CGFloat {
        padding  // 不缩放，保持所有设备一致
    }
}

// MARK: - 统一字体访问点
/// 全局统一的字体系统，所有页面应使用此系统
/// 基于 Apple Human Interface Guidelines 标准，确保跨页面的视觉一致性
/// 字体大小在所有设备上保持相同，不进行缩放
struct UnifiedFont {
    // MARK: - Apple HIG 标准字体大小（所有设备一致）
    /// 遵循 Apple Human Interface Guidelines 的字体层级系统
    /// 确保在不同设备上的视觉体验一致且符合 iOS 设计规范

    /// 大标题（34pt）- 页面主标题，每个页面只用一次
    static var largeTitle: CGFloat { ScaleFactor.font(34) }

    /// 标题1（28pt）- 大标题
    static var title1: CGFloat { ScaleFactor.font(28) }

    /// 标题2（22pt）- 区块标题
    static var title2: CGFloat { ScaleFactor.font(22) }

    /// 标题3（20pt）- 卡片/小标题
    static var title3: CGFloat { ScaleFactor.font(20) }

    /// 强调文字（17pt）- 强调的文字内容
    static var headline: CGFloat { ScaleFactor.font(17) }

    /// 正文（17pt）- 标准正文，主要文字内容
    static var body: CGFloat { ScaleFactor.font(17) }

    /// 次要内容（16pt）- 次要文字
    static var callout: CGFloat { ScaleFactor.font(16) }

    /// 副标题（15pt）- 副标题
    static var subheadline: CGFloat { ScaleFactor.font(15) }

    /// 说明文字（13pt）- 说明/提示文字
    static var footnote: CGFloat { ScaleFactor.font(13) }

    /// 脚注1（12pt）- 标签、徽章
    static var caption1: CGFloat { ScaleFactor.font(12) }

    /// 脚注2（11pt）- 小脚注
    static var caption2: CGFloat { ScaleFactor.font(11) }

    /// 兼容旧代码：caption 映射到 caption1
    @available(*, deprecated, message: "使用 caption1 替代")
    static var caption: CGFloat { caption1 }

    /// 自定义字体大小（不缩放）
    static func custom(_ size: CGFloat) -> CGFloat {
        ScaleFactor.font(size)  // 返回原始大小，不进行缩放
    }

    // MARK: - Font 便捷方法

    /// 创建系统字体
    static func system(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        Font.system(size: custom(size), weight: weight)
    }

    /// 创建粗体标题
    static func boldTitle(_ size: CGFloat? = nil) -> Font {
        Font.system(size: custom(size ?? 28), weight: .bold)
    }

    /// 创建半粗体正文
    static func semiboldBody(_ size: CGFloat? = nil) -> Font {
        Font.system(size: custom(size ?? 17), weight: .semibold)
    }

    /// 创建常规体
    static func regular(_ size: CGFloat? = nil) -> Font {
        Font.system(size: custom(size ?? 17), weight: .regular)
    }

    /// 创建中等体说明
    static func mediumFootnote(_ size: CGFloat? = nil) -> Font {
        Font.system(size: custom(size ?? 13), weight: .medium)
    }
}

// MARK: - View 便捷扩展
extension View {
    /// 应用统一的字体
    func unifiedFont(size: CGFloat, weight: Font.Weight = .regular) -> some View {
        self.font(Font.system(size: UnifiedFont.custom(size), weight: weight))
    }

    /// 统一大标题
    func largeTitle(weight: Font.Weight = .bold) -> some View {
        self.font(Font.system(size: UnifiedFont.largeTitle, weight: weight))
    }

    /// 统一标题
    func title(weight: Font.Weight = .semibold) -> some View {
        self.font(Font.system(size: UnifiedFont.title2, weight: weight))
    }

    /// 统一正文
    func body(weight: Font.Weight = .regular) -> some View {
        self.font(Font.system(size: UnifiedFont.body, weight: weight))
    }

    /// 统一脚注1（12pt）
    func caption1(weight: Font.Weight = .regular) -> some View {
        self.font(Font.system(size: UnifiedFont.caption11, weight: weight))
    }

    /// 统一脚注（已弃用，使用 caption1 替代）
    @available(*, deprecated, message: "使用 caption1(weight:) 替代")
    func caption(weight: Font.Weight = .regular) -> some View {
        self.font(Font.system(size: UnifiedFont.caption11, weight: weight))
    }
}

// MARK: - 自适应间距（基于比例缩放）
struct AdaptiveSpacing {
    // Section间距：大区块之间的间距（基准 24pt）
    static var section: CGFloat {
        ScaleFactor.spacing(24)
    }
    
    // Item间距：列表项或小元素之间的间距（基准 16pt）
    static var item: CGFloat {
        ScaleFactor.spacing(16)
    }
    
    // Card内边距：卡片内部的padding（基准 20pt）
    static var card: CGFloat {
        ScaleFactor.padding(20)
    }
    
    // 紧凑间距：图标和文字之间等紧密元素（基准 8pt）
    static var compact: CGFloat {
        ScaleFactor.spacing(8)
    }
}

// MARK: - 自适应字体（固定大小，与 UnifiedFont 一致）
/// 使用统一的字体系统，确保跨页面和跨设备的一致性
/// 基于 Apple HIG 标准，字体大小在所有设备上保持相同
struct AdaptiveFont {
    /// 大标题（34pt）
    static var largeTitle: CGFloat { ScaleFactor.font(34) }

    /// 标题1（28pt）
    static var title1: CGFloat { ScaleFactor.font(28) }

    /// 标题2（22pt）
    static var title2: CGFloat { ScaleFactor.font(22) }

    /// 标题3（20pt）
    static var title3: CGFloat { ScaleFactor.font(20) }

    /// 强调文字（17pt）
    static var headline: CGFloat { ScaleFactor.font(17) }

    /// 正文（17pt）
    static var body: CGFloat { ScaleFactor.font(17) }

    /// 次要内容（16pt）
    static var callout: CGFloat { ScaleFactor.font(16) }

    /// 副标题（15pt）
    static var subheadline: CGFloat { ScaleFactor.font(15) }

    /// 脚注（13pt）
    static var footnote: CGFloat { ScaleFactor.font(13) }

    /// 说明文字1（12pt）
    static var caption1: CGFloat { ScaleFactor.font(12) }

    /// 说明文字2（11pt）
    static var caption2: CGFloat { ScaleFactor.font(11) }

    /// 兼容旧代码：caption 映射到 caption1
    @available(*, deprecated, message: "使用 caption1 替代")
    static var caption: CGFloat { caption1 }

    /// 自定义字体大小（不缩放）
    static func custom(_ size: CGFloat) -> CGFloat {
        ScaleFactor.font(size)
    }
}

// MARK: - 自适应尺寸（固定大小，与 ScaleFactor 一致）
/// 所有设备上保持一致，不进行缩放
struct AdaptiveSize {
    /// 图标尺寸 - 小（16pt）
    static var iconSmall: CGFloat { ScaleFactor.size(16) }

    /// 图标尺寸 - 中（24pt）
    static var iconMedium: CGFloat { ScaleFactor.size(24) }

    /// 图标尺寸 - 大（32pt）
    static var iconLarge: CGFloat { ScaleFactor.size(32) }

    /// 按钮高度（48pt）
    static var buttonHeight: CGFloat { ScaleFactor.size(48) }

    /// 小按钮高度（40pt）
    static var buttonHeightSmall: CGFloat { ScaleFactor.size(40) }

    /// 圆角 - 小（8pt）
    static var cornerRadiusSmall: CGFloat { ScaleFactor.size(8) }

    /// 圆角 - 中（16pt）
    static var cornerRadius: CGFloat { ScaleFactor.size(16) }

    /// 圆角 - 大（24pt）
    static var cornerRadiusLarge: CGFloat { ScaleFactor.size(24) }

    /// 自定义尺寸
    static func custom(_ size: CGFloat) -> CGFloat {
        ScaleFactor.size(size)
    }
}

// MARK: - Color 扩展 - 动态颜色支持深色模式
extension Color {
    /// 根据系统外观动态选择颜色
    static func dynamicColor(light: Color, dark: Color) -> Color {
        return Color(UIColor { traitCollection in
            return traitCollection.userInterfaceStyle == .dark ?
                UIColor(dark) : UIColor(light)
        })
    }
}
