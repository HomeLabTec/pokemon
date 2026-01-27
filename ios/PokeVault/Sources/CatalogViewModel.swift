import Foundation

@MainActor
final class CatalogViewModel: ObservableObject {
    @Published var sets: [SetRow] = []
    @Published var cards: [CardRow] = []
    @Published var prices: [Int: PriceRow] = [:]
    @Published var selectedSetId: Int?
    @Published var search: String = ""
    @Published var rarity: String = ""
    @Published var artist: String = ""
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let client = APIClient.shared

    func loadSets() async {
        do {
            let result: [SetRow] = try await client.request("sets")
            sets = result
            if selectedSetId == nil {
                selectedSetId = result.first?.id
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadCards() async {
        isLoading = true
        errorMessage = nil
        do {
            var components = URLComponents()
            components.path = "/cards/search"
            var query: [URLQueryItem] = []
            if let selectedSetId {
                query.append(URLQueryItem(name: "set_id", value: String(selectedSetId)))
            }
            if !search.trimmingCharacters(in: .whitespaces).isEmpty {
                query.append(URLQueryItem(name: "q", value: search))
            }
            if !rarity.trimmingCharacters(in: .whitespaces).isEmpty {
                query.append(URLQueryItem(name: "rarity", value: rarity))
            }
            if !artist.trimmingCharacters(in: .whitespaces).isEmpty {
                query.append(URLQueryItem(name: "artist", value: artist))
            }
            components.queryItems = query
            let queryString = components.percentEncodedQuery ?? ""
            let path = queryString.isEmpty ? "cards/search" : "cards/search?\(queryString)"
            let result: [CardRow] = try await client.request(path)
            cards = result
            await loadPrices(cardIds: result.map { $0.id })
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadPrices(cardIds: [Int]) async {
        guard !cardIds.isEmpty else { return }
        do {
            let body = try JSONSerialization.data(withJSONObject: ["card_ids": cardIds, "fetch_remote": true])
            let response: CardPricesResponse = try await client.request("cards/prices", method: "POST", body: body)
            var next: [Int: PriceRow] = [:]
            response.prices.forEach { next[$0.card_id] = $0 }
            prices = next
        } catch {
            // ignore price errors
        }
    }
}
