import SwiftUI

struct MainTabView: View {
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
        .tint(.orange)
    }
}
