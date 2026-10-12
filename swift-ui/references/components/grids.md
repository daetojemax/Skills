# Grids

## Intent

Use `LazyVGrid` / `LazyHGrid` for icon pickers, media galleries, and dense visual selections where items align in columns.

## Core patterns

- Use `.adaptive` columns for layouts that should scale across window sizes – this is usually the right default, because the window can change size at any time (see `resizability.md`).
- Use several `.flexible` columns when you genuinely need a fixed column count.
- Keep spacing consistent and small to avoid uneven gutters.
- For square cells, use an aspect-ratio container rather than `GeometryReader`.
- Make each cell a `Button`, not an `onTapGesture`.

## Example: adaptive icon grid

```swift
let columns = [GridItem(.adaptive(minimum: 120))]

LazyVGrid(columns: columns, spacing: 8) {
    ForEach(icons) { icon in
        Button {
            select(icon)
        } label: {
            Image(icon.previewName)
                .resizable()
                .scaledToFit()
                .clipShape(.rect(cornerRadius: 8))
                .overlay(alignment: .bottomTrailing) {
                    if icon.isSelected {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundStyle(.green)
                            .padding(4)
                    }
                }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(icon.name)
        .accessibilityAddTraits(icon.isSelected ? .isSelected : [])
    }
}
```

## Example: square thumbnails without GeometryReader

```swift
LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: 3), spacing: 4) {
    ForEach(items) { item in
        Color.clear
            .aspectRatio(1, contentMode: .fit)
            .overlay {
                ThumbnailView(item: item)
                    .scaledToFill()
            }
            .clipped()
            .contentShape(.rect)
    }
}
```

The clear square defines the cell's size; the overlay fills it and `clipped()` trims the overflow.

## Design choices to keep

- Use lazy grids for large collections; avoid non-lazy grids for big sets.
- Prefer adaptive grids for pickers and flexible layouts.
- Give every cell the same top-level shape (see `performance.md`, collections).

## Pitfalls

- Avoid heavy overlays or effects in every cell; they multiply quickly.
- Don't nest grids inside other grids without a clear reason.
- Never load full-size images in cells.
