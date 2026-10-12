# Testing SwiftData code

Tests use Swift Testing (`@Test`, `#expect`, `#require`). In MV architecture, test stores, services, model actors, and pure model logic – there are no view models to mock.


## What to test, and how

| Code under test | Approach |
| --- | --- |
| Pure model logic (validation, formatting, sorting, computed values) | Plain values; no `ModelContainer`, no `import SwiftData` needed |
| A store or service that reads and writes through `ModelContext` | Fresh in-memory container per test |
| A `@ModelActor` | Fresh in-memory container; call it with `await`; assert on its `Sendable` results |
| A store that depends on a network or other client | Inject a stub client (see `swift-ui` skill, lightweight clients); add an in-memory container only if the store also persists |
| Predicates and fetch descriptors | In-memory container seeded with matching and non-matching records |
| Migrations | Real store files from previous versions (see `migrations.md`) |

If a test imports SwiftData only to build a value it never inserts or fetches, the logic probably belongs in a plain type – flag it rather than working around it.


## In-memory containers

```swift
import Testing
import SwiftData
@testable import Trips

@MainActor
struct TripEditorTests {
    @Test func addingStopLinksItToTrip() throws {
        let container = try AppStore.makeContainer(inMemory: true)
        let context = container.mainContext
        let trip = Trip(name: "Rome", startDate: .now)
        context.insert(trip)

        let editor = TripEditor(context: context)
        try editor.addStop("Colosseum", to: trip)

        let stops = try context.fetch(FetchDescriptor<Stop>())
        #expect(stops.count == 1)
        #expect(stops.first?.trip == trip)
    }
}
```

- **Always in memory** (`isStoredInMemoryOnly: true`). A test that writes to the real store mutates device state.
- **A fresh container in every test.** Never share a container or context between tests: Swift Testing runs tests in parallel, and shared state makes tests pass alone and fail together.
- **Build the container with the app's own factory** (`inMemory: true`), so the schema in tests matches production. The factory should skip the migration plan for in-memory stores – there is nothing to migrate, and intermittent save failures have been reported (see `migrations.md`).
- Use fixed dates and identifiers in test data, not `.now` or fresh UUIDs, wherever results depend on them.


## Testing `@ModelActor` code

```swift
@Test func importReportsCount() async throws {
    let container = try AppStore.makeContainer(inMemory: true)
    let importer = TripImporter(modelContainer: container)

    let summary = try await importer.importTrips([.fixture(name: "Rome")])
    #expect(summary.imported == 1)

    // Verify through a separate context, never through the actor's own.
    let context = ModelContext(container)
    #expect(try context.fetchCount(FetchDescriptor<Trip>()) == 1)
}
```

- Pass DTOs or `PersistentIdentifier`s into the actor, never `@Model` instances – in tests exactly as in production.
- Assert on the actor's returned `Sendable` values, or read through a separate context made from the same container. Never reach into the actor's `modelContext` from the test.
- Await the actor's methods directly. Do not wrap calls in `Task {}` and poll, and never sleep.


## Testing CloudKit-related logic

Sync itself cannot be unit-tested, but the logic around it can:

- Deduplication: insert duplicates with known creation dates and UUIDs, run the merge, and assert that the deterministic winner survives with all relationships moved to it.
- Late data: test that code handles a missing optional relationship.
- Use in-memory containers without CloudKit in tests (`cloudKitDatabase: .none` or simply in memory).


## Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Sharing a container or context across tests | Tests pass alone, fail in the full suite | New container per test |
| Missing `isStoredInMemoryOnly: true` | Tests leak state through the real store | Build test containers in memory |
| Migration plan on an in-memory store | Reported intermittent `save()` failures | Skip the plan for in-memory configurations |
| A model subclass missing from the test schema | Subclass inserts or queries fail | Use the app's factory, which lists every model |
| Reading `actor.modelContext` from a test | Hides the cross-actor bug the test should catch | Return `Sendable` results, or read via a separate context |
| `Task.sleep` to wait for persistence | Flaky tests | `await` the operation itself |
