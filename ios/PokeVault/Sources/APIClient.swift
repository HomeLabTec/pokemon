import Foundation

final class APIClient: ObservableObject {
    @Published var token: String? {
        didSet {
            if let token {
                KeychainStore.save(token, for: "pv_token")
            } else {
                KeychainStore.delete("pv_token")
            }
        }
    }

    static let shared = APIClient()

    private init() {
        token = KeychainStore.load("pv_token")
    }

    func request<T: Decodable>(_ path: String, method: String = "GET", body: Data? = nil) async throws -> T {
        let trimmed = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        let url = AppConfig.apiBaseURL.appendingPathComponent(trimmed)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        let (data, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
            let message = String(data: data, encoding: .utf8) ?? "Request failed"
            throw NSError(domain: "API", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: message])
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    func requestVoid(_ path: String, method: String = "POST", body: Data? = nil) async throws {
        let trimmed = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        let url = AppConfig.apiBaseURL.appendingPathComponent(trimmed)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        let (_, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
            throw NSError(domain: "API", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: "Request failed"])
        }
    }
}
