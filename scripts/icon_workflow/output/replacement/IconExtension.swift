import SwiftUI

// MARK: - 自定义图标扩展
extension Image {
    /// 使用自定义图标替换 SF Symbol
    /// - Parameter name: 图标名称（不含扩展名）
    /// - Parameter bundle: Bundle，默认使用 main
    static func icon(_ name: String, bundle: Bundle = .main) -> Image {
        Image(bundle: bundle, imageResource: .init(name: name))
    }
}

// MARK: - 图标名称枚举
enum IconName: String {
    // 导航方向
    case chevronRight
    case chevronLeft
    case chevronDown
    case arrowUp
    case arrowClockwise
    case arrowTriangleMerge

    // 操作动作
    case plusCircleFill
    case pencil
    case xmarkCircleFill
    case xmark
    case checkmarkCircleFill
    case checkmarkSealFill
    case sliderHorizontal3
    case squareAndPencil
    case ellipsisCircle

    // 状态指示
    case flameFill
    case sparkles
    case stopFill
    case lockShield
    case clockArrowCirclepath
    case exclamationmarkTriangle
    case exclamationmarkTriangleFill

    // 通讯交流
    case bubbleLeftAndBubbleRight
    case bubbleLeftFill
    case envelope
    case speakerWave2Fill
    case micFill
    case micSlashFill
    case paperplaneFill

    // 医疗专用
    case brainHeadProfile
    case heartFill
    case crossFill
    case noteText

    // 文档管理
    case docText
    case docTextFill
    case docTextViewfinder
    case calendar
    case link
    case squareAndArrowDown
    case squareAndArrowUp

    // 用户相关
    case personFill
    case personCircleFill
    case person2Slash
    case personCropCircleBadgePlus
    case personFillViewfinder
    case building2Slash

    // 其他
    case rectanglePortraitAndArrowRight
    case magnifyingglass
    case faceSmiling
}
