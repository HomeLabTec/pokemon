import Foundation

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var portfolio: [PortfolioPoint] = []
    @Published var holdingsCount = 0
    @Published var gradedCount = 0
    @Published var computedTotal: Double?
    @Published var isLoading = false

    private let client = APIClient.shared

    func loadDashboard() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: PortfolioResponse = try await client.request("analytics/portfolio")
            let sorted = response.data.sorted { $0.ts < $1.ts }
            if !sorted.isEmpty || portfolio.isEmpty {
                portfolio = sorted
            }
        } catch {
            // keep existing data on refresh failures
        }
        do {
            let holdings: [HoldingRow] = try await client.request("holdings/my")
            holdingsCount = holdings.count
            computedTotal = try await computeTotal(for: holdings)
        } catch {
            // keep existing counts on refresh failures
        }
        do {
            let graded: [GradedRow] = try await client.request("graded")
            gradedCount = graded.count
        } catch {
            // keep existing counts on refresh failures
        }
    }

    func createSnapshot() async {
        do {
            try await client.requestVoid("analytics/portfolio/snapshot", method: "POST")
        } catch {
            // ignore
        }
    }

    func createSnapshotAndRefresh() async {
        await createSnapshot()
        await loadDashboard()
    }

    private func computeTotal(for holdings: [HoldingRow]) async throws -> Double? {
        guard !holdings.isEmpty else { return nil }
        let cardIds = holdings.map { $0.card.id }
        let priceBody = try JSONSerialization.data(withJSONObject: ["card_ids": cardIds, "fetch_remote": true])
        let priceResponse: CardPricesResponse = try await client.request("cards/prices", method: "POST", body: priceBody)
        var priceMap: [Int: Double] = [:]
        priceResponse.prices.forEach { priceMap[$0.card_id] = $0.market }

        let graded: [GradedRow] = (try? await client.request("graded")) ?? []
        var gradedMap: [Int: GradedRow] = [:]
        graded.forEach { gradedMap[$0.card_id] = $0 }
        let gradedIds = graded.map { $0.id }
        var gradedPriceMap: [Int: Double] = [:]
        if !gradedIds.isEmpty {
            let gradedBody = try JSONSerialization.data(withJSONObject: ["graded_ids": gradedIds, "fetch_remote": true])
            let gradedResponse: GradedPricesResponse = try await client.request("graded/prices", method: "POST", body: gradedBody)
            gradedResponse.prices.forEach {
                if let market = $0.market {
                    gradedPriceMap[$0.graded_id] = market
                }
            }
        }

        var total: Double = 0
        for holding in holdings {
            if let graded = gradedMap[holding.card.id], let gradedValue = gradedPriceMap[graded.id] {
                total += gradedValue * Double(holding.quantity)
            } else if let market = priceMap[holding.card.id] {
                total += market * Double(holding.quantity)
            }
        }
        return total
    }
}
