import SwiftUI

struct SettingsView: View {
    @ObservedObject private var client = APIClient.shared

    var body: some View {
        VStack(spacing: 24) {
            Text("Account")
                .font(.title2.bold())
            Text("Signed in to \(AppConfig.appName).")
                .foregroundColor(.white.opacity(0.6))
            Button {
                client.token = nil
            } label: {
                Text("Log out")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(RoundedRectangle(cornerRadius: 16).stroke(Color.orange))
            }
            Spacer()
        }
        .padding()
        .foregroundColor(.white)
        .background(Color.black.ignoresSafeArea())
    }
}
