# Scroll-reveal detail surfaces

Requires iOS 18+ (`onScrollGeometryChange`, `onScrollTargetVisibilityChange`). On an iOS 17 target, gate the screen or use a simpler sheet-based detail.

## Intent

A detail screen with a primary surface first and secondary content behind it, revealed by scrolling or swiping rather than a separate button. Typical fits: media detail screens that reveal actions or metadata, maps or cards that transition into structured detail, full-screen viewers with a second "actions" page.

## Core pattern

Build the interaction as a paged vertical `ScrollView` with two sections – a primary section sized to the viewport, then a secondary section. Derive one normalized `progress` value from the scroll offset and drive every visual change from it. Do not build a separate gesture system unless scrolling alone cannot express the interaction.

```swift
struct DetailSurface: View {
    @State private var revealProgress = 0.0
    @State private var secondaryHeight = 1.0
    @State private var scrollPosition = ScrollPosition(idType: DetailSection.self)

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                PrimaryContent(progress: revealProgress)
                    .containerRelativeFrame(.vertical)
                    .id(DetailSection.primary)

                SecondaryContent(progress: revealProgress)
                    .id(DetailSection.secondary)
                    .onGeometryChange(for: Double.self) { proxy in
                        proxy.size.height
                    } action: { newHeight in
                        secondaryHeight = max(newHeight, 1)
                    }
            }
            .scrollTargetLayout()
        }
        .scrollIndicators(.hidden)
        .scrollTargetBehavior(.paging)
        .scrollPosition($scrollPosition)
        .onScrollGeometryChange(for: Double.self) { geometry in
            geometry.contentOffset.y + geometry.contentInsets.top
        } action: { _, offset in
            revealProgress = min(max(offset / secondaryHeight, 0), 1)
        }
        .safeAreaInset(edge: .bottom) {
            RevealToggle(progress: revealProgress, action: toggleReveal)
        }
    }

    private func toggleReveal() {
        withAnimation(.smooth) {
            scrollPosition.scrollTo(id: revealProgress < 0.5 ? DetailSection.secondary : .primary, anchor: .top)
        }
    }
}

private enum DetailSection: Hashable {
    case primary, secondary
}
```

`containerRelativeFrame(.vertical)` sizes the primary section to the scroll view's viewport without a `GeometryReader`.

## Design choices to keep

- Make the primary section exactly viewport-sized when the interaction should feel like paging between states.
- Compute `progress` from the real scroll offset, not from duplicated Booleans such as `isExpanded`, `isShowingSecondary`, and `isSnapped`.
- Drive `offset`, `opacity`, `blur`, `scaleEffect`, and toolbar state from `progress` so the whole surface stays synchronized. Prefer `visualEffect()` / `scrollTransition()` for purely visual changes – they avoid re-evaluating `body` (see `performance.md`).
- Use `onScrollTargetVisibilityChange` when you need a settled section state for haptics, tooltip dismissal, analytics, or accessibility announcements.

## Morphing a shared control

If a control appears to move from the primary surface into the secondary content, do not render two fully visible copies. Expose a source anchor and a destination anchor with `anchorPreference`, then render one overlay with `overlayPreferenceValue` that interpolates position and size using `progress`. This keeps the motion coherent and avoids duplicate hit targets.

## Interaction guards

- Disable vertical scrolling while a conflicting mode is active (pinch-to-zoom, crop, full-screen media manipulation).
- Disable hit testing on overlays that should disappear once the secondary content is revealed.
- Avoid same-axis nested scroll views unless the inner one is effectively static.

## Pitfalls

- Do not hard-code the progress divisor; measure the secondary section or another real reveal distance.
- Do not mix several animation sources for the same property.
- Beware of layout feedback loops when measuring heights: clamp zero values, and update only when the measured value actually changes.
- Do not let the raw offset fan out into many views; pass `progress` only where it is used.
