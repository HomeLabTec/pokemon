import Charts
import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()
    @State private var snapshotCooldownUntil: Date? = nil
    @State private var range: RangeOption = .month1
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"

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
                await viewModel.createSnapshotAndRefresh()
            }
        }
        .onAppear {
            Task { await viewModel.loadDashboard() }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                Text("Dashboard")
                    .font(.title2.bold())
                Text("Portfolio snapshot overview")
                    .font(.footnote)
                    .foregroundColor(.white.opacity(0.6))
            }
            Spacer()
            let accent = colorFromHex(accentHex) ?? .orange
            Button {
                Task { await triggerSnapshot() }
            } label: {
                Text("$$")
                    .font(.headline)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(RoundedRectangle(cornerRadius: 12).stroke(accent))
                    .foregroundColor(accent)
            }
            .disabled(isSnapshotCoolingDown)
            .opacity(isSnapshotCoolingDown ? 0.4 : 1)
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
            let points = chartPoints.isEmpty ? fallbackPoints : chartPoints
            let filtered = range == .all ? points : points.filter { $0.date >= range.cutoffDate() }
            if filtered.isEmpty {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.white.opacity(0.06))
                    .overlay(Text("No snapshots yet").foregroundColor(.white.opacity(0.6)))
                    .frame(height: 200)
            } else {
                let accent = colorFromHex(accentHex) ?? .orange
                Chart(filtered, id: \.date) { point in
                    LineMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .interpolationMethod(.catmullRom)
                    .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round, lineJoin: .round))
                    .foregroundStyle(
                        LinearGradient(colors: [accent, accent.opacity(0.6)], startPoint: .leading, endPoint: .trailing)
                    )
                    AreaMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(
                        LinearGradient(colors: [accent.opacity(0.25), .clear], startPoint: .top, endPoint: .bottom)
                    )
                    PointMark(
                        x: .value("Date", point.date),
                        y: .value("Total", point.total)
                    )
                    .foregroundStyle(accent)
                }
                .frame(height: 200)
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 4)) { _ in
                        AxisGridLine().foregroundStyle(Color.white.opacity(0.05))
                        AxisTick().foregroundStyle(Color.white.opacity(0.5))
                        AxisValueLabel().foregroundStyle(Color.white.opacity(0.6))
                    }
                }
                .chartYAxis {
                    AxisMarks(position: .leading) { value in
                        AxisGridLine().foregroundStyle(Color.white.opacity(0.08))
                        AxisTick().foregroundStyle(Color.white.opacity(0.5))
                        AxisValueLabel() {
                            if let value = value.as(Double.self) {
                                Text(String(format: "$%.0f", value))
                            }
                        }
                    }
                }
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))
            }
            RangePicker(range: $range)
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

    private var isSnapshotCoolingDown: Bool {
        if let until = snapshotCooldownUntil {
            return Date() < until
        }
        return false
    }

    private func triggerSnapshot() async {
        guard !isSnapshotCoolingDown else { return }
        snapshotCooldownUntil = Date().addingTimeInterval(30)
        await viewModel.createSnapshotAndRefresh()
    }
}
