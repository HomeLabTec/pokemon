import SwiftUI
import UIKit

enum CardScanStep {
    case idle
    case identifying
    case multipleMatches
    case confirm
    case notFound
    case success
}

@MainActor
final class CardScanViewModel: ObservableObject {
    @Published var image: UIImage?
    @Published var isIdentifying = false
    @Published var step: CardScanStep = .idle
    @Published var ocrName: String = ""
    @Published var ocrNumber: String = ""
    @Published var matches: [CardRow] = []
    @Published var manualQuery: String = ""
    @Published var manualResults: [CardRow] = []
    @Published var selectedCard: CardRow?
    @Published var matchedImageURL: URL?
    @Published var errorMessage: String?
    @Published var sets: [SetRow] = []
    @Published var isSearching = false
    @Published var rawOCR: String = ""

    private let client = APIClient.shared

    func loadSets() async {
        do {
            let result: [SetRow] = try await client.request("sets")
            sets = result
        } catch {
            // ignore
        }
    }

    func identify(image: UIImage) async {
        isIdentifying = true
        step = .identifying
        errorMessage = nil
        matches = []
        manualResults = []
        selectedCard = nil
        matchedImageURL = nil
        rawOCR = ""

        let resized = image.resized(maxDimension: 1800)
        guard let data = resized.jpegData(compressionQuality: 0.9) else {
            isIdentifying = false
            step = .idle
            errorMessage = "Unable to read image data."
            return
        }

        do {
            let result = try await CardIdentifierClient.shared.identify(imageData: data)
            ocrName = result.name?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            ocrNumber = result.number?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            rawOCR = result.rawResponse
            manualQuery = ocrName
            if ocrName.isEmpty || ocrNumber.isEmpty {
                step = .notFound
                isIdentifying = false
                return
            }
            await resolveMatches(name: ocrName, number: ocrNumber)
        } catch CardIdentifyError.unprocessable {
            errorMessage = "Couldn’t detect/identify card. Try again with better lighting and include the full card in frame."
            step = .idle
        } catch CardIdentifyError.invalidResponse {
            errorMessage = "Couldn’t detect/identify card. Please try again."
            step = .idle
        } catch CardIdentifyError.serverError {
            errorMessage = "AI server unreachable. Check your connection and try again."
            step = .idle
        } catch {
            errorMessage = "AI server unreachable. Check your connection and try again."
            step = .idle
        }
        isIdentifying = false
    }

    func resolveMatches(name: String, number: String) async {
        isSearching = true
        defer { isSearching = false }
        do {
            let query = name.trimmingCharacters(in: .whitespacesAndNewlines)
            var components = URLComponents()
            components.path = "/cards/search"
            components.queryItems = [URLQueryItem(name: "q", value: query)]
            let queryString = components.percentEncodedQuery ?? ""
            let path = queryString.isEmpty ? "cards/search" : "cards/search?\(queryString)"
            let result: [CardRow] = try await client.request(path)
            let normalizedName = normalizeName(name)
            let normalizedNumber = normalizeNumber(number)
            let strictMatches = result.filter {
                normalizeName($0.name) == normalizedName && normalizeNumber($0.number) == normalizedNumber
            }
            if !strictMatches.isEmpty {
                if strictMatches.count == 1 {
                    if let card = strictMatches.first {
                        selectedCard = card
                        await loadMatchedImage(for: card)
                    }
                    step = .confirm
                } else {
                    matches = strictMatches
                    matchedImageURL = nil
                    step = .multipleMatches
                }
                return
            }

            let nameMatches = result.filter { normalizeName($0.name) == normalizedName }
            if !nameMatches.isEmpty {
                matches = nameMatches
                matchedImageURL = nil
                step = .multipleMatches
            } else {
                step = .notFound
                matches = []
                selectedCard = nil
                matchedImageURL = nil
            }
        } catch {
            errorMessage = "Unable to search your catalog."
            step = .notFound
        }
    }

    func manualSearch() async {
        let query = manualQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return }
        isSearching = true
        defer { isSearching = false }
        do {
            var components = URLComponents()
            components.path = "/cards/search"
            components.queryItems = [URLQueryItem(name: "q", value: query)]
            let queryString = components.percentEncodedQuery ?? ""
            let path = queryString.isEmpty ? "cards/search" : "cards/search?\(queryString)"
            let result: [CardRow] = try await client.request(path)
            manualResults = result
        } catch {
            errorMessage = "Unable to search your catalog."
        }
    }

    func selectCard(_ card: CardRow) {
        selectedCard = card
        step = .confirm
        Task { await loadMatchedImage(for: card) }
    }

    func reset() {
        image = nil
        isIdentifying = false
        step = .idle
        ocrName = ""
        ocrNumber = ""
        matches = []
        manualQuery = ""
        manualResults = []
        selectedCard = nil
        matchedImageURL = nil
        errorMessage = nil
        rawOCR = ""
    }

    func setForCard(_ card: CardRow) -> SetRow? {
        sets.first { $0.id == card.set_id }
    }

    private func loadMatchedImage(for card: CardRow) async {
        if setForCard(card) == nil {
            do {
                let result: [SetRow] = try await client.request("sets")
                sets = result
            } catch {
                // ignore
            }
        }
        if let set = setForCard(card) {
            matchedImageURL = URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
            return
        }
        matchedImageURL = nil
    }

    private func normalizeNumber(_ value: String) -> String {
        value.replacingOccurrences(of: " ", with: "").lowercased()
    }

    private func normalizeName(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }
}

