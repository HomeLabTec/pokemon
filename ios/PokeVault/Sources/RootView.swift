import SwiftUI

struct RootView: View {
    @ObservedObject private var client = APIClient.shared

    var body: some View {
        if client.token == nil {
            LoginView()
        } else {
            MainTabView()
        }
    }
}
