import Foundation

enum AppConfig {
    static let apiBaseURL = URL(string: "https://poke.taconetwork.net/api")!
    static let appName = "PokeVault"
    static let cardIdServerURLDefault = URL(string: "https://pokescan.taconetwork.net")!
    private static let legacyCardIdServerURL = "http://172.22.22.51:8099"

    static var cardIdServerURL: URL {
        if let raw = UserDefaults.standard.string(forKey: "cardIdServerUrl"),
           let url = URL(string: raw.trimmingCharacters(in: .whitespacesAndNewlines)),
           !raw.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return url
        }
        return cardIdServerURLDefault
    }

    static func migrateCardIdServerURLIfNeeded() {
        let key = "cardIdServerUrl"
        if let current = UserDefaults.standard.string(forKey: key) {
            let trimmed = current.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed == legacyCardIdServerURL || trimmed.isEmpty {
                UserDefaults.standard.set(cardIdServerURLDefault.absoluteString, forKey: key)
            }
        } else {
            UserDefaults.standard.set(cardIdServerURLDefault.absoluteString, forKey: key)
        }
    }
}
