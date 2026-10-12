# SwiftUI Views

Views are lightweight state expressions and orchestration points. They read like UI: data flow plus layout, not a view controller. For where logic lives instead, see `architecture.md`.


## Member ordering

Order view members top to bottom like this, unless the file has a stronger local convention to preserve:

1. `@Environment` properties
2. `let` properties (inputs)
3. `@State` / `@Binding` / other stored properties
4. Computed non-view properties
5. `init`
6. `body`
7. Small view helpers (rare – see below)
8. Action methods and async helpers, optionally in a `private extension` with `// MARK: -`


## Extracting subviews

- Strongly prefer dedicated `View` structs over computed properties or methods that return `some View`, even with `@ContentBuilder`. A screen built out of `private var header: some View` fragments is still one big view: every fragment is re-evaluated whenever anything in the parent changes.
- Flag `body` properties longer than roughly one screen, or containing several logical sections. Split them into subviews before considering any other restructuring.
- If the user has created a handful of small, private helper `some View` properties for structural readability, and they both belong to the same concern as `body` and would fit in `body` at an acceptable length if inlined, these can be left alone. Otherwise, extract them into `View` structs.
- Extract a subview whenever a section has its own state, async work, branching, or deserves its own preview.
- Pass small, explicit inputs (values, bindings, actions) into extracted subviews instead of handing down the entire parent state or a whole store.
- Remove a `Group` that merely wraps one view; attach its modifiers to that view directly. For example, `Group { Image(systemName: "leaf") }` adds no visual behavior, but gives the compiler another type to check throughout the modifier chain. Groups containing siblings, a `ForEach`, or conditional branches serve a purpose and should stay, except around branches inside a `List` row, where a `VStack` is needed instead so that the row's shape does not depend on which branch ran.

Prefer:

```swift
var body: some View {
    List {
        HeaderSection(title: title, subtitle: subtitle)
        FilterSection(options: filterOptions, selection: $selectedFilter)
        ResultsSection(items: filteredItems)
    }
}
```

Avoid:

```swift
var body: some View {
    List {
        header
        filters
        results
    }
}

private var header: some View { /* … */ }
private var filters: some View { /* … */ }
private var results: some View { /* … */ }
```


## Files

- A small `private` subview used only by one screen may stay in the same file as that screen, below the main view. This keeps a feature readable as one unit.
- Move a subview into its own file as soon as it is reused elsewhere, grows its own state or logic, or is meaningful on its own (for example, it has its own preview).
- Non-view types – `@Observable` stores, services, clients, models, route enums – always get their own file.
- When a view file exceeds roughly 300 lines, split it: extract sections into dedicated view types first, and use `private` extensions with `// MARK: -` for actions. Extensions are not a substitute for splitting a giant screen.


## Actions and side effects

- Extract button actions into methods rather than writing them inline in `body`. If an action can be passed directly, do so: `Button("Save", systemImage: "checkmark", action: save)` rather than `Button("Save", systemImage: "checkmark") { save() }`.
- Do not bury business logic inside `task()`, `onAppear()`, `onChange()`, or `refreshable()`. Call a small private method, and keep real logic in services or `@Observable` stores (see `architecture.md`).
- Do not start network or other expensive work from `body` or a view initializer.

```swift
Button("Save", action: save)
    .disabled(isSaving)
    .task(id: searchText) {
        await reload(for: searchText)
    }

private func save() {
    Task { await store.save(draft) }
}
```


## Stable view tree

- Avoid `body` or helper views that return completely different root hierarchies via top-level `if`/`else`. Root-level branch swapping causes identity churn, state resets, broader invalidation, and broken animations.
- Prefer one stable base view, with conditions localized inside sections, `overlay`, `toolbar`, or modifier values (see `performance.md`).
- Switching on a loading state (`switch viewState { case .loading: … }`) inside a stable container such as `List` or `ScrollView` is fine; swapping the container itself is not.


## Other view rules