struct CardScanView: View {
    @Environment(\.dismiss) private var dismiss
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"
    @StateObject private var viewModel = CardScanViewModel()
    @State private var showImagePicker = false
    @State private var pickerSource: UIImagePickerController.SourceType = .photoLibrary
    @State private var showHoldingSheet = false
    @State private var didAutoOpen = false
    @State private var quantity = 1
    @State private var condition = "NM"
    @State private var isForTrade = false
    @State private var isWantlist = false
    @State private var isWatched = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                ScrollView {
                    VStack(spacing: 20) {
                        header
                        if let image = viewModel.image {
                            Image(uiImage: image)
                                .resizable()
                                .scaledToFit()
                                .frame(maxWidth: 260)
                                .cornerRadius(16)
                                .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.15)))
                        }
                        if let matchedURL = viewModel.matchedImageURL, viewModel.step == .confirm {
                            VStack(spacing: 8) {
                                Text("Matched card")
                                    .foregroundColor(.white.opacity(0.7))
                                    .font(.caption)
                                CachedAsyncImage(url: matchedURL, cornerRadius: 14)
                                    .frame(width: 200, height: 280)
                            }
                        }
                        if viewModel.isIdentifying || viewModel.isSearching {
                            ProgressView()
                                .tint(colorFromHex(accentHex) ?? .orange)
                        }
                        if let message = viewModel.errorMessage {
                            Text(message)
                                .foregroundColor(.red.opacity(0.9))
                                .font(.footnote)
                                .multilineTextAlignment(.center)
                        }
                        content
                    }
                    .padding()
                }
            }
            .safeAreaInset(edge: .bottom) {
                if viewModel.step == .confirm, viewModel.selectedCard != nil {
                    addHoldingButton
                }
            }
            .navigationTitle("Scan Card")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Close") { dismiss() }
                        .foregroundColor(colorFromHex(accentHex) ?? .orange)
                }
            }
        }
        .onAppear {
            Task { await viewModel.loadSets() }
            if !didAutoOpen {
                didAutoOpen = true
                openCamera()
            }
        }
        .sheet(isPresented: $showImagePicker) {
            ImagePicker(sourceType: pickerSource) { image in
                viewModel.image = image
                Task { await viewModel.identify(image: image) }
            }
        }
        .sheet(isPresented: $showHoldingSheet) {
            HoldingFormView(
                title: "Add to holdings",
                cardName: viewModel.selectedCard?.name,
                cardImageURL: selectedCardImageURL,
                quantity: $quantity,
                condition: $condition,
                isForTrade: $isForTrade,
                isWantlist: $isWantlist,
                isWatched: $isWatched,
                onSave: { Task { await addHolding() } },
                onCancel: { showHoldingSheet = false }
            )
        }
    }

    private var header: some View {
        VStack(spacing: 8) {
            Text("Identify a Pokémon card from a photo.")
                .foregroundColor(.white.opacity(0.7))
                .font(.footnote)
                .multilineTextAlignment(.center)
            Text("Server: \(AppConfig.cardIdServerURL.absoluteString)")
                .foregroundColor(.white.opacity(0.4))
                .font(.caption2)
                .multilineTextAlignment(.center)
        }
    }

    @ViewBuilder
    private var content: some View {
        switch viewModel.step {
        case .idle:
            idleControls
        case .identifying:
            Text("Identifying card…")
                .foregroundColor(.white.opacity(0.7))
        case .multipleMatches:
            matchesList(title: "Multiple matches found", cards: viewModel.matches)
        case .confirm:
            confirmationView
        case .notFound:
            notFoundView
        case .success:
            successView
        }
    }

    private var idleControls: some View {
        VStack(spacing: 12) {
            Button {
                openCamera()
            } label: {
                Label("Scan a card", systemImage: "camera.viewfinder")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(RoundedRectangle(cornerRadius: 16).fill(colorFromHex(accentHex) ?? .orange))
                    .foregroundColor(.black)
            }
            Button("Choose from library") {
                openLibrary()
            }
            .foregroundColor(.white.opacity(0.8))
            if viewModel.image != nil {
                Button("Pick a different photo") {
                    openLibrary()
                }
                .foregroundColor(.white.opacity(0.8))
            }
        }
    }

    private func matchesList(title: String, cards: [CardRow]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .foregroundColor(.white)
                .font(.headline)
            ForEach(cards, id: \.id) { card in
                Button {
                    viewModel.selectCard(card)
                } label: {
                    HStack(spacing: 12) {
                        CachedAsyncImage(url: imageURL(for: card), cornerRadius: 10)
                            .frame(width: 52, height: 72)
                        VStack(alignment: .leading, spacing: 4) {
                            Text(card.name)
                                .foregroundColor(.white)
                                .font(.subheadline.weight(.semibold))
                            Text("\(setName(for: card)) • \(card.number)")
                                .foregroundColor(.white.opacity(0.6))
                                .font(.caption)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.white.opacity(0.4))
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 14).fill(Color.white.opacity(0.06)))
                }
            }
        }
    }

    private var confirmationView: some View {
        VStack(spacing: 16) {
            if let selectedCard = viewModel.selectedCard {
                Text("Confirm match")
                    .foregroundColor(.white)
                    .font(.headline)
                CachedAsyncImage(url: viewModel.matchedImageURL ?? imageURL(for: selectedCard), cornerRadius: 14)
                    .frame(width: 200, height: 280)
                Text(selectedCard.name)
                    .foregroundColor(.white)
                    .font(.title3.bold())
                Text("\(setName(for: selectedCard)) • \(selectedCard.number)")
                    .foregroundColor(.white.opacity(0.6))
                    .font(.footnote)
                Button {
                    prepareHoldingDefaults()
                    showHoldingSheet = true
                } label: {
                    Text("Add to holdings")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(RoundedRectangle(cornerRadius: 16).fill(colorFromHex(accentHex) ?? .orange))
                        .foregroundColor(.black)
                }
                Button("Scan another") {
                    viewModel.reset()
                    openCamera()
                }
                .foregroundColor(.white.opacity(0.8))
            }
        }
        .frame(maxWidth: .infinity)
    }

    private var addHoldingButton: some View {
        Button {
            prepareHoldingDefaults()
            showHoldingSheet = true
        } label: {
            Text("Add to holdings")
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(RoundedRectangle(cornerRadius: 16).fill(colorFromHex(accentHex) ?? .orange))
                .foregroundColor(.black)
        }
        .padding(.horizontal)
        .padding(.bottom, 12)
        .background(Color.black.opacity(0.6))
    }

    private var notFoundView: some View {
        VStack(spacing: 16) {
            Text("Card not found")
                .foregroundColor(.white)
                .font(.headline)
            if !viewModel.ocrName.isEmpty || !viewModel.ocrNumber.isEmpty {
                Text("OCR result: \(viewModel.ocrName) \(viewModel.ocrNumber)")
                    .foregroundColor(.white.opacity(0.7))
                    .font(.footnote)
            }
            VStack(alignment: .leading, spacing: 8) {
                Text("Search manually")
                    .foregroundColor(.white)
                    .font(.subheadline.weight(.semibold))
                TextField("Search by name", text: $viewModel.manualQuery)
                    .padding(12)
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.white.opacity(0.08)))
                    .foregroundColor(.white)
                Button("Search") {
                    Task { await viewModel.manualSearch() }
                }
                .foregroundColor(colorFromHex(accentHex) ?? .orange)
            }
            if !viewModel.manualResults.isEmpty {
                matchesList(title: "Results", cards: viewModel.manualResults)
            }
            Button("Try again") {
                viewModel.reset()
                openCamera()
            }
            .foregroundColor(.white.opacity(0.8))
        }
    }

    private var successView: some View {
        VStack(spacing: 16) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 48))
                .foregroundColor(colorFromHex(accentHex) ?? .orange)
            Text("Added to holdings")
                .foregroundColor(.white)
                .font(.headline)
            Button("Scan another") {
                viewModel.reset()
            }
            .foregroundColor(.white.opacity(0.8))
            Button("Done") {
                dismiss()
            }
            .foregroundColor(.white.opacity(0.8))
        }
        .padding(.top, 8)
    }

    private var selectedCardImageURL: URL? {
        guard let card = viewModel.selectedCard else { return nil }
        return imageURL(for: card)
    }

    private func imageURL(for card: CardRow) -> URL? {
        guard let set = viewModel.setForCard(card) else { return nil }
        return URL(string: "https://images.pokemontcg.io/\(set.code)/\(card.number).png")
    }

    private func setName(for card: CardRow) -> String {
        viewModel.setForCard(card)?.name ?? "Unknown set"
    }

    private func prepareHoldingDefaults() {
        quantity = 1
        condition = "NM"
        isForTrade = false
        isWantlist = false
        isWatched = false
    }

    private func addHolding() async {
        guard let card = viewModel.selectedCard else { return }
        let payload = HoldingCreatePayload(
            card_id: card.id,
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
            showHoldingSheet = false
            viewModel.step = .success
        } catch {
            showHoldingSheet = false
            viewModel.errorMessage = "Unable to add holding."
        }
    }

    private func openCamera() {
        if UIImagePickerController.isSourceTypeAvailable(.camera) {
            pickerSource = .camera
        } else {
            pickerSource = .photoLibrary
        }
        showImagePicker = true
    }

    private func openLibrary() {
        pickerSource = .photoLibrary
        showImagePicker = true
    }
}
