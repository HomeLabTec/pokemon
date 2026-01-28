import SwiftUI

struct MainTabView: View {
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"

    var body: some View {
        TabView {
            NavigationStack {
                DashboardView()
            }
            .tabItem {
                Label("Dashboard", systemImage: "chart.line.uptrend.xyaxis")
            }
            NavigationStack {
                CatalogView()
            }
            .tabItem {
                Label("Catalog", systemImage: "square.grid.2x2")
            }
            NavigationStack {
                HoldingsView()
            }
            .tabItem {
                Label("Holdings", systemImage: "tray.full")
            }
            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Account", systemImage: "person.crop.circle")
            }
        }
        .tint(Color.fromHex(accentHex) ?? .orange)
    }
}
