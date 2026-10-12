# Split views and columns

## Intent

Multi-column layouts for iPad, Mac, and wide iPhone windows (including iPhone Duo's inner display).

## Default: NavigationSplitView

Prefer `NavigationSplitView`. On iOS 26+ it gets the Liquid Glass sidebar, fluid column resizing, correct safe areas, and `backgroundExtensionEffect()` support; on iOS 27 its detail-column toolbar participates in vertical bars (see `resizability.md`).

```swift
struct LibrarySplitView: View {
    @State private var selectedFolder: Folder.ID?
    @State private var selectedItem: Item.ID?
    @State private var showsInspector = false

    var body: some View {
        NavigationSplitView {
            FolderList(selection: $selectedFolder)
        } content: {
            ItemList(folderID: selectedFolder, selection: $selectedItem)
        } detail: {
            ItemDetail(itemID: selectedItem)
        }
        .inspector(isPresented: $showsInspector) {
            ItemInspector(itemID: selectedItem)
        }
    }
}
```

- Keep selections in state above the split view, so they survive size-class changes.
- Attach toolbars to the column whose content they control.
- Use `inspector(isPresented:content:)` for a trailing settings or detail panel: it becomes a column at regular width and a sheet at compact width.
- Use `navigationSplitViewColumnWidth(_:)` to tune column widths instead of fixed frames.
- On iPhone compact width, the split view collapses into a stack automatically; make sure every feature remains reachable (see `design.md`).

## Alternative: a custom secondary column

Only when the design needs something `NavigationSplitView` cannot express – for example a permanent secondary column (such as notifications) that is independent of selection – build the columns manually:

```swift
struct AppView: View {
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @AppStorage("showsSecondaryColumn") private var showsSecondaryColumn = true

    var body: some View {
        HStack(spacing: 0) {
            MainTabs()

            if horizontalSizeClass == .regular && showsSecondaryColumn {
                Divider()
                    .ignoresSafeArea()
                NotificationsColumn()
                    .frame(maxWidth: 380)
                    .environment(\.isSecondaryColumn, true)
            }
        }
    }
}

extension EnvironmentValues {
    @Entry var isSecondaryColumn = false
}
```

- Test for `== .regular`, never `!= .compact` (size classes are optional).
- A custom column gets none of the system behaviors: no glass sidebar, no vertical bar migration, no fluid resizing animations. Accept that consciously.

## Pitfalls

- Do not base column decisions on device idiom or orientation; use size classes.
- Do not drop features from compact layouts.
