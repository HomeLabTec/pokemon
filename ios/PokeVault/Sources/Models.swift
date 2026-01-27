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
        ISO8601DateFormatter().date(from: ts)
    }
}

struct CardDetailResponse: Codable {
    let card: CardRow
    let images: [CardImageRow]
    let latest_prices: [LatestPriceRow]
    let price_history: [PricePoint]
}

struct HoldingRow: Codable, Identifiable, Hashable {
    let holding_id: Int
    let quantity: Int
    let condition: String
    let is_for_trade: Bool
    let is_wantlist: Bool
    let is_watched: Bool
    let notes: String?
    let card: CardRow
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

struct PortfolioPoint: Codable, Hashable {
    let ts: String
    let total: Double
    let raw: Double
    let graded: Double
}

struct PortfolioResponse: Codable {
    let range: String
    let data: [PortfolioPoint]
}
