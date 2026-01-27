import SwiftUI

struct HoldingsView: View {
    @StateObject private var viewModel = HoldingsViewModel()
    @State private var selectedHolding: HoldingRow?
    @State private var detail: CardDetailResponse?
    @State private var gradedHistory: [PricePoint] = []
    @State private var showDetail = false
    @State private var detailLoading = false
    @State private var activeSheet: HoldingSheet?
    @State private var editQuantity = 1
    @State private var editCondition = "NM"
    @State private var editForTrade = false
    @State private var editWantlist = false
    @State private var editWatched = false
    @State private var grader = "PSA"
    @State private var grade = ""

    private let columns = [GridItem(.adaptive(minimum: 170), spacing: 16)]

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 16) {
                header
                if viewModel.isLoading {
                    ProgressView().tint(.orange)
                }
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 16) {
                        ForEach(viewModel.holdings) { item in
                            HoldingCardView(
                                item: item,
                                price: viewModel.prices[item.card.id]?.market,
                                graded: viewModel.gradedMap[item.card.id],
                                gradedPrice: viewModel.gradedMap[item.card.id].flatMap { viewModel.gradedPrices[$0.id] }
                            )
                            .onTapGesture {
                                Task { await openDetail(item) }
                            }
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    .padding(.horizontal)
                    .animation(.easeInOut(duration: 0.25), value: viewModel.holdings)
                }
            }
        }
        .onAppear {
            Task { await viewModel.loadHoldings() }
        }
        .fullScreenCover(isPresented: $showDetail) {
            if let holding = selectedHolding {
                if let detail {
                    let graded = viewModel.gradedMap[holding.card.id]
                    CardDetailView(
                        title: detail.card.name,
                        subtitle: "\(holding.set.name) • \(detail.card.number) • \(detail.card.rarity ?? "Unknown rarity")",
                        imageURL: detail.images.first(where: { $0.kind == "large" && $0.local_path != nil })?.local_path,
                        fallbackImageURL: remoteImageURL(for: detail.card, set: holding.set),
                        priceLabel: graded != nil ? "\(graded!.grader) \(graded!.grade) market history" : "NM market history",
                        latestPrice: graded != nil ? viewModel.gradedPrices[graded!.id] : detail.latest_prices.first?.market,
                        priceHistory: graded != nil ? gradedHistory : detail.price_history,
                        details: [
                            ("Set", holding.set.name),
                            ("Number", detail.card.number),
                            ("Rarity", detail.card.rarity ?? ""),
                            ("Condition", holding.condition),
                            ("Quantity", "\(holding.quantity)"),
                            ("Grade", graded != nil ? "\(graded!.grader) \(graded!.grade)" : ""),
                            ("Supertype", detail.card.supertype ?? ""),
                            ("Subtypes", detail.card.subtypes?.joined(separator: ", ") ?? ""),
                            ("Types", detail.card.types?.joined(separator: ", ") ?? ""),
                            ("HP", detail.card.hp ?? ""),
                            ("Artist", detail.card.artist ?? ""),
                        ],
                        primaryActionTitle: "Edit holding",
                        primaryAction: { presentEdit(holding) },
                        secondaryActionTitle: "Get graded value",
                        secondaryAction: { presentGradedLookup(holding) }
                    )
                } else {
                    DetailLoadingView(isLoading: detailLoading)
                }
            }
        }
        .sheet(item: $activeSheet) { sheet in
            switch sheet {
            case .edit:
                HoldingFormView(
                    title: "Edit holding",
                    cardName: selectedHolding?.card.name,
                    cardImageURL: selectedHolding.flatMap { holding in
                        URL(string: "https://images.pokemontcg.io/\(holding.set.code)/\(holding.card.number).png")
                    },
                    quantity: $editQuantity,
                    condition: $editCondition,
                    isForTrade: $editForTrade,
                    isWantlist: $editWantlist,
                    isWatched: $editWatched,
                    onSave: { Task { await saveEdit() } },
                    onCancel: { activeSheet = nil }
                )
            case .graded:
                GradedLookupView(
                    grader: $grader,
                    grade: $grade,
                    onFetch: { Task { await fetchGraded() } },
                    onCancel: { activeSheet = nil }
                )
            }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Holdings")
                    .font(.title2.bold())
                Text("Your collection at a glance")
                    .foregroundColor(.white.opacity(0.6))
                    .font(.footnote)
            }
            Spacer()
        }
        .padding(.horizontal)
        .foregroundColor(.white)
    }

    private func openDetail(_ item: HoldingRow) async {
        selectedHolding = item
        detail = nil
        detailLoading = true
        showDetail = true
        do {
            let detail: CardDetailResponse = try await APIClient.shared.request("cards/\(item.card.id)")
            self.detail = detail
            if let graded = viewModel.gradedMap[item.card.id] {
                let history: GradedHistoryResponse = try await APIClient.shared.request("graded/\(graded.id)/history")
                gradedHistory = history.price_history
            } else {
                gradedHistory = []
            }
        } catch {
            // ignore
        }
        detailLoading = false
    }

    private func presentEdit(_ item: HoldingRow) {
        editQuantity = item.quantity
        editCondition = item.condition
        editForTrade = item.is_for_trade
        editWantlist = item.is_wantlist
        editWatched = item.is_watched
        showDetail = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            activeSheet = .edit
        }
    }

    private func saveEdit() async {
        guard let holding = selectedHolding else { return }
        let payload = HoldingUpdatePayload(
            quantity: editQuantity,
            condition: editCondition,
            is_for_trade: editForTrade,
            is_wantlist: editWantlist,
            is_watched: editWatched,
            notes: nil
        )
        do {
            try await viewModel.updateHolding(holdingId: holding.holding_id, payload: payload)
            await viewModel.loadHoldings()
            activeSheet = nil
        } catch {
            activeSheet = nil
        }
    }

    private func presentGradedLookup(_ item: HoldingRow) {
        if let graded = viewModel.gradedMap[item.card.id] {
            grader = graded.grader
            grade = graded.grade
        } else {
            grader = "PSA"
            grade = ""
        }
        showDetail = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            activeSheet = .graded
        }
    }

    private func fetchGraded() async {
        guard let holding = selectedHolding else { return }
        do {
            _ = try await viewModel.fetchGradedPrice(cardId: holding.card.id, grader: grader, grade: grade)
            await viewModel.loadGraded()
            await viewModel.loadGradedPrices()
            activeSheet = nil
        } catch {
            activeSheet = nil
        }
    }

    private func remoteImageURL(for card: CardRow, set: SetRow) -> URL? {
        URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
    }
}

