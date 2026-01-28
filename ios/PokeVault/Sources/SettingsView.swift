import SwiftUI

struct SettingsView: View {
    @ObservedObject private var client = APIClient.shared
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"
    @AppStorage("cardIdServerUrl") private var cardIdServerUrl: String = AppConfig.cardIdServerURLDefault.absoluteString

    var body: some View {
        VStack(spacing: 24) {
            Text("Account")
                .font(.title2.bold())
            Text("Signed in to \(AppConfig.appName).")
                .foregroundColor(.white.opacity(0.6))

            VStack(alignment: .leading, spacing: 12) {
                Text("Accent color")
                    .font(.subheadline.weight(.semibold))
                ColorPicker(
                    "Pick a color",
                    selection: Binding(
                        get: { colorFromHex(accentHex) ?? .orange },
                        set: { accentHex = $0.toHexString() }
                    )
                )
                .labelsHidden()
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))

            VStack(alignment: .leading, spacing: 12) {
                Text("Card ID server")
                    .font(.subheadline.weight(.semibold))
                TextField("http://172.22.22.51:8099", text: $cardIdServerUrl)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .padding(12)
                    .background(RoundedRectangle(cornerRadius: 14).fill(Color.white.opacity(0.08)))
                    .foregroundColor(.white)
                Text("Used for AI card identification over your LAN.")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.5))
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.06)))

            Button {
                client.token = nil
            } label: {
                Text("Log out")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(RoundedRectangle(cornerRadius: 16).stroke(colorFromHex(accentHex) ?? .orange))
            }
            Spacer()
        }
        .padding()
        .foregroundColor(.white)
        .background(Color.black.ignoresSafeArea())
    }
}
