import Foundation

enum AppConfig {
    static let apiBaseURL = URL(string: "https://poke.taconetwork.net/api")!
    static let appName = "PokeVault"
    static let cardIdServerURLDefault = URL(string: "http://172.22.22.51:8099")!

    static var cardIdServerURL: URL {
        if let raw = UserDefaults.standard.string(forKey: "cardIdServerUrl"),
           let url = URL(string: raw.trimmingCharacters(in: .whitespacesAndNewlines)),
           !raw.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return url
        }
        return cardIdServerURLDefault
    }
}
