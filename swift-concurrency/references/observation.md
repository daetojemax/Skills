# Observation and concurrency

How `@Observable` stores – the backbone of MV architecture – interact with actors, tasks, and Sendable checking. For SwiftUI data flow itself, see the `swift-ui` skill.


## Isolate the whole store to the main actor

Stores that SwiftUI views read are `@MainActor`. Annotate the whole class, not individual properties; partial isolation fragments access and produces confusing diagnostics. In a target with main-actor default isolation the annotation is implicit – check Step 0 in `SKILL.md`.

```swift
@MainActor
@Observable
final class FeedStore {
    private(set) var posts: [Post] = []
    private(set) var isLoading = false

    private let client: FeedClient

    init(client: FeedClient) {
        self.client = client
    }

    func refresh() async throws {
        isLoading = true
        defer { isLoading = false }
        posts = try await client.feed()   // suspends; resumes on the main actor
    }
}
```

- Async methods on a `@MainActor` store suspend at `await` and resume on the main actor, so assigning results afterwards is safe – no `MainActor.run` needed.
- Network and other I/O inside `client.feed()` does not block the main actor: awaiting suspends the store's method, and the I/O runs elsewhere. **Do not wrap I/O in `@concurrent`, `Task.detached`, or `Task { @concurrent in … }` + `MainActor.run`** – that adds hops and Sendable friction for no benefit.
- A `@MainActor` class is implicitly `Sendable`; never add `@unchecked Sendable` to it.

```swift
// ❌ Wrong: only one property isolated
@Observable
final class CounterStore {
    @MainActor var count = 0

    func increment() {
        count += 1 // error: main actor-isolated property accessed from nonisolated context
    }
}
```


## Parallel loading

Use `async let` for a fixed set of independent requests, then assign on the main actor:

```swift
func loadDashboard() async throws {
    async let stats = client.stats()
    async let notifications = client.notifications()
    (self.stats, self.notifications) = try await (stats, notifications)
}
```

For a dynamic number of requests, use a task group (see `structured.md`).


## Offloading CPU-heavy work

Only CPU-bound work – image processing, parsing very large payloads, compression – needs to leave the main actor. Put it in a `nonisolated` helper marked `@concurrent`, and await it from the store:

```swift
nonisolated struct ImageFilter {
    @concurrent
    func apply(to data: Data) async throws -> CGImage { /* heavy work */ }
}

@MainActor
@Observable
final class EditorStore {
    private(set) var processedImage: CGImage?
    private(set) var isProcessing = false

    func process(_ data: Data) async throws {
        isProcessing = true
        defer { isProcessing = false }
        processedImage = try await ImageFilter().apply(to: data)
    }
}
```

The call stays structured (cancellation and priority propagate), unlike `Task.detached`. Values crossing into the helper must be `Sendable` – `Data` is.


## Shared mutable state behind a store

When several tasks write the same state concurrently, keep a private actor for the writes and publish results through the main-actor store:

```swift
@MainActor
@Observable
final class DownloadStore {
    private(set) var completedCount = 0

    private let progress = ProgressCounter()

    func didFinishDownload() async {
        completedCount = await progress.increment()
    }
}

private actor ProgressCounter {
    private var value = 0

    func increment() -> Int {
        value += 1
        return value
    }
}
```

| Scenario | Strategy |
| --- | --- |
| State that views read | `@MainActor @Observable` store |
| CPU-heavy computation | `@concurrent` method on a `nonisolated` helper, awaited from the store |
| High-contention writes from many tasks | Private actor inside the store; the store publishes results |
| Background model that no view reads | An `actor` (or a custom global actor) – not `@Observable` |

Do not make SwiftUI read an `@Observable` isolated to a background global actor: views are `@MainActor` and would need `await` for every property. Publish results into a main-actor store instead.


## Passing stores across isolation boundaries

An `@Observable` class without isolation is not `Sendable`, and passing it into another actor fails to compile. Do not fix this with `@unchecked Sendable`.

Pass a `Sendable` snapshot of the values needed:

```swift
struct SettingsSnapshot: Sendable {
    let theme: Theme
    let syncInterval: Duration
}

actor SyncEngine {
    func apply(_ settings: SettingsSnapshot) { /* … */ }
}

// In the main-actor store:
await syncEngine.apply(SettingsSnapshot(theme: theme, syncInterval: syncInterval))
```

Or, if the store is `@MainActor` (and therefore `Sendable`), the other actor may hold a reference and read individual properties with `await` – but snapshots keep the dependency explicit and are usually clearer.


## Observing changes from async code

- **In SwiftUI views**, react to store changes with `onChange(of:)` or restart work with `.task(id:)`. Do not build observation streams for view logic.
- **Outside views, iOS 26+**: `Observations { … }` is an `AsyncSequence` of transactional snapshots of the `@Observable` properties read in its closure. Consume it in a task the owner can cancel:

```swift
func watchQuery() async {
    for await query in Observations({ self.query }) {
        results = query.isEmpty ? [] : (try? await client.search(query)) ?? []
    }
}
```

  Synchronous mutations are batched until the next suspension, so observers never see half-updated state. `Observations` is not back-deployed.
- **Outside views, before iOS 26**: use `withObservationTracking`, re-registering inside `onChange`. `onChange` fires once, *before* the new value is set, and not necessarily on the main actor – hop to the store's actor before reading the new value.
- Operators such as `debounce` or `throttle` on async sequences come from the swift-async-algorithms package. It is a third-party dependency: ask before adding it. In views, a sleep at the start of `.task(id:)` already debounces.


## Common diagnostics

| Error | Cause | Fix |
| --- | --- | --- |
| `Main actor-isolated property 'x' can not be accessed from a nonisolated context` | Reading a store property from non-isolated code without `await` | `await` it, or move the caller onto the main actor |
| `Capture of non-sendable type 'MyStore' in a '@Sendable' closure` | The store has no isolation, so it is not `Sendable` | Make the store `@MainActor` |
| `Sending value of non-Sendable type 'MyStore' risks causing data races` | Passing a non-isolated store into another actor | Pass a `Sendable` snapshot, or isolate the store |
| `Actor-isolated property 'x' can not be mutated from a Sendable closure` | Writing store state from `Task.detached` or a `@concurrent` closure | Return the value and assign it in the store after `await` |
