# Navigation and presentation

## Rules

- Use `NavigationStack` or `NavigationSplitView` as appropriate; flag all use of the deprecated `NavigationView`.
- Strongly prefer `navigationDestination(for:)` to specify destinations; flag the old `NavigationLink(destination:)` pattern where it should be replaced. Use `NavigationLink(value:)` or `router.navigate(to:)` to push.
- Never mix `navigationDestination(for:)` and `NavigationLink(destination:)` in the same navigation hierarchy; it causes significant problems.
- Register `navigationDestination(for:)` once per data type within each navigation stack; flag competing registrations in the same stack. Independent stacks, including those in separate tabs, can each register the same type.
- Store lightweight route data in the path (identifiers or small value models), never view instances or heavy state.
- Keep navigation state per scene (scene-root `@State` or `@SceneStorage`), never in a singleton or `@AppStorage`, so two windows can navigate independently.


## Router pattern

One `NavigationStack` per tab, each bound to its own router. The router owns the path and the presented sheet, and is injected into the environment so any child can navigate or present without prop-drilling.

```swift
@MainActor
@Observable
final class Router {
    var path: [Route] = []
    var presentedSheet: SheetDestination?

    func navigate(to route: Route) {
        path.append(route)
    }

    func popToRoot() {
        path.removeAll()
    }
}

enum Route: Hashable {
    case account(id: Account.ID)
    case post(id: Post.ID)
}
```

Map routes to views in one place, applied once per stack:

```swift
extension View {
    func withAppRoutes() -> some View {
        navigationDestination(for: Route.self) { route in
            switch route {
            case .account(let id):
                AccountView(id: id)
            case .post(let id):
                PostView(id: id)
            }
        }
    }
}
```

A reusable stack container uses `@Bindable` to get a binding to the path – no `Binding(get:set:)` needed:

```swift
struct RoutedStack<Root: View>: View {
    @Bindable var router: Router
    @ContentBuilder let root: Root

    var body: some View {
        NavigationStack(path: $router.path) {
            root
                .withAppRoutes()
        }
        .withSheetDestinations($router.presentedSheet)
        .environment(router)
    }
}
```

Apply `.environment(router)` outside the sheet modifier so sheet content inherits the router too.

A child view navigates or presents through the environment:

```swift
struct PostRow: View {
    @Environment(Router.self) private var router
    let post: Post

    var body: some View {
        Button(post.title, action: openAuthor)
    }

    private func openAuthor() {
        router.navigate(to: .account(id: post.authorID))
    }
}
```

- Reset the path when the app context changes (account switch, logout).
- If the project already uses a routing library, follow it rather than introducing this pattern.


## Tabs

Define tab identity, titles, icons, and root content in one enum, and keep one router per tab:

```swift
enum AppTab: Hashable, CaseIterable, Identifiable {
    case home, search, settings

    var id: Self { self }

    var title: LocalizedStringResource {
        switch self {
        case .home: "Home"
        case .search: "Search"
        case .settings: "Settings"
        }
    }

    var systemImage: String {
        switch self {
        case .home: "house"
        case .search: "magnifyingglass"
        case .settings: "gear"
        }
    }

    @MainActor @ContentBuilder
    var rootView: some View {
        switch self {
        case .home: HomeView()
        case .search: SearchView()
        case .settings: SettingsView()
        }
    }
}

@MainActor
@Observable
final class TabRouters {
    let home = Router()
    let search = Router()
    let settings = Router()

    func router(for tab: AppTab) -> Router {
        switch tab {
        case .home: home
        case .search: search
        case .settings: settings
        }
    }
}
```

iOS 18+ – use the `Tab` API:

```swift
struct AppView: View {
    @State private var selectedTab: AppTab = .home
    @State private var routers = TabRouters()

    var body: some View {
        TabView(selection: $selectedTab) {
            ForEach(AppTab.allCases) { tab in
                Tab(tab.title, systemImage: tab.systemImage, value: tab) {
                    RoutedStack(router: routers.router(for: tab)) {
                        tab.rootView
                    }
                }
            }
        }
    }
}
```

iOS 17 target – `Tab` is unavailable, so use `tabItem()` and `tag()` with the same enum. This is the one place `tabItem()` is still correct; replace it once the target reaches iOS 18.

```swift
TabView(selection: $selectedTab) {
    ForEach(AppTab.allCases) { tab in
        RoutedStack(router: routers.router(for: tab)) {
            tab.rootView
        }
        .tabItem { Label(tab.title, systemImage: tab.systemImage) }
        .tag(tab)
    }
}
```

