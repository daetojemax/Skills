# ScrollView and Lazy stacks

## Intent

Use `ScrollView` with `LazyVStack`, `LazyHStack`, or `LazyVGrid` when you need custom layout, mixed content, or horizontal/ grid-based scrolling.

## Core patterns

- Prefer `ScrollView` + `LazyVStack` for chat-like or custom feed layouts.
- Use `ScrollView(.horizontal)` + `LazyHStack` for chips, tags, avatars, and media strips.
- Use `LazyVGrid` for icon/media grids; prefer adaptive columns when possible.
- Use `.defaultScrollAnchor(.bottom)` (iOS 17) to start chat-like content at the bottom.
- For programmatic jumps, prefer `scrollPosition(id:)` (iOS 17) or `ScrollPosition` with `scrollPosition(_:)` (iOS 18); `ScrollViewReader` still works but needs the proxy inside its closure.
- Hide indicators with `.scrollIndicators(.hidden)`, not `showsIndicators: false`.
- Use `safeAreaBar(edge:)` (iOS 26+) or `safeAreaInset(edge:)` for bars that should stick above the keyboard (see `input-toolbar.md`).

## Example: vertical custom feed

```swift
struct ConversationView: View {
  let messages: [Message]

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
    .safeAreaInset(edge: .bottom) {
      MessageInputBar()
    }
  }
}
```

## Example: horizontal chips

```swift
ScrollView(.horizontal) {
  LazyHStack(spacing: 8) {
    ForEach(chips) { chip in
      ChipView(chip: chip)
    }
  }
}
.scrollIndicators(.hidden)
```

## Example: adaptive grid

```swift
let columns = [GridItem(.adaptive(minimum: 120))]

ScrollView {
  LazyVGrid(columns: columns, spacing: 8) {
    ForEach(items) { item in
      GridItemView(item: item)
    }
  }
  .padding(8)
}
```

## Design choices to keep

- Use `Lazy*` stacks when item counts are large or unknown.
- Use non-lazy stacks for small, fixed-size content to avoid lazy overhead.
- Keep IDs stable when scrolling to an ID.
- Prefer explicit animations (`withAnimation`) when scrolling to an ID.

## Pitfalls

- Avoid nesting scroll views of the same axis; it causes gesture conflicts.
- Don’t combine `List` and `ScrollView` in the same hierarchy without a clear reason.
- Overuse of `LazyVStack` for tiny content can add unnecessary complexity.
