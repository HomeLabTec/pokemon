import Foundation

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var portfolio: [PortfolioPoint] = []
    @Published var holdingsCount = 0
    @Published var gradedCount = 0
    @Published var isLoading = false

    private let client = APIClient.shared

    func loadDashboard() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: PortfolioResponse = try await client.request("analytics/portfolio")
            portfolio = response.data.sorted { $0.ts < $1.ts }
        } catch {
            portfolio = []
        }
        do {
            let holdings: [HoldingRow] = try await client.request("holdings/my")
            holdingsCount = holdings.count
        } catch {
            holdingsCount = 0
        }
        do {
            let graded: [GradedRow] = try await client.request("graded")
            gradedCount = graded.count
        } catch {
            gradedCount = 0
        }
    }
}
