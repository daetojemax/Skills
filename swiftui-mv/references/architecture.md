# Architecture: MV (model–view), not MVVM

Default to vanilla SwiftUI. Views own local UI state and orchestrate; `@Observable` stores and services own shared state and real work; dependencies arrive through the environment or the initializer. View models are the exception, not the default.

The default stack:

- `@State` for local view state.
- `@Environment` for shared app services and stores.
- `@Query` for SwiftData-backed collections.
- `.task`, `.task(id:)`, and `onChange()` for lightweight orchestration.
- Services, stores, clients, and models for business logic.


## State ownership

Choose where the state lives first, then pick the wrapper. Use the narrowest tool that matches the ownership.

| Scenario | Pattern |
| --- | --- |
| Local UI state owned by one view | `@State private var` |
| Child mutates a parent-owned value | `@Binding` |
| Root-owned reference model | `@State private var store = Store()` with an `@Observable` type |
| Child reads an injected `@Observable` model | Plain stored property: `let store: Store` |
| Child needs bindings into an injected `@Observable` model | `@Bindable var store: Store` |
| Shared app service, store, or configuration | `@Environment(Store.self) private var store`, installed once near the root |
| SwiftData collection | `@Query` plus `@Environment(\.modelContext)` |
| Window-specific UI state (selected tab, navigation path) | Scene-root `@State` or `@SceneStorage` |

- Do not introduce a reference model when plain value state is enough.
- `@Observable` classes are `@MainActor` unless the project uses Main Actor default isolation (see `data.md`).
- `ObservableObject`, `@StateObject`, `@ObservedObject`, and `@EnvironmentObject` exist only in legacy code. Since every supported target is iOS 17+, new code uses Observation.


## Where logic lives

- **View** – layout, local UI state, presentation decisions, thin action methods that call into stores or services.
- **Store** (`@Observable`, usually `@MainActor`) – shared, long-lived state plus the operations that mutate it. Injected through the environment or the initializer.
- **Service / client** – networking, persistence, and other side effects. Stateless or internally isolated (an actor). Easy to swap for previews and tests – see `components/lightweight-clients.md`.
- **Model** – value types and domain rules: validation, formatting, sorting (`Comparable`), transformation.

Test services, stores, and model transformations. Validate views with previews and, where needed, UI tests. Do not introduce a view model just to make a simple view "testable" – that adds ceremony without improving the design.


## Preferred pattern: local state plus environment

```swift
struct FeedView: View {
    @Environment(FeedClient.self) private var client

    @State private var viewState: ViewState = .loading

    var body: some View {
        List {
            switch viewState {
            case .loading:
                ProgressView("Loading feed…")
            case .failed(let message):
                ErrorStateView(message: message, retry: load)
            case .loaded(let posts):
                ForEach(posts) { post in
                    PostRow(post: post)
                }
            }
        }
        .task { await load() }
    }

    private func load() async {
        do {
            viewState = .loaded(try await client.feed())
        } catch is CancellationError {
            return
        } catch {
            viewState = .failed(error.localizedDescription)
        }
    }
}

extension FeedView {
    enum ViewState {
        case loading
        case failed(String)
        case loaded([Post])
    }
}
```

State stays close to the UI that renders it, the dependency comes from the environment instead of a wrapper object, and the client owns the real work. The `switch` sits inside a stable `List`, so the container's identity never changes.

With SwiftData, `@Query` already is the data flow. Do not add a view model that manually fetches and mirrors the same data:

```swift
struct BookListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Book.title) private var books: [Book]

    var body: some View {
        List(books) { book in
            BookRow(book: book)
                .swipeActions {
                    Button("Delete", systemImage: "trash", role: .destructive) {
                        modelContext.delete(book)
                    }
                }
        }
    }
}
```

For SwiftData itself, defer to the `swiftdata-pro` skill.


## Dependency injection

- Use `@Environment` for app-level services, shared stores, theme, and configuration that many descendants genuinely need.
- Prefer initializer injection for feature-local dependencies and models. Do not move something into the environment just to avoid passing one or two arguments.
- Keep mutable feature state out of the environment unless it is intentionally shared across broad parts of the app.
- Install shared dependencies in one place – a single `withAppDependencies()` view modifier at the root – so call sites cannot forget one. Keep that modifier to wiring only; no feature state or heavy logic.
- Do not reach for global singletons (`.shared`) from views. Create instances at the app root, store them in `@State`, and inject them.
- Rapidly changing values (scroll offsets, geometry, timers) never go into the environment – see `performance.md`.

```swift
@main
struct MyApp: App {
    @State private var session = SessionStore(client: .live())
    @State private var library = LibraryStore(client: .live())

    var body: some Scene {
        WindowGroup {
            AppView()
                .withAppDependencies(session: session, library: library)
        }
    }
}

extension View {
    func withAppDependencies(session: SessionStore, library: LibraryStore) -> some View {
        environment(session)
            .environment(library)
            .task(id: session.currentAccountID) {
                await library.reload(for: session.currentAccountID)
            }
    }
}
```

Use `.task(id:)` in the wiring modifier to react to app-level changes such as an account switch. Keep that work lightweight; long-running work belongs in services.


## Async state and task lifecycle

- Use `.task` for load-on-appear work that belongs to the view lifecycle; it is cancelled automatically when the view disappears.
- Use `.task(id:)` when work should restart for a changing input such as a query, selection, or identifier.
- Treat cancellation as a normal path. Catch `CancellationError` silently, and check `Task.isCancelled` in longer flows.
- Debounce user-driven work such as search inside `.task(id:)` with `try await Task.sleep(for:)` – the previous task is cancelled when the input changes, so no extra debouncer is needed.
- Model loading as one enum (`loading`, `loaded`, `failed`) rather than several independent Booleans.
- If async work spans several screens or must survive dismissal, move it into a store or service.

```swift
.task(id: query) {
    do {
        try await Task.sleep(for: .milliseconds(250))
        results = query.isEmpty ? [] : try await client.search(query)
    } catch is CancellationError {
        return
    } catch {
        searchError = error
    }
}
```


## When a view model is justified

A dedicated per-screen model can be reasonable when at least one of these is true:

- the user explicitly asks for one;
- the codebase already standardizes on view models for that feature – follow local convention;
- the screen needs a long-lived reference model with behavior that does not fit naturally in a store or service;
- the feature adapts a non-SwiftUI API that needs a bridge object (delegates, KVO, AVFoundation);
- several views share presentation-specific state that is not better modeled as app-level environment data.

Even then, keep it small, `@MainActor @Observable`, non-optional, and created once in the owning view's initializer – never through `bootstrapIfNeeded()`-style delayed setup:

```swift
struct EditorView: View {
    @State private var model: EditorModel

    init(document: Document) {
        _model = State(initialValue: EditorModel(document: document))
    }
}
```

Initialize each `@State` in exactly one place: here the initializer, so the declaration has no initial value (see `data.md`).


## Refactoring toward MV

1. Remove view models that only mirror local view state or wrap environment dependencies.
2. Replace optional or lazily bootstrapped view models with plain view state when that is enough.
3. Move business logic out of `body` and lifecycle modifiers into stores, services, or models.
4. Split large bodies into smaller view types before adding any new layer of indirection.
5. Keep behavior intact: do not change layout or business logic unless asked.

When editing an existing codebase that consistently uses MVVM, follow its convention for the code you touch and suggest MV changes separately rather than converting files unasked.
