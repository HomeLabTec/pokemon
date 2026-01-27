import SwiftUI

struct HoldingFormView: View {
    let title: String
    @Binding var quantity: Int
    @Binding var condition: String
    @Binding var isForTrade: Bool
    @Binding var isWantlist: Bool
    @Binding var isWatched: Bool
    let onSave: () -> Void
    let onCancel: () -> Void

    private let conditions = ["NM", "LP", "MP", "HP", "Damaged"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Condition") {
                    Picker("Condition", selection: $condition) {
                        ForEach(conditions, id: \.self) { value in
                            Text(value).tag(value)
                        }
                    }
                }
                Section("Quantity") {
                    Stepper(value: $quantity, in: 1...99) {
                        Text("\(quantity)")
                    }
                }
                Section("Flags") {
                    Toggle("For trade", isOn: $isForTrade)
                    Toggle("Wantlist", isOn: $isWantlist)
                    Toggle("Watched", isOn: $isWatched)
                }
            }
            .navigationTitle(title)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { onCancel() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { onSave() }
                }
            }
        }
    }
}
