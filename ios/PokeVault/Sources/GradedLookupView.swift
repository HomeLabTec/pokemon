import SwiftUI

struct GradedLookupView: View {
    @Binding var grader: String
    @Binding var grade: String
    let onFetch: () -> Void
    let onCancel: () -> Void

    private let graders = ["PSA", "BGS", "CGC", "TAG", "ACE"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Grader") {
                    Picker("Grader", selection: $grader) {
                        ForEach(graders, id: \.self) { value in
                            Text(value).tag(value)
                        }
                    }
                }
                Section("Grade") {
                    TextField("Grade", text: $grade)
                        .keyboardType(.decimalPad)
                }
            }
            .navigationTitle("Get graded value")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { onCancel() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fetch") { onFetch() }
                }
            }
        }
    }
}
