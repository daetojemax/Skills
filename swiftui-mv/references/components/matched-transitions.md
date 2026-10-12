# Matched transitions

## Intent

Use matched transitions to create smooth continuity between a source view (thumbnail, avatar) and a destination view (sheet, detail, viewer).

## Core patterns

- Use a shared `Namespace` and a stable ID for the source.
- Use `matchedTransitionSource` + `navigationTransition(.zoom(...))` (iOS 18+) for zooming into a pushed view, sheet, or full-screen cover.
- Use `matchedGeometryEffect` for in-place transitions within a view hierarchy.
- Keep IDs stable across view updates (avoid random UUIDs).

## Example: media preview to full-screen viewer (iOS 18+)

```swift
struct MediaPreview: View {
  @Namespace private var namespace
  @State private var selected: MediaAttachment?

  let attachment: MediaAttachment

  var body: some View {
    Button {
      selected = attachment
    } label: {
      ThumbnailView(attachment: attachment)
    }
    .matchedTransitionSource(id: attachment.id, in: namespace)
    .fullScreenCover(item: $selected) { item in
      MediaViewer(item: item)
        .navigationTransition(.zoom(sourceID: item.id, in: namespace))
    }
  }
}
```

## Example: matched geometry within a view

```swift
struct ToggleBadge: View {
  @Namespace private var space
  @State private var isOn = false

  var body: some View {
    Button {
      withAnimation(.spring) { isOn.toggle() }
    } label: {
      Image(systemName: isOn ? "eye" : "eye.slash")
        .matchedGeometryEffect(id: "icon", in: space)
    }
  }
}
```

## Design choices to keep

- Prefer `matchedTransitionSource` for cross-screen transitions.
- Keep source and destination sizes reasonable to avoid jarring scale changes.
- Use `withAnimation` for state-driven transitions.

## Pitfalls

- Don’t use unstable IDs; it breaks the transition. The source ID is the source item's own stable ID, never derived from the current selection.
- Avoid mismatched shapes (e.g., square to circle) unless the design expects it.
