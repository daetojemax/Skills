# Containers, contexts, and actors

## Container setup comes first

- Create one `ModelContainer` per store and share it. In SwiftUI, attach `.modelContainer(...)` at the app or window root, or create the container in the `App` and pass it with `.modelContainer(container)`.
- If no container is attached, the environment's context has no schema: inserts fail and fetches come back empty. Check the wiring before debugging "missing data".
- SwiftData adds models reachable through relationships to the schema automatically, but list every `@Model` type explicitly anyway – it documents the schema and is required for subclasses, which are never inferred (see `class-inheritance.md`).
- Create the container manually (not only through the view modifier) whenever you need a migration plan, an app group, a CloudKit database choice, or access from a widget or App Intent:

```swift
enum AppStore {
    static func makeContainer(inMemory: Bool = false) throws -> ModelContainer {
        let schema = Schema([Trip.self, Stop.self])
        let configuration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: inMemory)
        return try ModelContainer(for: schema, configurations: [configuration])
    }
}
```

Keep this factory in one place so the app, widgets, intents, previews, and tests build the store the same way (see `widgets-and-history.md`, `testing.md`).


## Context roles

- `container.mainContext` – the same context as `@Environment(\.modelContext)` – is `@MainActor`-bound and meant for UI-driven work: `@Query`, editing forms, user-initiated inserts and deletes.
- A context created with `ModelContext(container)` belongs to whatever isolation creates it. Use it for one unit of work, not as a long-lived shared object.
- For background persistence – imports, sync processing, large batch updates – use a `@ModelActor` (below). Never run long write pipelines on the main context.


## Saving

- Autosave on the main context happens at hard-to-predict moments. When correctness matters – before the app may be suspended, before reading data from another process, after an import – call `try context.save()` explicitly. No need to check `hasChanges` first.
- Contexts you create yourself are not configured like the main context; set `autosaveEnabled` deliberately or save explicitly.
- Group related mutations with `try context.transaction { … }`, which saves when the block finishes.
- Handle save errors visibly – never `try?` a save that the user is waiting on.


## Insert, update, delete

- Insert the root of a new object graph; related models are inserted with it.
- Updates need no API: changing a property on a managed model is tracked automatically.
- `context.delete(model)` removes one instance; `try context.delete(model: Trip.self, where: predicate)` deletes in bulk. **Without a predicate, the bulk form deletes every instance of the type** – always review the predicate, and confirm destructive bulk deletes with the user.
- Clear any selection that refers to a model before deleting it.


## Undo

- Enable undo with `.modelContainer(for: …, isUndoEnabled: true)` or by giving the main context an `UndoManager`.
- Undo covers changes made through the main context. Background contexts are not a substitute for undo-enabled user editing.


## In MV architecture

- Views read with `@Query` and write through `@Environment(\.modelContext)` for simple edits.
- When logic grows – validation, multi-step writes, anything worth testing – move it into a `@MainActor` store or service that receives the `ModelContext` (or the `ModelContainer`) through its initializer. `@Query` never moves into a store; stores fetch with `FetchDescriptor`.

```swift
@MainActor
@Observable
final class TripEditor {
    private let context: ModelContext

    init(context: ModelContext) {
        self.context = context
    }

    func addStop(_ title: String, to trip: Trip) throws {
        let stop = Stop(title: title)
        stop.trip = trip
        context.insert(stop)
        try context.save()
    }
}
```


## Background work with `@ModelActor`

`@ModelActor` creates an actor with its own `ModelContext` and serialized access to it.

```swift
@ModelActor
actor TripImporter {
    func importTrips(_ records: [TripRecord]) throws -> ImportSummary {
        for record in records {
            modelContext.insert(Trip(record))
        }
        try modelContext.save()
        return ImportSummary(imported: records.count)
    }
}

// From a main-actor store:
let importer = TripImporter(modelContainer: container)
let summary = try await importer.importTrips(records)
```

- Create the actor with the shared `ModelContainer`, never with a context.
- **`@Model` instances and `ModelContext` never cross isolation boundaries.** Pass `Sendable` value types (DTOs such as `TripRecord`, `ImportSummary`) or `PersistentIdentifier`s, and re-fetch inside the receiving context:

```swift
func markVisited(_ id: PersistentIdentifier) throws {
    guard let stop = modelContext.model(for: id) as? Stop else { return }
    stop.isVisited = true
    try modelContext.save()
}
```

- `PersistentIdentifier` is temporary until the model's first save; save before handing an identifier to another context.
- The main context does not see a background actor's changes until that actor saves.
- Do not create a `@ModelActor` just to wrap a few UI-driven writes; the main context is the right place for those.


## Identity

- Use `persistentModelID` for in-process identity (selection, navigation routes).
- It is local to one store. For identity that must survive across devices or services – CloudKit sync, server IDs, deep links – add your own stable property, e.g. `var uuid = UUID()` assigned once at creation (see `cloudkit.md`).
