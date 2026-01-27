import Charts
import SwiftUI

struct PriceHistoryChartView: View {
    let points: [PricePoint]
    let label: String

    private var sorted: [PricePoint] {
        points.sorted { ($0.date ?? .distantPast) < ($1.date ?? .distantPast) }
    }

    var body: some View {
        if sorted.isEmpty {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white.opacity(0.06))
                .overlay(Text("No price history yet").foregroundColor(.white.opacity(0.6)))
                .frame(height: 180)
        } else {
            Chart(sorted, id: \.ts) { point in
                if let value = point.market, let date = point.date {
                    LineMark(
                        x: .value("Date", date),
                        y: .value("Price", value)
                    )
                    .foregroundStyle(.orange)
                    AreaMark(
                        x: .value("Date", date),
                        y: .value("Price", value)
                    )
                    .foregroundStyle(.orange.opacity(0.2))
                }
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
