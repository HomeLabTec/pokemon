import Foundation

struct CardIdentifyResult {
    let name: String?
    let number: String?
    let rawResponse: String
}

enum CardIdentifyError: LocalizedError {
    case unprocessable
    case invalidResponse
    case invalidData
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .unprocessable:
            return "Could not identify card."
        case .invalidResponse:
            return "Invalid response from server."
        case .invalidData:
            return "Invalid card image data."
        case .serverError(let message):
            return message
        }
    }
}

final class CardIdentifierClient {
    static let shared = CardIdentifierClient()

    private init() {}

    func identify(
        imageData: Data,
        filename: String = "card.jpg",
        mimeType: String = "image/jpeg",
        connectTimeout: TimeInterval = 8,
        requestTimeout: TimeInterval = 90
    ) async throws -> CardIdentifyResult {
        guard let url = URL(string: "identify", relativeTo: AppConfig.cardIdServerURL) else {
            throw CardIdentifyError.invalidResponse
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = requestTimeout

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = buildMultipartBody(
            boundary: boundary,
            fieldName: "file",
            filename: filename,
            mimeType: mimeType,
            fileData: imageData
        )

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = connectTimeout
        config.timeoutIntervalForResource = requestTimeout
        let session = URLSession(configuration: config)

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw CardIdentifyError.invalidResponse
        }

        if http.statusCode == 422 {
            throw CardIdentifyError.unprocessable
        }
        guard (200..<300).contains(http.statusCode) else {
            let message = String(data: data, encoding: .utf8) ?? "Server error"
            throw CardIdentifyError.serverError(message)
        }

        let raw = String(data: data, encoding: .utf8) ?? ""
        #if DEBUG
        if !raw.isEmpty {
            print("[CardID] raw response: \(raw)")
        }
        #endif
        let decoded = try JSONDecoder().decode(CardIdentifyResponse.self, from: data)
        return CardIdentifyResult(name: decoded.ocr?.name, number: decoded.ocr?.number, rawResponse: raw)
    }

    private func buildMultipartBody(
        boundary: String,
        fieldName: String,
        filename: String,
        mimeType: String,
        fileData: Data
    ) -> Data {
        var body = Data()
        let boundaryPrefix = "--\(boundary)\r\n"
        body.append(boundaryPrefix.data(using: .utf8) ?? Data())
        body.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(filename)\"\r\n".data(using: .utf8) ?? Data())
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8) ?? Data())
        body.append(fileData)
        body.append("\r\n".data(using: .utf8) ?? Data())
        body.append("--\(boundary)--\r\n".data(using: .utf8) ?? Data())
        return body
    }
}
