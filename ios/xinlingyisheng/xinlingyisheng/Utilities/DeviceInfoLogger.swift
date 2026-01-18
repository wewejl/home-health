import SwiftUI

struct DeviceInfoLogger {
    static func log(context: String) {
        #if DEBUG
        DispatchQueue.main.async {
            let device = UIDevice.current
            let screen = UIScreen.main
            let bounds = screen.bounds
            let nativeBounds = screen.nativeBounds
            let scale = screen.scale
            let nativeScale = screen.nativeScale
            let preferredContentSize = UIApplication.shared.preferredContentSizeCategory
            
            var safeAreaText = "unknown"
            if let windowScene = UIApplication.shared.connectedScenes
                .compactMap({ $0 as? UIWindowScene }).first,
               let window = windowScene.windows.first(where: { $0.isKeyWindow }) {
                let insets = window.safeAreaInsets
                safeAreaText = "top: \(insets.top), bottom: \(insets.bottom), left: \(insets.left), right: \(insets.right)"
            }
            
            print("===== DeviceInfo (\(context)) =====")
            print("Device: \(device.model) - \(device.name)")
            print("System: iOS \(device.systemVersion)")
            print("Screen bounds: \(bounds.width)x\(bounds.height) @\(scale)x")
            print("Native bounds: \(nativeBounds.width)x\(nativeBounds.height) @\(nativeScale)x")
            print("Safe area insets: \(safeAreaText)")
            print("Preferred content size: \(preferredContentSize.rawValue)")
            print("==================================")
        }
        #endif
    }
}
