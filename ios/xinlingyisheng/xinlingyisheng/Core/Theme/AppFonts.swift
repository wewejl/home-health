//
//  AppFonts.swift
//

import SwiftUI

enum AppFonts {
    static let large: CGFloat = 20
    static let title1: CGFloat = 18
    static let body: CGFloat = 14
    static let caption1: CGFloat = 12
}

#if DEBUG
struct AppFonts_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            Text("Large").font(.system(size: 20))
            Text("Title 1").font(.system(size: 18))
            Text("Body").font(.system(size: 14))
            Text("Caption 1").font(.system(size: 12))
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
