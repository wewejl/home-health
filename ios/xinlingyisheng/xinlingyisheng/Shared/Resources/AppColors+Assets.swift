//
//  AppColors+Assets.swift
//  灵犀健康
//
//  用途: 扩展颜色系统，添加图片资源支持

import SwiftUI

/// 扩展颜色系统
///
/// 在原有 AppColors 基础上添加图片资源加载功能
///
extension AppColors {

    // MARK: - Image Loading

    /// 从 Assets 加载图片
    static func image(named name: String) -> Image {
        Image(name)
    }

    /// 从Assets 加载可着色图片
    static func tintableImage(named name: String) -> some View {
        let bundle = Bundle.main
        if let path = bundle.path(forResource: name, ofType: "png") {
            return AnyView(Image(uiImage: .init(named: name))
                    .renderingMode(.original)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
            )
        } else {
            return Image(systemName: "photo")
        }
    }
}

// MARK: - Preview Provider

#if DEBUG
struct AppColorsAssets_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Image Loading")
                .foregroundColor(AppColors.primary)
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
