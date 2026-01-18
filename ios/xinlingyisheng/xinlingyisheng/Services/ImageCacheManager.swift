import UIKit
import SwiftUI

class ImageCacheManager {
    static let shared = ImageCacheManager()
    
    private let cache = NSCache<NSString, UIImage>()
    private let fileManager = FileManager.default
    private let cacheDirectory: URL
    
    private init() {
        let paths = fileManager.urls(for: .cachesDirectory, in: .userDomainMask)
        cacheDirectory = paths[0].appendingPathComponent("MedicalDossierImages")
        
        try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
        
        cache.countLimit = 100
        cache.totalCostLimit = 50 * 1024 * 1024 // 50 MB
    }
    
    func image(for key: String) -> UIImage? {
        if let cached = cache.object(forKey: key as NSString) {
            return cached
        }
        
        let filePath = cacheDirectory.appendingPathComponent(key.sha256Hash)
        if let data = try? Data(contentsOf: filePath),
           let image = UIImage(data: data) {
            cache.setObject(image, forKey: key as NSString)
            return image
        }
        
        return nil
    }
    
    func setImage(_ image: UIImage, for key: String) {
        cache.setObject(image, forKey: key as NSString)
        
        let filePath = cacheDirectory.appendingPathComponent(key.sha256Hash)
        if let data = image.jpegData(compressionQuality: 0.8) {
            try? data.write(to: filePath)
        }
    }
    
    func clearCache() {
        cache.removeAllObjects()
        try? fileManager.removeItem(at: cacheDirectory)
        try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
    }
    
    func thumbnail(for key: String, size: CGSize) -> UIImage? {
        let thumbnailKey = "\(key)_\(Int(size.width))x\(Int(size.height))"
        
        if let cached = image(for: thumbnailKey) {
            return cached
        }
        
        if let original = image(for: key) {
            let thumbnail = original.thumbnail(size: size)
            setImage(thumbnail, for: thumbnailKey)
            return thumbnail
        }
        
        return nil
    }
}

extension String {
    var sha256Hash: String {
        let data = Data(self.utf8)
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes {
            _ = CC_SHA256($0.baseAddress, CC_LONG(data.count), &hash)
        }
        return hash.map { String(format: "%02x", $0) }.joined()
    }
}

import CommonCrypto

extension UIImage {
    func thumbnail(size: CGSize) -> UIImage {
        let aspectRatio = self.size.width / self.size.height
        var targetSize = size
        
        if aspectRatio > 1 {
            targetSize.height = size.width / aspectRatio
        } else {
            targetSize.width = size.height * aspectRatio
        }
        
        let renderer = UIGraphicsImageRenderer(size: targetSize)
        return renderer.image { _ in
            self.draw(in: CGRect(origin: .zero, size: targetSize))
        }
    }
}

struct CachedAsyncImage: View {
    let url: String
    let placeholder: Image
    
    @State private var image: UIImage?
    @State private var isLoading = false
    
    var body: some View {
        Group {
            if let image = image {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } else {
                placeholder
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .overlay(
                        Group {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                            }
                        }
                    )
            }
        }
        .onAppear {
            loadImage()
        }
    }
    
    private func loadImage() {
        if let cached = ImageCacheManager.shared.image(for: url) {
            self.image = cached
            return
        }
        
        guard !isLoading else { return }
        isLoading = true
        
        Task {
            guard let imageUrl = URL(string: url) else {
                isLoading = false
                return
            }
            
            do {
                let (data, _) = try await URLSession.shared.data(from: imageUrl)
                if let downloadedImage = UIImage(data: data) {
                    ImageCacheManager.shared.setImage(downloadedImage, for: url)
                    await MainActor.run {
                        self.image = downloadedImage
                        self.isLoading = false
                    }
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }
}
