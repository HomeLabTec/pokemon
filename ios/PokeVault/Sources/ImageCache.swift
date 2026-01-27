import SwiftUI

final class ImageCache {
    static let shared = ImageCache()

    private let fileManager = FileManager.default
    private let cacheDir: URL
    private let session: URLSession

    private init() {
        cacheDir = fileManager.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("images")
        if !fileManager.fileExists(atPath: cacheDir.path) {
            try? fileManager.createDirectory(at: cacheDir, withIntermediateDirectories: true)
        }
        let config = URLSessionConfiguration.default
        config.urlCache = URLCache(memoryCapacity: 64 * 1024 * 1024, diskCapacity: 256 * 1024 * 1024)
        session = URLSession(configuration: config)
    }

    func image(for url: URL) async throws -> UIImage {
        let fileURL = cacheDir.appendingPathComponent(cacheKey(for: url))
        if let data = try? Data(contentsOf: fileURL), let image = UIImage(data: data) {
            return image
        }
        let (data, _) = try await session.data(from: url)
        if let image = UIImage(data: data) {
            try? data.write(to: fileURL)
            return image
        }
        throw NSError(domain: "ImageCache", code: -1)
    }

    private func cacheKey(for url: URL) -> String {
        let raw = url.absoluteString
        let hashed = String(raw.hashValue)
        let ext = url.pathExtension.isEmpty ? "img" : url.pathExtension
        return "img_\(hashed).\(ext)"
    }
}

struct CachedAsyncImage: View {
    let url: URL?
    let cornerRadius: CGFloat

    @State private var image: UIImage?
    @State private var isLoading = false

    var body: some View {
        ZStack {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .clipShape(RoundedRectangle(cornerRadius: cornerRadius))
            } else {
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(Color.white.opacity(0.06))
                    .overlay(
                        ProgressView().opacity(isLoading ? 1 : 0)
                    )
            }
        }
        .task(id: url?.absoluteString) {
            guard let url else { return }
            isLoading = true
            do {
                image = try await ImageCache.shared.image(for: url)
            } catch {
                image = nil
            }
            isLoading = false
        }
    }
}
