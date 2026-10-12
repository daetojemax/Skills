# TabView: sidebars, sections, and dynamic tabs

Basic tab architecture – the `AppTab` enum, one router per tab, the iOS 17 `tabItem()` fallback, and intercepting a "compose" tab – lives in `navigation.md`. This file covers the iOS 18+ extras.

## Sidebar-adaptable tabs (iOS 18+)

- Apply `.tabViewStyle(.sidebarAdaptable)` so tabs become a sidebar on iPad and Mac. On iOS 27, combine it with `.defaultTabBarPlacement(.sidebar)` to get a sidebar on wide iPhone layouts too (see `resizability.md`).
- Group sidebar-only destinations with `TabSection("Title") { … }` and `.tabPlacement(.sidebarOnly)`.
- Use `.tabPlacement(.pinned)` for a single tab that should always stay visible.
- Use `tabViewSidebarHeader { … }` for a header above the sidebar list.

```swift
TabView(selection: $selectedTab) {
    Tab("Home", systemImage: "house", value: AppTab.home) {
        RoutedStack(router: routers.home) { HomeView() }
    }

    TabSection("Collections") {
        ForEach(collections) { collection in
            Tab(collection.name, systemImage: collection.symbol, value: AppTab.collection(collection.id)) {
                CollectionView(collectionID: collection.id)
            }
        }
    }
    .tabPlacement(.sidebarOnly)

    Tab(role: .search) {
        RoutedStack(router: routers.search) { SearchView() }
    }
}
.tabViewStyle(.sidebarAdaptable)
```

## Dynamic tabs

- Model dynamic tabs as an enum case with a stable associated identifier, e.g. `case collection(Collection.ID)`, so `AppTab` stays `Hashable` and identity is stable.
- Never derive a tab's identity from editable fields such as its title.
- Keep the source data for dynamic tabs in a store, not in the view.

## Pitfalls

- Do not add a view model per tab; keep tab state local or in `@Observable` stores.
- Give each tab both a title and an icon; vertical bars and overflow menus need both.
- For iOS 26 tab-bar behaviors (minimize on scroll, bottom accessory, search activation) see `liquid-glass.md`.
