import Charts
import SwiftUI

struct PriceHistoryChartView: View {
    let points: [PricePoint]
    let label: String

    private var sorted: [PricePoint] {
        points.sorted { ($0.date ?? .distantPast) < ($1.date ?? .distantPast) }
    }

    var body: some View {
        let calendar = Calendar(identifier: .gregorian)
        let chartPoints = sorted.compactMap { point -> (Date, Double)? in
            guard let date = point.date, let value = point.market else { return nil }
            let day = calendar.startOfDay(for: date)
            return (day, value)
        }
        let deduped = Dictionary(grouping: chartPoints, by: { $0.0 })
            .map { key, values in
                let last = values.last ?? (key, 0)
                return (key, last.1)
            }
            .sorted { $0.0 < $1.0 }
        if deduped.isEmpty {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white.opacity(0.06))
                .overlay(Text("No price history yet").foregroundColor(.white.opacity(0.6)))
                .frame(height: 180)
        } else {
            Chart(deduped, id: \.0) { point in
                LineMark(
                    x: .value("Date", point.0),
                    y: .value("Price", point.1)
                )
                .foregroundStyle(.orange)
                AreaMark(
                    x: .value("Date", point.0),
                    y: .value("Price", point.1)
                )
                .foregroundStyle(.orange.opacity(0.2))
                PointMark(
                    x: .value("Date", point.0),
                    y: .value("Price", point.1)
                )
                .foregroundStyle(.orange)
            }
            .frame(height: 180)
            .chartYAxis {
                AxisMarks(position: .leading)
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 4))
            }
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))
        }
    }
}