struct HoldingCardView: View {
    let item: HoldingRow
    let price: Double?
    let graded: GradedRow?
    let gradedPrice: Double?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            CachedAsyncImage(url: imageURL, cornerRadius: 16)
                .frame(height: 210)
            Text(item.card.name)
                .font(.headline)
                .foregroundColor(.white)
                .lineLimit(1)
            Text("\(item.set.name) • \(item.card.rarity ?? "Unknown rarity")")
                .font(.caption)
                .foregroundColor(.white.opacity(0.6))
            HStack {
                Text(priceText)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.orange)
                Spacer()
                Text(item.condition)
                    .font(.caption2)
                    .foregroundColor(.white.opacity(0.5))
            }
            if let graded {
                HStack {
                    Text("\(graded.grader) \(graded.grade)")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                    Spacer()
                    Text(gradedPriceText)
                        .font(.caption)
                        .foregroundColor(.orange.opacity(0.8))
                }
            }
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 20).fill(Color.white.opacity(0.05)))
    }

    private var imageURL: URL? {
        URL(string: "https://images.pokemontcg.io/\(item.set.code)/\(item.card.number).png")
    }

    private var priceText: String {
        guard let price else { return "—" }
        return String(format: "$%.2f", price)
    }

    private var gradedPriceText: String {
        guard let gradedPrice else { return "—" }
        return String(format: "$%.2f", gradedPrice)
    }
}

struct DetailLoadingView: View {
    let isLoading: Bool

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 16) {
                if isLoading {
                    ProgressView()
                        .tint(.orange)
                }
                Text(isLoading ? "Loading card details..." : "Unable to load card details.")
                    .foregroundColor(.white.opacity(0.7))
            }
        }
    }
}

enum HoldingSheet: Identifiable {
    case edit
    case graded

    var id: String {
        switch self {
        case .edit:
            return "edit"
        case .graded:
            return "graded"
        }
    }
}
