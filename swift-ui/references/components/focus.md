# Focus handling and field chaining

## Intent

Use `@FocusState` to control keyboard focus, chain fields, and coordinate focus across forms.

## Core patterns

- Represent focusable fields with an enum (`Hashable`), stored in `@FocusState private var`.
- Set initial focus in `onAppear` (on iOS, `defaultFocus` does not reliably raise the keyboard).
- Move to the next field with `.onSubmit`, and set `.submitLabel(.next)` / `.submitLabel(.done)` so the return key says what it does.
- For a dynamic list of fields, key focus by the element's stable identifier, never by index.

## Example: chained fields

```swift
struct EditTagView: View {
    private enum Field: Hashable {
        case title, symbol
    }

    @Binding var tag: Tag
    @FocusState private var focusedField: Field?

    var body: some View {
        Form {
            TextField("Title", text: $tag.title)
                .focused($focusedField, equals: .title)
                .submitLabel(.next)
                .onSubmit { focusedField = .symbol }

            TextField("Symbol", text: $tag.symbol)
                .focused($focusedField, equals: .symbol)
                .submitLabel(.done)
                .onSubmit { focusedField = nil }
        }
        .onAppear { focusedField = .title }
    }
}
```

## Example: dynamic fields

```swift
struct PollOption: Identifiable {
    let id = UUID()
    var text = ""
}

struct PollEditor: View {
    @State private var options = [PollOption(), PollOption()]
    @FocusState private var focusedOption: PollOption.ID?

    var body: some View {
        Form {
            ForEach($options) { $option in
                TextField("Option", text: $option.text)
                    .focused($focusedOption, equals: option.id)
                    .submitLabel(.next)
                    .onSubmit { addOption(after: option.id) }
            }
        }
        .onAppear { focusedOption = options.first?.id }
    }

    private func addOption(after id: PollOption.ID) {
        let newOption = PollOption()
        options.append(newOption)
        // Let the new field enter the hierarchy before focusing it.
        Task {
            await Task.yield()
            focusedOption = newOption.id
        }
    }
}
```

Each option's identity is created once when it is stored (`let id = UUID()`), not during `body` (see `data.md`).

## Design choices to keep

- Keep focus state local to the view that owns the fields.
- Pair forms and scroll views with `.scrollDismissesKeyboard(.interactively)` or `.immediately`.
- Use focus changes to drive helper UI such as validation messages.

## Pitfalls

- Don't store focus state in shared objects; it is view-local.
- Never use `DispatchQueue.main.asyncAfter` to delay focus; use a `Task`.
- Avoid aggressive focus changes during animations.
