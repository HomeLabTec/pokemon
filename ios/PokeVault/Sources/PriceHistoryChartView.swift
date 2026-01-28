import Charts
import SwiftUI

struct PriceHistoryChartView: View {
    let points: [PricePoint]
    let label: String

    @State private var range: RangeOption = .month1
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"

    private struct StyledPoint: Hashable {
        let date: Date
        let value: Double
    }

    private var sorted: [PricePoint] {
        points.sorted { ($0.date ?? .distantPast) < ($1.date ?? .distantPast) }
    }

    var body: some View {
        let deduped = dedupe(points: sorted)
        let filtered = filter(points: deduped, range: range)

        VStack(spacing: 12) {
            if filtered.isEmpty {
                RoundedRectangle(cornerRadius: 18)
                    .fill(Color.white.opacity(0.06))
                    .overlay(Text("No price history yet").foregroundColor(.white.opacity(0.6)))
                    .frame(height: 190)
            } else {
                let accent = colorFromHex(accentHex) ?? .orange
                Chart(filtered, id: \.date) { point in
                    LineMark(
                        x: .value("Date", point.date),
                        y: .value("Price", point.value)
                    )
                    .interpolationMethod(.catmullRom)
                    .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round, lineJoin: .round))
                    .foregroundStyle(
                        LinearGradient(colors: [accent, accent.opacity(0.6)], startPoint: .leading, endPoint: .trailing)
                    )

                    AreaMark(
                        x: .value("Date", point.date),
                        y: .value("Price", point.value)
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(
                        LinearGradient(
                            colors: [accent.opacity(0.25), .clear],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                    PointMark(
                        x: .value("Date", point.date),
                        y: .value("Price", point.value)
                    )
                    .symbolSize(20)
                    .foregroundStyle(accent)
                }
                .frame(height: 190)
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
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 4)) { _ in
                        AxisGridLine().foregroundStyle(Color.white.opacity(0.05))
                        AxisTick().foregroundStyle(Color.white.opacity(0.5))
                        AxisValueLabel().foregroundStyle(Color.white.opacity(0.6))
                    }
                }
                .chartPlotStyle { plotArea in
                    plotArea
                        .background(
                            RoundedRectangle(cornerRadius: 18)
                                .fill(Color.white.opacity(0.04))
                        )
                }
                .padding(12)
            }

            RangePicker(range: $range)
        }
    }

    private func dedupe(points: [PricePoint]) -> [StyledPoint] {
        let calendar = Calendar(identifier: .gregorian)
        let chartPoints = points.compactMap { point -> (Date, Double)? in
            guard let date = point.date, let value = point.market else { return nil }
            let day = calendar.startOfDay(for: date)
            return (day, value)
        }
        return Dictionary(grouping: chartPoints, by: { $0.0 })
            .map { key, values in
                let last = values.last ?? (key, 0)
                return StyledPoint(date: key, value: last.1)
            }
            .sorted { $0.date < $1.date }
    }

    private func filter(points: [StyledPoint], range: RangeOption) -> [StyledPoint] {
        guard range != .all else { return points }
        let cutoff = range.cutoffDate()
        return points.filter { $0.date >= cutoff }
    }
}

enum RangeOption: String, CaseIterable, Identifiable {
    case day1 = "1D"
    case day7 = "7D"
    case month1 = "1M"
    case month3 = "3M"
    case month6 = "6M"
    case year1 = "1Y"
    case all = "All"

    var id: String { rawValue }

    func cutoffDate() -> Date {
        let calendar = Calendar(identifier: .gregorian)
        let now = Date()
        switch self {
        case .day1:
            return calendar.date(byAdding: .day, value: -1, to: now) ?? now
        case .day7:
            return calendar.date(byAdding: .day, value: -7, to: now) ?? now
        case .month1:
            return calendar.date(byAdding: .month, value: -1, to: now) ?? now
        case .month3:
            return calendar.date(byAdding: .month, value: -3, to: now) ?? now
        case .month6:
            return calendar.date(byAdding: .month, value: -6, to: now) ?? now
        case .year1:
            return calendar.date(byAdding: .year, value: -1, to: now) ?? now
        case .all:
            return .distantPast
        }
    }
}

struct RangePicker: View {
    @Binding var range: RangeOption
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"

    var body: some View {
        let accent = colorFromHex(accentHex) ?? .orange
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(RangeOption.allCases) { option in
                    Button(option.rawValue) {
                        range = option
                    }
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(
                        Capsule()
                            .fill(range == option ? accent : Color.white.opacity(0.08))
                    )
                    .foregroundColor(range == option ? .black : .white.opacity(0.7))
                }
            }
            .padding(.horizontal, 6)
        }
    }
}
