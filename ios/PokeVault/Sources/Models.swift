import Foundation

struct SetRow: Codable, Identifiable, Hashable {
    let id: Int
    let code: String
    let name: String
    let series: String?
}

struct CardRow: Codable, Identifiable, Hashable {
    let id: Int
    let set_id: Int
    let number: String
    let name: String
    let rarity: String?
    let supertype: String?
    let subtypes: [String]?
    let types: [String]?
    let hp: String?
    let artist: String?
}

struct CardImageRow: Codable, Hashable {
    let kind: String
    let local_path: String?
}

struct LatestPriceRow: Codable, Hashable {
    let market: Double?
    let updated_at: String?
    let source: String?
    let source_type: String?
}

struct PricePoint: Codable, Hashable {
    let ts: String
    let market: Double?

    var date: Date? {
        DateParser.shared.parse(ts)
    }
}

struct CardDetailResponse: Codable {
    let card: CardRow
    let images: [CardImageRow]
    let latest_prices: [LatestPriceRow]
    let price_history: [PricePoint]
}

struct HoldingCardRow: Codable, Hashable {
    let id: Int
    let name: String
    let number: String
    let rarity: String?
}

struct HoldingRow: Codable, Identifiable, Hashable {
    let holding_id: Int
    let quantity: Int
    let condition: String
    let is_for_trade: Bool
    let is_wantlist: Bool
    let is_watched: Bool
    let notes: String?
    let card: HoldingCardRow
    let set: SetRow

    var id: Int { holding_id }
}

struct GradedRow: Codable, Identifiable, Hashable {
    let id: Int
    let card_id: Int
    let grader: String
    let grade: String
}

struct GradedHistoryResponse: Codable {
    let graded: GradedRow
    let price_history: [PricePoint]
}

struct CardSearchResponse: Codable {
    let cards: [CardRow]
}

struct PriceRow: Codable, Hashable {
    let card_id: Int
    let market: Double?
    let source: String?
    let source_type: String?
}

struct CardPricesResponse: Codable {
    let prices: [PriceRow]
}

struct HoldingCreatePayload: Codable {
    let card_id: Int
    let quantity: Int
    let condition: String
    let is_for_trade: Bool
    let is_wantlist: Bool
    let is_watched: Bool
    let notes: String?
}

struct HoldingUpdatePayload: Codable {
    let quantity: Int?
    let condition: String?
    let is_for_trade: Bool?
    let is_wantlist: Bool?
    let is_watched: Bool?
    let notes: String?
}

struct GradedFetchResponse: Codable {
    let graded_id: Int
    let market: Double?
    let source: String?
    let source_type: String?
}

struct GradedPriceRow: Codable {
    let graded_id: Int
    let market: Double?
    let source: String?
    let source_type: String?
}

struct GradedPricesResponse: Codable {
    let prices: [GradedPriceRow]
}

struct CardIdentifyOCR: Codable {
    let name: String?
    let number: String?
}

struct CardIdentifyResponse: Codable {
    let ocr: CardIdentifyOCR?
}

struct PortfolioPoint: Codable, Hashable {
    let ts: String
    let total: Double
    let raw: Double
    let graded: Double

    var date: Date? {
        DateParser.shared.parse(ts)
    }
}

struct PortfolioResponse: Codable {
    let range: String
    let data: [PortfolioPoint]
}

final class DateParser {
    static let shared = DateParser()

    private let formatter: ISO8601DateFormatter
    private let fallbackFormatters: [DateFormatter]

    private init() {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        self.formatter = formatter

        let formats = [
            "yyyy-MM-dd'T'HH:mm:ss.SSSZ",
            "yyyy-MM-dd'T'HH:mm:ssZ",
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
            "yyyy-MM-dd'T'HH:mm:ss.SSS",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd",
        ]
        self.fallbackFormatters = formats.map { format in
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = TimeZone(secondsFromGMT: 0)
            formatter.dateFormat = format
            return formatter
        }
    }

    func parse(_ value: String) -> Date? {
        if let date = formatter.date(from: value) {
            return date
        }
        if let date = ISO8601DateFormatter().date(from: value) {
            return date
        }
        for formatter in fallbackFormatters {
            if let date = formatter.date(from: value) {
                return date
            }
        }
        return nil
    }
}