- Use `Tab(role: .search)` for a search tab (iOS 18+); the system places it at the trailing end and, on iOS 26, separates it in the tab bar.
- Use `TabSection` with `.tabViewStyle(.sidebarAdaptable)` (iOS 18+) when tabs should become a sidebar on iPad. See `resizability.md` for iPhone sidebar behavior on iOS 27.
- To intercept a tab that performs an action instead of changing selection (here, an extra `compose` case in `AppTab`), put the interception in a writable computed property on a store, and bind to that – not a `Binding(get:set:)` in `body`:

```swift
@MainActor
@Observable
final class AppNavigation {
    var selectedTab: AppTab = .home
    var isComposing = false

    var tabSelection: AppTab {
        get { selectedTab }
        set {
            if newValue == .compose {
                isComposing = true
            } else {
                selectedTab = newValue
            }
        }
    }
}

// In the view: TabView(selection: $navigation.tabSelection) { … }
```

For tab-specific iOS 26 behavior (minimizing tab bar, bottom accessory, search activation) see `liquid-glass.md`.


## Sheets

- If a sheet presents an optional piece of data, prefer `sheet(item:)` over `sheet(isPresented:)` so the optional is safely unwrapped. Avoid `if let` inside a sheet body.
- When the sheet view takes the item as its only initializer parameter, prefer `sheet(item: $someItem, content: SomeView.init)` over `sheet(item: $someItem) { someItem in SomeView(item: someItem) }`.
- Use one optional enum instead of several Booleans for mutually exclusive sheets.
- Sheets own their actions: read `@Environment(\.dismiss)` and call it internally, rather than forwarding `onCancel` / `onConfirm` closures through many layers.
- A sheet that needs to push gets its own `NavigationStack`.

Local sheet:

```swift
@State private var editingItem: Item?

.sheet(item: $editingItem, content: EditItemSheet.init)
```

App-wide sheets, driven by the router:

```swift
enum SheetDestination: Identifiable, Hashable {
    case composer
    case editProfile
    case report(postID: Post.ID)

    var id: Self { self }
}

extension View {
    func withSheetDestinations(_ sheet: Binding<SheetDestination?>) -> some View {
        self.sheet(item: sheet) { destination in
            switch destination {
            case .composer:
                ComposerView()
            case .editProfile:
                EditProfileView()
            case .report(let postID):
                ReportView(postID: postID)
            }
        }
    }
}
```

A sheet that owns its actions:

```swift
struct EditItemSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(ItemStore.self) private var store

    let item: Item

    @State private var isSaving = false

    var body: some View {
        NavigationStack {
            Form { /* … */ }
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel", role: .cancel) { dismiss() }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Save", action: save)
                            .disabled(isSaving)
                    }
                }
        }
    }

    private func save() {
        isSaving = true
        Task {
            await store.save(item)
            dismiss()
        }
    }
}
```

Keep `SheetDestination` cases lightweight: pass identifiers or small models, not heavy state.


## Alerts and confirmation dialogs

- Attach `confirmationDialog()` to its triggering control so Liquid Glass animates from the right source. An action inside `ToolbarOverflowMenu` is the exception: the system owns that menu, so a dialog attached to a button inside it never appears, even though the button's action runs. Attach it to a view outside the menu and drive presentation with state.
- When building with Xcode 27 or later, use `alert(_:item:)` or `confirmationDialog(_:item:)` when presentation concerns one optional value, such as a pending removal. The optional supplies the unwrapped value to the closures and becomes `nil` on dismissal, without requiring `Identifiable`. This removes the separate Boolean and `presenting:` value, much as `sheet(item:)` does. These overloads are compiled into the app and support iOS 15 onward, or iOS 16 when the title is a `LocalizedStringResource`, without an availability check.
- If an alert has only a single "OK" button that does nothing but dismiss the alert, it can be omitted entirely: `.alert("Dismiss Me", isPresented: $isShowingAlert) { }`.


## Deep links

Centralize URL handling in the router: one entry point for external links (`onOpenURL`) and one for in-app links (`OpenURLAction`). The router decides whether to navigate or hand the URL back to the system.

```swift
extension Router {
    func handle(_ url: URL) -> OpenURLAction.Result {
        guard let route = Route(url: url) else {
            return .systemAction
        }
        navigate(to: route)
        return .handled
    }
}

extension View {
    func withLinkRouting(_ router: Router) -> some View {
        environment(\.openURL, OpenURLAction { url in
            router.handle(url)
        })
        .onOpenURL { url in
            _ = router.handle(url)
        }
    }
}
```

- Parse URLs into `Route` in one failable initializer; never assume a URL is internal.
- Always fall back to `.systemAction` for URLs the app does not own.
- If resolving a link needs network work, navigate to a loading destination and resolve it there with `.task`, rather than blocking.
