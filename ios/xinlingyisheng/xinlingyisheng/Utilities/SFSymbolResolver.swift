import UIKit

enum SFSymbolResolver {
    static func resolve(_ name: String?, fallback: String = "cross.case") -> String {
        guard let symbol = name, !symbol.isEmpty else {
            return fallback
        }
        
        return UIImage(systemName: symbol) != nil ? symbol : fallback
    }
}
