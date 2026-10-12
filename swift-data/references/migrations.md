# Schema migrations

Every shipped schema change is a migration of real user data. Plan it before changing a model, and rehearse it on a store created by the previous app version – not only on clean installs.

If the project syncs with CloudKit, the rules in `cloudkit.md` ("Schema evolution") override anything below: synced schemas only grow.

Apple's reference pages for `VersionedSchema`, `SchemaMigrationPlan`, and `MigrationStage` contain no prose or examples, so this file is the working reference. The examples below were compiled in Swift 6 language mode and run against a real store (see `SOURCES.md`).


## Lightweight first

SwiftData migrates automatically when changes are lightweight, for example:

- adding a model type;
- adding a property with a default value, or an optional property;
- removing a property (not with CloudKit);
- renaming with `@Attribute(originalName: "oldName")` or `@Relationship(originalName:)` (not with CloudKit);
- changing a delete rule.

Anything that changes how existing values must be interpreted – splitting a field, changing a type, making an optional property required, deduplicating before adding a constraint – needs a custom stage.


## Versioned schemas

Even when every change is lightweight, keep versioned schemas from the first release. It costs little and makes the first custom migration painless.

```swift
enum SchemaV1: VersionedSchema {
    static let versionIdentifier = Schema.Version(1, 0, 0)
    static var models: [any PersistentModel.Type] { [Trip.self] }

    @Model
    final class Trip {
        var name = ""
        var startDate = Date.now

        init(name: String, startDate: Date) {
            self.name = name
            self.startDate = startDate
        }
    }
}

enum SchemaV2: VersionedSchema {
    static let versionIdentifier = Schema.Version(2, 0, 0)
    static var models: [any PersistentModel.Type] { [Trip.self] }

    @Model
    final class Trip {
        var name = ""
        var startDate = Date.now
        var endDate = Date.now

        init(name: String, startDate: Date, endDate: Date) {
            self.name = name
            self.startDate = startDate
            self.endDate = endDate
        }
    }
}

// The rest of the app always uses the current version.
typealias Trip = SchemaV2.Trip
```

- Each version is a complete, frozen copy of every model at that version. Never edit an old version after it has shipped.
- Use `static let` for `versionIdentifier` – a `static var` is mutable global state and fails strict concurrency checking.
- Point the rest of the app at the latest models with type aliases.


## Migration plan

```swift
enum AppMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [SchemaV1.self, SchemaV2.self]
    }

    static var stages: [MigrationStage] {
        [migrateV1toV2]
    }

    static var migrateV1toV2: MigrationStage {
        .custom(
            fromVersion: SchemaV1.self,
            toVersion: SchemaV2.self,
            willMigrate: nil,
            didMigrate: { context in
                let trips = try context.fetch(FetchDescriptor<SchemaV2.Trip>())
                for trip in trips {
                    trip.endDate = trip.startDate
                }
                try context.save()
            }
        )
    }
}
```

- List schemas oldest to newest, with a stage between each adjacent pair. Use `.lightweight(fromVersion:toVersion:)` where nothing custom is needed.
- `willMigrate` sees the old models (prepare or deduplicate before a constraint is added); `didMigrate` sees the new ones (fill new fields).
- Keep custom stages deterministic and idempotent.

Pass the plan when creating the container. The SwiftUI `.modelContainer(for:)` modifier cannot take a plan, so create the container yourself:

```swift
let schema = Schema(versionedSchema: SchemaV2.self)
let configuration = ModelConfiguration(schema: schema)
let container = try ModelContainer(
    for: schema,
    migrationPlan: AppMigrationPlan.self,
    configurations: [configuration]
)
```


## Testing migrations

- Keep a store file created by each shipped version and test opening it with the current plan.
- **Skip the migration plan for in-memory stores.** There is nothing to migrate, and intermittent save failures have been reported in that combination (not reproduced in a simple test, but the branch costs nothing). Branch in the container factory:

```swift
if configuration.isStoredInMemoryOnly {
    return try ModelContainer(for: schema, configurations: [configuration])
}
return try ModelContainer(for: schema, migrationPlan: AppMigrationPlan.self, configurations: [configuration])
```

- Errors such as `unknownSchema` or `backwardMigration` mean the stored version is missing from `schemas`, or the plan cannot reach the current version.


## Checklist

- [ ] The change is classified as lightweight or custom before writing code.
- [ ] Old `VersionedSchema` types are untouched; a new version was added.
- [ ] Every adjacent pair of versions has a stage.
- [ ] With CloudKit: only additive changes (see `cloudkit.md`).
- [ ] Tested by upgrading a store from the previous release, not only a clean install.
