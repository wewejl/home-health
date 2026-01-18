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

// MARK: - 响应式缩放系统（Apple 推荐方法）
/// 基于屏幕宽度比例的缩放因子，以 iPhone 14 Pro Max (430pt) 为基准
/// 这是 iOS 官方推荐的响应式设计方法
struct ScaleFactor {
    // 基准宽度：iPhone 14 Pro Max
    private static let baseWidth: CGFloat = 430.0
    
    /// 当前设备相对于基准设备的缩放比例
    static var width: CGFloat {
        DeviceType.screenWidth / baseWidth
    }
    
    /// 缩放字体大小
    /// - Parameter size: 基准字体大小（基于 430pt 宽度设计）
    /// - Returns: 适配当前设备的字体大小
    static func font(_ size: CGFloat) -> CGFloat {
        size * width
    }
    
    /// 缩放尺寸（宽度、高度、圆角等）
    /// - Parameter size: 基准尺寸
    /// - Returns: 适配当前设备的尺寸
    static func size(_ size: CGFloat) -> CGFloat {
        size * width
    }
    
    /// 缩放间距
    /// - Parameter spacing: 基准间距
    /// - Returns: 适配当前设备的间距
    static func spacing(_ spacing: CGFloat) -> CGFloat {
        size(spacing)
    }
    
    /// 缩放内边距
    /// - Parameter padding: 基准内边距
    /// - Returns: 适配当前设备的内边距
    static func padding(_ padding: CGFloat) -> CGFloat {
        size(padding)
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

// MARK: - 自适应字体（基于比例缩放）
struct AdaptiveFont {
    /// 大标题（基准 28pt）
    static var largeTitle: CGFloat { ScaleFactor.font(28) }
    
    /// 标题1（基准 24pt）
    static var title1: CGFloat { ScaleFactor.font(24) }
    
    /// 标题2（基准 20pt）
    static var title2: CGFloat { ScaleFactor.font(20) }
    
    /// 标题3（基准 18pt）
    static var title3: CGFloat { ScaleFactor.font(18) }
    
    /// 正文（基准 16pt）
    static var body: CGFloat { ScaleFactor.font(16) }
    
    /// 副标题（基准 14pt）
    static var subheadline: CGFloat { ScaleFactor.font(14) }
    
    /// 脚注（基准 12pt）
    static var footnote: CGFloat { ScaleFactor.font(12) }
    
    /// 说明文字（基准 11pt）
    static var caption: CGFloat { ScaleFactor.font(11) }
    
    /// 自定义字体大小
    static func custom(_ size: CGFloat) -> CGFloat {
        ScaleFactor.font(size)
    }
}

// MARK: - 自适应尺寸（基于比例缩放）
struct AdaptiveSize {
    /// 图标尺寸 - 小（基准 16pt）
    static var iconSmall: CGFloat { ScaleFactor.size(16) }
    
    /// 图标尺寸 - 中（基准 24pt）
    static var iconMedium: CGFloat { ScaleFactor.size(24) }
    
    /// 图标尺寸 - 大（基准 32pt）
    static var iconLarge: CGFloat { ScaleFactor.size(32) }
    
    /// 按钮高度（基准 48pt）
    static var buttonHeight: CGFloat { ScaleFactor.size(48) }
    
    /// 小按钮高度（基准 40pt）
    static var buttonHeightSmall: CGFloat { ScaleFactor.size(40) }
    
    /// 圆角 - 小（基准 8pt）
    static var cornerRadiusSmall: CGFloat { ScaleFactor.size(8) }
    
    /// 圆角 - 中（基准 16pt）
    static var cornerRadius: CGFloat { ScaleFactor.size(16) }
    
    /// 圆角 - 大（基准 24pt）
    static var cornerRadiusLarge: CGFloat { ScaleFactor.size(24) }
    
    /// 自定义尺寸
    static func custom(_ size: CGFloat) -> CGFloat {
        ScaleFactor.size(size)
    }
}
