import Charts
import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 16) {
                header
                summaryCards
                portfolioChart
                Spacer()
            }
            .padding()
        }
        .onAppear {
            Task { await viewModel.loadDashboard() }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Dashboard")
                .font(.title2.bold())
            Text("Portfolio snapshot overview")
                .font(.footnote)
                .foregroundColor(.white.opacity(0.6))
        }
        .foregroundColor(.white)
    }

    private var summaryCards: some View {
        HStack(spacing: 12) {
            summaryCard(title: "Holdings", value: "\(viewModel.holdingsCount)")
            summaryCard(title: "Graded", value: "\(viewModel.gradedCount)")
            summaryCard(title: "Latest Total", value: latestTotalText)
        }
    }

    private func summaryCard(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.6))
            Text(value)
                .font(.headline)
                .foregroundColor(.white)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))
    }

    private var portfolioChart: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Total value")
                .font(.subheadline.weight(.semibold))
                .foregroundColor(.white)
            if viewModel.portfolio.isEmpty {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.white.opacity(0.06))
                    .overlay(Text("No snapshots yet").foregroundColor(.white.opacity(0.6)))
                    .frame(height: 200)
            } else {
                Chart(viewModel.portfolio, id: \.ts) { point in
                    LineMark(
                        x: .value("Date", point.ts),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(.orange)
                    AreaMark(
                        x: .value("Date", point.ts),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(.orange.opacity(0.2))
                }
                .frame(height: 200)
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 4))
                }
                .chartYAxis {
                    AxisMarks(position: .leading)
                }
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))
            }
        }
    }

    private var latestTotalText: String {
        guard let last = viewModel.portfolio.last else { return "—" }
        return String(format: "$%.0f", last.total)
    }
}
