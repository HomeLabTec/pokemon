import Charts
import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    private struct ChartPoint: Hashable {
        let date: Date
        let total: Double
    }

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    header
                    summaryCards
                    portfolioChart
                }
                .padding()
            }
            .refreshable {
                await viewModel.createSnapshot()
                await viewModel.loadDashboard()
            }
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
            let chartPoints = viewModel.portfolio.compactMap { point -> ChartPoint? in
                guard let date = point.date else { return nil }
                return ChartPoint(date: date, total: point.total)
            }
            let fallbackPoints: [ChartPoint] = {
                if let total = viewModel.computedTotal {
                    return [ChartPoint(date: Date(), total: total)]
                }
                return []
            }()
            if chartPoints.isEmpty && fallbackPoints.isEmpty {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.white.opacity(0.06))
                    .overlay(Text("No snapshots yet").foregroundColor(.white.opacity(0.6)))
                    .frame(height: 200)
            } else {
                let points = chartPoints.isEmpty ? fallbackPoints : chartPoints
                Chart(points, id: \.date) { point in
                    LineMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(.orange)
                    AreaMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(.orange.opacity(0.2))
                    PointMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(.orange)
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
