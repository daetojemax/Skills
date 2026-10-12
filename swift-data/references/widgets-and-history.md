# Widgets, App Intents, and persistent history

Use this when an extension – a widget, an App Intent, a share or notification extension – reads or writes the app's SwiftData store.


## One store in an app group

Each process has its own sandbox, so share the store through an app group:

1. Add the **App Groups** capability with the same group (e.g. `group.com.example.trips`) to the app and every extension that touches the store.
2. Add the model files and the container factory to all of those targets.
3. Build every container from the same factory, pointing at the group:

```swift
enum AppStore {
    static let appGroup = "group.com.example.trips"

    static func makeContainer(inMemory: Bool = false) throws -> ModelContainer {
        let schema = Schema(versionedSchema: SchemaV2.self)
        let configuration = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: inMemory,
            groupContainer: inMemory ? .none : .identifier(appGroup)
        )
        return try ModelContainer(for: schema, migrationPlan: AppMigrationPlan.self, configurations: [configuration])
    }
}
```

(Apply the in-memory / migration-plan branch from `migrations.md` if tests use this factory.)

- **Moving an existing store into an app group is a data migration.** A store created before the app group existed lives in the app's own container; changing the configuration silently opens a new, empty store. Copy or migrate the old store deliberately, and test the upgrade path.
- With CloudKit, decide which processes sync. Extensions are short-lived and should usually only read or make small writes; check Apple's guidance before enabling sync in an extension.


## Widgets

- Create the container once per extension process (a `static` in the timeline provider, not per timeline call), and read with a fresh `ModelContext(container)` – there is no `@Query` in a `TimelineProvider`.
- Convert models to small `Sendable` value types for the timeline entry; never put `@Model` instances in entries.
- Fetch narrowly (`fetchLimit`, `propertiesToFetch`): widgets have tight memory limits.
- After the app saves changes that a widget shows, call `WidgetCenter.shared.reloadTimelines(ofKind:)` (or `reloadAllTimelines()`). Save before reloading – the widget reads the store, not the app's unsaved context.


## App Intents and interactive widgets

- An intent's `perform()` builds a context from the shared container, writes, and **saves explicitly** before returning.
- Set an author on contexts in each process, so changes can be told apart later:

```swift
let context = ModelContext(container)
context.author = "widget"
```

- Return or display value types, not models.


## Seeing another process's changes in the app

The app's live queries are not guaranteed to reflect writes made by another process. When the scene becomes active (`scenePhase == .active`), catch up:

- **iOS 18+**: read persistent history since the last processed token (below) and update only what changed.
- **iOS 17**: history APIs are unavailable. Refetch the affected data when the scene becomes active, or after an intent reports a change.


## Persistent history (iOS 18+)

SwiftData records every save as a transaction. Each transaction has a token (`Comparable`, `Codable`) and the author of the context that wrote it.

```swift
func changes(after token: DefaultHistoryToken?, excludingAuthor author: String) throws -> [DefaultHistoryTransaction] {
    var descriptor = HistoryDescriptor<DefaultHistoryTransaction>()
    if let token {
        descriptor.predicate = #Predicate { $0.token > token && $0.author != author }
    } else {
        descriptor.predicate = #Predicate { $0.author != author }
    }
    return try ModelContext(container).fetchHistory(descriptor)
}
```

- **Persist the newest processed token** (encode it with `JSONEncoder`, store it in the app group's `UserDefaults` or a file) and fetch only newer transactions next time.
- **Filter changes.** One transaction can contain inserts, updates, and deletes of several model types. Each element of `transaction.changes` is a `HistoryChange` enum (`.insert`, `.update`, `.delete`); cast the payload to the model-specific type, check `updatedAttributes` for updates, then re-fetch the affected model by its `changedPersistentIdentifier` in your own context:

```swift
for transaction in transactions {
    for change in transaction.changes {
        guard case .update(let update) = change,
              let tripUpdate = update as? DefaultHistoryUpdate<Trip>
        else { continue }
        // When only certain fields matter, inspect tripUpdate.updatedAttributes (key paths) here.
        let tripID = tripUpdate.changedPersistentIdentifier
        // Re-fetch with context.model(for: tripID) and refresh UI or caches.
    }
}
```
- **Deleted models**: mark identifying attributes with `@Attribute(.preserveValueOnDeletion)` and read them from the delete change's `tombstone`, e.g. `deletion.tombstone[\.uuid]`. `persistentModelID` alone is useless once the model is gone.
- **Clean up**: delete transactions every consumer has processed, with `deleteHistory(_:)` and a `token < oldest processed token` predicate. History otherwise grows without limit.
- **`historyTokenExpired`**: the token refers to deleted history. Reset: refetch everything relevant, then store a fresh token.

The type names above (`DefaultHistoryTransaction`, `DefaultHistoryUpdate`, `HistoryChange`, `changedPersistentIdentifier`) match the SwiftData API reference. Apple's article "Fetching and filtering time-based model changes" still uses older beta names (`History.DefaultTransaction`, `changedModelID`); prefer the reference names, and if something does not compile, check the current documentation rather than guessing.
