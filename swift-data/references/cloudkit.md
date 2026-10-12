# SwiftData with CloudKit

**Apply this file only when the project syncs with CloudKit** (Step 0 in `SKILL.md`), or when the user plans to add sync. If sync might be added later, design models to these rules from the start: retrofitting them means a schema migration on existing user data.

SwiftData syncs through `NSPersistentCloudKitContainer` to the user's private iCloud database.


## Schema rules

- **Never use `@Attribute(.unique)` or `#Unique`.** CloudKit does not support them, and when present they make local storage fail too.
- **Every property has a default value or is optional.**
- **Every relationship is optional.** To-many relationships become optional arrays, e.g. `var stops: [Stop]? = []`.
- Keep explicit delete rules and inverses (see `core-rules.md`); they matter even more when records arrive in arbitrary order.
- Indexes and model subclasses are supported, given the right OS version (`indexing.md`, `class-inheritance.md`).

```swift
@Model
final class Trip {
    var uuid = UUID()
    var name = ""
    var startDate = Date.now
    @Relationship(deleteRule: .cascade, inverse: \Stop.trip)
    var stops: [Stop]? = []

    init(name: String, startDate: Date) {
        self.name = name
        self.startDate = startDate
    }
}
```


## Eventual consistency

CloudKit sync is eventually consistent. Code must behave correctly when data has not arrived yet, arrives late, or arrives in pieces:

- A related model may still be `nil` when its parent appears. Handle optional relationships gracefully in UI and logic.
- Do not assume a fresh install starts empty – or full. Data may flow in seconds or minutes after launch.
- Do not seed default data unconditionally on first launch: every device will seed, and the copies will sync into duplicates. Seed only data that cannot collide, or deduplicate (below).


## Duplicates

Without uniqueness constraints, the same logical record can exist twice – seeded on two devices, or created offline on both. Plan for it:

1. **Give each model a stable identity** that is meaningful across devices: a `uuid` assigned once at creation, or a natural key (an external ID, or a fixed key for seeded singletons). `persistentModelID` is local to one store and cannot serve this purpose.
2. **Detect duplicates** by fetching all records that share the key – at launch, and after remote changes arrive (on iOS 18+, history tells you what was imported; see `widgets-and-history.md`).
3. **Pick the winner deterministically**, so every device independently keeps the same record – for example, the earliest creation date, with the `uuid` string as a tie-breaker. Never "keep the one on this device".
4. **Merge**: move relationships from the losers to the winner, combine fields if needed, delete the losers, save.

Deduplication runs on every device; because the winner rule is deterministic, all devices converge on the same result.


## Schema evolution

Once a CloudKit schema is promoted to production, it is **additive only**: you can add model types and properties, but cannot delete model types or change existing attributes. Devices running an older app version keep syncing against the same schema.

- Add new properties with defaults, or optional. Do not delete, rename, or change the type of a synced property – add a new one and stop using the old.
- `originalName` renames work locally but not for the CloudKit schema; treat a rename as "add new, migrate values, keep the old field".
- Custom migration stages run on every device independently. Make them deterministic and idempotent, and only write values into newly added fields.

See `migrations.md` for the migration plan itself.


## Setup checklist

1. **iCloud capability** with CloudKit enabled and a container selected (requires an Apple Developer account with admin rights).
2. **Background Modes → Remote notifications**, so the app receives silent pushes about server changes.
3. **Container choice.** By default SwiftData uses the first CloudKit container in the entitlements. With several containers, choose explicitly: `ModelConfiguration(cloudKitDatabase: .private("iCloud.com.example.App"))`. If the app already uses CloudKit directly with an incompatible schema, disable SwiftData sync with `cloudKitDatabase: .none`. For an app already in production, specify only containers that SwiftData or Core Data managed before.
4. **Initialize the development schema** before testing sync: in a `#if DEBUG` block, load the same store with `NSPersistentCloudKitContainer` (built from `NSManagedObjectModel.makeManagedObjectModel(for:)`), call `initializeCloudKitSchema()`, and unload the store before creating the `ModelContainer`. Follow Apple's "Syncing model data across a person's devices" for the exact code.
5. **Inspect the schema** in the CloudKit Console; promote it to production before release.
6. **Test with two devices** (or a device and a simulator signed into the same account): create, edit, delete, and go offline on each side.


## Review checklist

- [ ] No `@Attribute(.unique)` or `#Unique`.
- [ ] All properties have defaults or are optional; all relationships are optional.
- [ ] Every model has a cross-device identity if duplicates are possible.
- [ ] No unconditional seeding on first launch.
- [ ] No deleted, renamed, or retyped synced properties after release.
- [ ] Code tolerates missing related records and late-arriving data.
