import SwiftUI

struct CardDetailView: View {
    let title: String
    let subtitle: String
    let imageURL: String?
    let fallbackImageURL: URL?
    let priceLabel: String
    let latestPrice: Double?
    let priceHistory: [PricePoint]
    let details: [(String, String)]
    let primaryActionTitle: String?
    let primaryAction: (() -> Void)?
    let secondaryActionTitle: String?
    let secondaryAction: (() -> Void)?
    let destructiveActionTitle: String?
    let destructiveAction: (() -> Void)?

    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 16) {
                header
                ScrollView {
                    VStack(spacing: 20) {
                        heroImage
                        detailCard
                        PriceHistoryChartView(points: priceHistory, label: priceLabel)
                        let accent = Color.fromHex(accentHex) ?? .orange
                        if let primaryActionTitle, let primaryAction {
                            Button(primaryActionTitle) {
                                primaryAction()
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(RoundedRectangle(cornerRadius: 18).fill(accent))
                            .foregroundColor(.black)
                            .padding(.horizontal)
                        }
                        if let secondaryActionTitle, let secondaryAction {
                            Button(secondaryActionTitle) {
                                secondaryAction()
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(RoundedRectangle(cornerRadius: 18).stroke(accent))
                            .foregroundColor(accent)
                            .padding(.horizontal)
                            .padding(.bottom, 4)
                        }
                        if let destructiveActionTitle, let destructiveAction {
                            Button(destructiveActionTitle) {
                                destructiveAction()
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(RoundedRectangle(cornerRadius: 18).stroke(Color.red))
                            .foregroundColor(.red)
                            .padding(.horizontal)
                            .padding(.bottom, 8)
                        }
                    }
                    .padding(.horizontal)
                }
            }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.title2.bold())
                Text(subtitle)
                    .font(.footnote)
                    .foregroundColor(.white.opacity(0.6))
            }
            Spacer()
            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.title2)
                    .foregroundColor(.white.opacity(0.6))
            }
        }
        .padding()
        .foregroundColor(.white)
    }

    private var heroImage: some View {
        Group {
            if let url = resolvedImageURL {
                CachedAsyncImage(url: url, cornerRadius: 24)
            } else {
                RoundedRectangle(cornerRadius: 24)
                    .fill(Color.white.opacity(0.06))
                    .frame(height: 420)
            }
        }
        .frame(maxHeight: 520)
        .shadow(color: .black.opacity(0.4), radius: 20, x: 0, y: 12)
        .padding(.top, 12)
    }

    private var detailCard: some View {
        VStack(spacing: 12) {
            HStack {
                Text(latestPriceText)
                    .font(.title3.bold())
                    .foregroundColor(Color.fromHex(accentHex) ?? .orange)
                Spacer()
                Text(priceLabel)
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.6))
            }
            ForEach(details.filter { !$0.1.isEmpty }, id: \.0) { row in
                HStack {
                    Text(row.0)
                        .foregroundColor(.white.opacity(0.5))
                    Spacer()
                    Text(row.1)
                        .foregroundColor(.white.opacity(0.85))
                }
                .font(.subheadline)
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 20).fill(Color.white.opacity(0.06)))
    }

    private var latestPriceText: String {
        guard let latestPrice else { return "—" }
        return String(format: "$%.2f", latestPrice)
    }

    private var resolvedImageURL: URL? {
        if let imageURL, let localURL = URL(string: imageURL) {
            if imageURL.hasPrefix("/") {
                let trimmed = imageURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
                return AppConfig.apiBaseURL
                    .deletingLastPathComponent()
                    .appendingPathComponent(trimmed)
            }
            return localURL
        }
        return fallbackImageURL
    }
}
