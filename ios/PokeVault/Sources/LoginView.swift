import SwiftUI

struct LoginView: View {
    @StateObject private var auth = AuthViewModel()
    @AppStorage("accentHex") private var accentHex: String = "#f59e0b"

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.black, Color(red: 0.08, green: 0.06, blue: 0.04)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 24) {
                VStack(spacing: 8) {
                    Text(AppConfig.appName)
                        .font(.system(size: 32, weight: .semibold))
                        .foregroundColor(.white)
                    Text("Your collection, beautifully organized.")
                        .foregroundColor(.white.opacity(0.6))
                }

                VStack(spacing: 16) {
                    TextField("Email", text: $auth.email)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.08)))

                    SecureField("Password", text: $auth.password)
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 16).fill(Color.white.opacity(0.08)))
                }
                .foregroundColor(.white)
                .frame(maxWidth: 320)

                if let errorMessage = auth.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red.opacity(0.8))
                        .font(.footnote)
                }

                Button {
                    Task { await auth.login() }
                } label: {
                    HStack {
                        if auth.isLoading {
                            ProgressView()
                        }
                        Text(auth.isLoading ? "Signing in..." : "Sign In")
                    }
                    .frame(maxWidth: 320)
                    .padding(.vertical, 12)
                    .background(RoundedRectangle(cornerRadius: 18).fill(Color(hex: accentHex) ?? .orange))
                    .foregroundColor(.black)
                }
                .disabled(auth.isLoading)

                Spacer()
            }
            .padding()
        }
    }
}