- Unless a full-screen editing experience is required, prefer `TextField` with `axis: .vertical` over `TextEditor`, because it allows placeholder text. If a specific minimum height is required, use something like `lineLimit(5...)`.
- When rendering SwiftUI views to images, strongly prefer `ImageRenderer` over `UIGraphicsImageRenderer`.
- Use `#Preview`, not the legacy `PreviewProvider` protocol. See `components/previews.md`.
- When using `TabView(selection:)`, bind to a property that stores an enum rather than an integer or string: `Tab("Home", systemImage: "house", value: .home)` rather than `Tab("Home", systemImage: "house", value: 0)`.

Examples use the Xcode 27+ name `@ContentBuilder`, which has no minimum iOS; keep `@ViewBuilder` on earlier toolchains and leave existing uses unchanged.


## Animating views

- Strongly prefer the `@Animatable` macro: it supplies `Animatable` conformance and `animatableData` automatically. Mark properties that cannot or should not animate, such as integers and Booleans, with `@AnimatableIgnored`. Write `animatableData` manually only when its setter needs behavior the macro cannot generate, such as range limiting or normalization; use `AnimatableValues` on iOS 26+, or `AnimatablePair` for earlier targets.
- For an animated `ViewModifier`, use `@Animatable` rather than the deprecated `AnimatableModifier` protocol.
- Never use `animation(_ animation: Animation?)`; always provide a value to watch, such as `.animation(.bouncy, value: score)`.
- Chaining animations must be done using a `completion` closure passed to `withAnimation()`, rather than trying to execute multiple `withAnimation()` calls using delays.

For example:

```swift
Button("Animate Me") {
    withAnimation {
        scale = 2
    } completion: {
        withAnimation {
            scale = 1
        }
    }
}
```


## Reordering and swipe actions

The following requires iOS 27+ and is unavailable on tvOS.

- Enable drag reordering with `reorderable()` on the `ForEach` and `reorderContainer(for:)` on its enclosing container. Apply the callback's `ReorderDifference` to the source data yourself; SwiftUI does not mutate it. This works in lists, lazy stacks and grids, ordinary stacks, and custom layouts. Earlier versions require `List` with `onMove()` or a custom drag implementation. Elements must conform to `Identifiable`, or use the `itemID:` overload.

For example:

```swift
ScrollView {
    LazyVStack {
        ForEach(bookmarks) { bookmark in
            BookmarkRow(bookmark: bookmark)
        }
        .reorderable()
    }
    .reorderContainer(for: Bookmark.self) { change in
        change.apply(to: &bookmarks)
    }
}
```

SwiftUI has no built-in way to apply this difference. Add a helper like this one, adapted from an Apple example, in its own file:

```swift
extension ReorderDifference where CollectionID == ReorderableSingleCollectionIdentifier {
    func apply<Items>(to items: inout Items)
    where Items: RangeReplaceableCollection,
          Items.Element: Identifiable,
          Items.Element.ID == ItemID {
        let sourceIDs = Set(sources)
        var relocated: [Items.Element] = []

        items.removeAll { candidate in
            if sourceIDs.contains(candidate.id) {
                relocated.append(candidate)
                return true
            }
            return false
        }

        switch destination.position {
        case .before(let followingID):
            let insertionPoint = items.firstIndex { $0.id == followingID } ?? items.endIndex
            items.insert(contentsOf: relocated, at: insertionPoint)
        case .end:
            items.append(contentsOf: relocated)
        }
    }
}
```

- For moves across sections, identify each inner collection with `reorderable(collectionID:)`, and use `reorderContainer(for:in:)` on the enclosing container. Read `difference.destination.collectionID` to determine the receiving section.
- Reordering needs no drag-and-drop code; `reorderContainer(for:)` already acts as the drag container. Add `dragContainer(for:)` to the same container only when items should also take part in system drag and drop, such as dragging out to other views or apps, and make the item type `Transferable`. A `draggable()` on a row has no effect on reordering.
- Swipe actions also work in scroll views containing lazy stacks, lazy grids, or ordinary stacks. Apply `swipeActions()` to the rows and `swipeActionsContainer()` to the `ScrollView`; omitting the latter leaves the actions inactive without an error.
