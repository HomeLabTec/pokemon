import SwiftUI

struct CatalogView: View {
    @StateObject private var viewModel = CatalogViewModel()
    @State private var selectedCard: CardRow?
    @State private var selectedSet: SetRow?
    @State private var detail: CardDetailResponse?
    @State private var showDetail = false
    @State private var activeSheet: CatalogSheet?
    @State private var quantity = 1
    @State private var condition = "NM"
    @State private var isForTrade = false
    @State private var isWantlist = false
    @State private var isWatched = false

    private let columns = [GridItem(.adaptive(minimum: 160), spacing: 16)]
    @State private var showFilters = false

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VStack(spacing: 16) {
                header
                filters
                if viewModel.isLoading {
                    ProgressView().tint(.orange)
                }
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 16) {
                        ForEach(viewModel.cards) { card in
                            CatalogCardView(
                                card: card,
                                set: viewModel.sets.first(where: { $0.id == card.set_id }),
                                price: viewModel.prices[card.id]?.market
                            )
                            .onTapGesture {
                                Task { await openDetail(card) }
                            }
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    .padding(.horizontal)
                    .animation(.easeInOut(duration: 0.25), value: viewModel.cards)
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.loadSets()
                await viewModel.loadCards()
            }
        }
        .fullScreenCover(isPresented: $showDetail) {
            if let detail, let selectedSet {
                CardDetailView(
                    title: detail.card.name,
                    subtitle: "\(selectedSet.name) • \(detail.card.number) • \(detail.card.rarity ?? "Unknown rarity")",
                    imageURL: detail.images.first(where: { $0.kind == "large" && $0.local_path != nil })?.local_path,
                    fallbackImageURL: remoteImageURL(for: detail.card, set: selectedSet),
                    priceLabel: "NM market history",
                    latestPrice: detail.latest_prices.first?.market,
                    priceHistory: detail.price_history,
                    details: [
                        ("Set", selectedSet.name),
                        ("Series", selectedSet.series ?? ""),
                        ("Number", detail.card.number),
                        ("Rarity", detail.card.rarity ?? ""),
                        ("Supertype", detail.card.supertype ?? ""),
                        ("Subtypes", detail.card.subtypes?.joined(separator: ", ") ?? ""),
                        ("Types", detail.card.types?.joined(separator: ", ") ?? ""),
                        ("HP", detail.card.hp ?? ""),
                        ("Artist", detail.card.artist ?? ""),
                    ],
                    primaryActionTitle: "Add to holdings",
                    primaryAction: { presentAddHolding() },
                    secondaryActionTitle: nil,
                    secondaryAction: nil,
                    destructiveActionTitle: nil,
                    destructiveAction: nil
                )
            }
        }
        .sheet(item: $activeSheet) { sheet in
            switch sheet {
            case .add:
                HoldingFormView(
                    title: "Add to holdings",
                    cardName: selectedCard?.name,
                    cardImageURL: selectedCard.flatMap { card in
                        guard let set = viewModel.sets.first(where: { $0.id == card.set_id }) else { return nil }
                        return URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
                    },
                    quantity: $quantity,
                    condition: $condition,
                    isForTrade: $isForTrade,
                    isWantlist: $isWantlist,
                    isWatched: $isWatched,
                    onSave: { Task { await saveHolding() } },
                    onCancel: { activeSheet = nil }
                )
            case .filters:
                NavigationStack {
                    Form {
                        Section("Advanced filters") {
                            TextField("Rarity", text: $viewModel.rarity)
                            TextField("Artist", text: $viewModel.artist)
                        }
                    }
                    .navigationTitle("Filters")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") { activeSheet = nil }
                        }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Apply") {
                                Task { await viewModel.loadCards() }
                                activeSheet = nil
                            }
                        }
                    }
                }
            }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Catalog")
                    .font(.title2.bold())
                Text("Explore every set and variant")
                    .foregroundColor(.white.opacity(0.6))
                    .font(.footnote)
            }
            Spacer()
            Button {
                activeSheet = .filters
            } label: {
                Image(systemName: "slider.horizontal.3")
                    .font(.title3)
                    .foregroundColor(.orange)
            }
        }
        .padding(.horizontal)
        .foregroundColor(.white)
    }

    private var filters: some View {
        VStack(spacing: 12) {
            Picker("Set", selection: $viewModel.selectedSetId) {
                ForEach(viewModel.sets, id: \.id) { set in
                    Text(set.name).tag(Optional(set.id))
                }
            }
            .pickerStyle(.menu)
            .tint(.orange)
            .onChange(of: viewModel.selectedSetId) { _ in
                Task { await viewModel.loadCards() }
            }

            TextField("Search cards", text: $viewModel.search)
                .textInputAutocapitalization(.never)
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 14).fill(Color.white.opacity(0.08)))
                .foregroundColor(.white)
                .onChange(of: viewModel.search) { _ in
                    Task { await viewModel.loadCards() }
                }
        }
        .padding(.horizontal)
    }

    private func openDetail(_ card: CardRow) async {
        guard let set = viewModel.sets.first(where: { $0.id == card.set_id }) else { return }
        selectedSet = set
        do {
            let detail: CardDetailResponse = try await APIClient.shared.request("cards/\(card.id)")
            self.detail = detail
            self.selectedCard = card
            print("[iOS] catalog price_history sample:", detail.price_history.prefix(5))
            showDetail = true
        } catch {
            // ignore
        }
    }

    private func presentAddHolding() {
        quantity = 1
        condition = "NM"
        isForTrade = false
        isWantlist = false
        isWatched = false
        showDetail = false
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            activeSheet = .add
        }
    }

    private func saveHolding() async {
        guard let selectedCard else { return }
        let payload = HoldingCreatePayload(
            card_id: selectedCard.id,
            quantity: quantity,
            condition: condition,
            is_for_trade: isForTrade,
            is_wantlist: isWantlist,
            is_watched: isWatched,
            notes: nil
        )
        do {
            let body = try JSONEncoder().encode(payload)
            _ = try await APIClient.shared.request("holdings", method: "POST", body: body) as HoldingRow
            activeSheet = nil
        } catch {
            activeSheet = nil
        }
    }

    private func remoteImageURL(for card: CardRow, set: SetRow) -> URL? {
        URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
    }
}

struct CatalogCardView: View {
    let card: CardRow
    let set: SetRow?
    let price: Double?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            CachedAsyncImage(url: imageURL, cornerRadius: 16)
                .frame(height: 210)
            Text(card.name)
                .font(.headline)
                .foregroundColor(.white)
                .lineLimit(1)
            Text("\(set?.name ?? "Unknown set") • \(card.rarity ?? "Unknown rarity")")
                .font(.caption)
                .foregroundColor(.white.opacity(0.6))
            HStack {
                Text(priceText)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.orange)
                Spacer()
                Text("NM")
                    .font(.caption2)
                    .foregroundColor(.white.opacity(0.5))
            }
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 20).fill(Color.white.opacity(0.05)))
    }

    private var imageURL: URL? {
        guard let set else { return nil }
        return URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
    }

    private var priceText: String {
        guard let price else { return "—" }
        return String(format: "$%.2f", price)
    }
}

enum CatalogSheet: Identifiable {
    case add
    case filters

    var id: String {
        switch self {
        case .add:
            return "add"
        case .filters:
            return "filters"
        }
    }
}
