import Foundation

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let client = APIClient.shared

    struct LoginResponse: Codable {
        let access_token: String
    }

    func login() async {
        isLoading = true
        errorMessage = nil
        do {
            let body = try JSONEncoder().encode(["email": email, "password": password])
            let response: LoginResponse = try await client.request("auth/login", method: "POST", body: body)
            client.token = response.access_token
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func logout() {
        client.token = nil
    }
}
