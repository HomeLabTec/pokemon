import Foundation

@MainActor
final class HoldingsViewModel: ObservableObject {
    @Published var holdings: [HoldingRow] = []
    @Published var prices: [Int: PriceRow] = [:]
    @Published var gradedMap: [Int: GradedRow] = [:]
    @Published var gradedPrices: [Int: Double] = [:]
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let client = APIClient.shared

    func loadHoldings() async {
        isLoading = true
        errorMessage = nil
        do {
            let result: [HoldingRow] = try await client.request("holdings/my")
            holdings = result
            await loadPrices(cardIds: result.map { $0.card.id })
            await loadGraded()
            await loadGradedPrices()
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
            // ignore
        }
    }

    func loadGraded() async {
        do {
            let graded: [GradedRow] = try await client.request("graded")
            var map: [Int: GradedRow] = [:]
            graded.forEach { map[$0.card_id] = $0 }
            gradedMap = map
        } catch {
            // ignore
        }
    }

    func loadGradedPrices() async {
        let ids = gradedMap.values.map { $0.id }
        guard !ids.isEmpty else { return }
        do {
            let body = try JSONSerialization.data(withJSONObject: ["graded_ids": ids, "fetch_remote": true])
            let response: GradedPricesResponse = try await client.request("graded/prices", method: "POST", body: body)
            var next: [Int: Double] = [:]
            for item in response.prices {
                if let market = item.market {
                    next[item.graded_id] = market
                }
            }
            gradedPrices = next
        } catch {
            // ignore
        }
    }

    func fetchGradedPrice(cardId: Int, grader: String, grade: String) async throws -> Double? {
        let body = try JSONSerialization.data(withJSONObject: ["card_id": cardId, "grader": grader, "grade": grade])
        let response: GradedFetchResponse = try await client.request("graded/fetch-price", method: "POST", body: body)
        return response.market
    }

    func createHolding(_ payload: HoldingCreatePayload) async throws {
        let body = try JSONEncoder().encode(payload)
        _ = try await client.request("holdings", method: "POST", body: body) as HoldingRow
    }

    func updateHolding(holdingId: Int, payload: HoldingUpdatePayload) async throws {
        let body = try JSONEncoder().encode(payload)
        _ = try await client.request("holdings/\(holdingId)", method: "PATCH", body: body) as HoldingRow
    }

    func deleteHolding(holdingId: Int) async throws {
        try await client.requestVoid("holdings/\(holdingId)", method: "DELETE")
    }
}
