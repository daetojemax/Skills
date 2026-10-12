# Input toolbar (bottom anchored)

## Intent

Use a bottom-anchored input bar for chat, composer, or quick actions without fighting the keyboard.

## Core patterns

- On iOS 26+, attach the bar with `.safeAreaBar(edge: .bottom)`: it reserves space and applies the system scroll edge effect under it. Below iOS 26, use `.safeAreaInset(edge: .bottom)`.
- Keep the main content in a `ScrollView` or `List`.
- Drive focus with `@FocusState` and set initial focus when needed.
- Avoid embedding the input bar inside the scroll content; keep it separate.

## Example: scroll view + bottom input

```swift
struct ConversationView: View {
  let messages: [Message]
  @State private var draft = ""
  @FocusState private var isInputFocused: Bool

  var body: some View {
    ScrollView {
      LazyVStack {
        ForEach(messages) { message in
          MessageRow(message: message)
        }
      }
      .padding(.horizontal)
    }
    .defaultScrollAnchor(.bottom)
    .safeAreaBar(edge: .bottom) {   // iOS 26+; use .safeAreaInset(edge: .bottom) below iOS 26
      InputBar(text: $draft)
        .focused($isInputFocused)
    }
    .scrollDismissesKeyboard(.interactively)
    .onAppear { isInputFocused = true }
  }
}
```

## Design choices to keep

- Keep the input bar visually separated from the scrollable content.
- Use `.scrollDismissesKeyboard(.interactively)` for chat-like screens.
- Ensure send actions are reachable via keyboard return or a clear button.

## Pitfalls

- Avoid placing the input view inside the scroll stack; it will jump with content.
- Avoid nested scroll views that fight for drag gestures.
