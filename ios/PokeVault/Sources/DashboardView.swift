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
                Chart(viewModel.portfolio.compactMap { point in
                    guard let date = point.date else { return nil }
                    return (date, point.total)
                }, id: \.0) { point in
                    LineMark(
                        x: .value("Date", point.0),
                        y: .value("Total", point.1)
                    )
                    .foregroundStyle(.orange)
                    AreaMark(
                        x: .value("Date", point.0),
                        y: .value("Total", point.1)
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
        if let last = viewModel.portfolio.last {
            return String(format: "$%.0f", last.total)
        }
        if let computed = viewModel.computedTotal {
            return String(format: "$%.0f", computed)
        }
        return "—"
    }
}
