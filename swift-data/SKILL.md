---
name: swift-data
description: Writes, reviews, and debugs SwiftData persistence – @Model design, relationships and delete rules, predicates and queries, ModelContainer and ModelContext, @ModelActor background work, CloudKit sync, schema migrations, widgets and App Intents sharing a store, persistent history, and SwiftData tests. Use when reading, writing, reviewing, or testing code that uses SwiftData.
license: MIT
metadata:
  version: "1.0.0"
  based-on: "SwiftData Pro 1.0 (Paul Hudson); SwiftData Expert (Kudrin Dmitry); SwiftData Testing (Akshay Pimprikar); Apple SwiftData documentation – see SOURCES.md"
---

# SwiftData

Write and review SwiftData code for data integrity first: no runtime-crashing predicates, no silent data loss, no models crossing actors, and schema changes that real user data survives. Report only genuine problems – do not nitpick or invent issues.


## Step 0: Know the project

Before advising, establish these facts from the project rather than assuming them:

```bash
xcodebuild -version
grep -rhoE "IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+" --include=project.pbxproj . | sort -u
grep -rln "CloudKit" --include='*.entitlements' . ; grep -rn "cloudKitDatabase" --include='*.swift' .
grep -rln "application-groups" --include='*.entitlements' . ; grep -rln "import WidgetKit\|import AppIntents" --include='*.swift' .
grep -rn "modelContainer(\|ModelContainer(\|VersionedSchema\|SchemaMigrationPlan\|@ModelActor" --include='*.swift' .
```

- **Deployment target** – the user's projects target iOS 17 or iOS 26. `#Index`, `#Unique`, and persistent history need iOS 18; model inheritance needs iOS 26.
- **CloudKit** – the user often, but not always, syncs with CloudKit. If the entitlements or a `cloudKitDatabase` setting show CloudKit, **every rule in `references/cloudkit.md` applies** and overrides general advice (no unique constraints, optional relationships, additive-only schema). If CloudKit is absent but the user is designing new models, ask whether sync is planned: retrofitting CloudKit rules later means migrating user data.
- **App group and extensions** – widgets or App Intents sharing the store mean `references/widgets-and-history.md` applies.
- **Container and migrations** – where the container is built, and whether a `SchemaMigrationPlan` exists.


## Core instructions

- Use SwiftData across the board. Do not suggest Core Data unless a feature cannot be built with SwiftData.
- MV architecture: views read with `@Query` and make simple writes through `@Environment(\.modelContext)`; stores and services use `ModelContext` and `FetchDescriptor`. `@Query` never appears outside views. Do not introduce view models or repository layers unless the codebase already has them.
- `@Model` instances and `ModelContext` never cross actor boundaries; pass `PersistentIdentifier`s or `Sendable` value types. For general concurrency, use the `swift-concurrency` skill; for SwiftUI, the `swift-ui` skill.
- Treat every change to a shipped model as a migration (`references/migrations.md`).
- Review destructive operations – bulk deletes, delete rules, migrations – before anything else, and confirm bulk deletes with the user.
- Do not introduce third-party frameworks without asking first.
- Organize files by feature; one model per file.


## Looking up Apple APIs

Do not rely on memory for exact signatures, parameters, or OS availability of Apple APIs – especially anything newer than iOS 18, or anything this skill marks as version-dependent.

1. **Xcode MCP `DocumentationSearch`** (semantic search over Apple's documentation; pass `frameworks`, e.g. `["SwiftUI"]`, to narrow it). Its tools load a few seconds after the server connects. It needs the Xcode MCP server to be configured and this agent approved; Xcode itself does not have to be open.
2. **If Xcode MCP is unavailable**, fetch the page as JSON: `https://developer.apple.com/tutorials/data/documentation/<framework>/<symbol>.json` – for example `.../documentation/swiftui/view/glasseffect(_:in:).json`. `metadata.platforms` gives availability per OS; `primaryContentSections` holds the declaration and discussion.
3. **If neither is available**, say that the API detail is unverified rather than presenting it as fact.

Prefer the API reference over Apple's articles when they disagree: articles sometimes keep beta-era names.

## Modes

### Designing models

1. Step 0 – especially CloudKit.
2. Apply `references/core-rules.md`: delete rules, explicit inverses, forbidden names, `@Transient`, enums.
3. With CloudKit (or planned sync), apply `references/cloudkit.md`: defaults or optionals everywhere, optional relationships, no uniqueness, a cross-device identity.
4. Consider indexes for frequently filtered or sorted properties on iOS 18+ (`references/indexing.md`). Use inheritance only for a genuine IS-A hierarchy on iOS 26+ (`references/class-inheritance.md`).
5. Put models in a `VersionedSchema` from the first release (`references/migrations.md`).

### Writing data code

- Queries and predicates: `references/predicates.md`.
- Containers, contexts, saving, undo, stores, `@ModelActor`: `references/context-and-actors.md`.
- Widgets, App Intents, app groups, history: `references/widgets-and-history.md`.
- Changing an existing model: `references/migrations.md`.

### Reviewing code

1. Data loss risks: delete rules, bulk deletes, migrations, store location changes.
2. Runtime crashes: predicates (`references/predicates.md`), forbidden property names and observers (`references/core-rules.md`).
3. CloudKit compatibility, if applicable (`references/cloudkit.md`).
4. Isolation: models or contexts crossing actors, `@Query` outside views (`references/context-and-actors.md`).
5. Query efficiency: fetch limits, `propertiesToFetch`, prefetching, indexes (`references/core-rules.md`, `references/indexing.md`).
6. Tests, if present (`references/testing.md`).

For a partial review, load only the relevant references.

### Writing tests

Follow `references/testing.md`: in-memory containers built by the app's own factory, a fresh container per test, stores and model actors tested directly.

### Debugging

Start with `references/troubleshooting.md`.


## Output format

If the user asks for a review, organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after code fix.
4. Say if the finding depends on CloudKit or the deployment target.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first. If the user asks you to write or improve code, apply the same rules and make the changes directly.

Example output:

### Destination.swift

**Line 8: Add an explicit delete rule and inverse for relationships.**

```swift
// Before
var sights: [Sight]

// After
@Relationship(deleteRule: .cascade, inverse: \Sight.destination) var sights: [Sight]
```

**Line 22: Do not use `isEmpty == false` in predicates – it crashes at runtime. Use `!` instead.**

```swift
// Before
#Predicate<Destination> { $0.sights.isEmpty == false }

// After
#Predicate<Destination> { !$0.sights.isEmpty }
```

### Summary

1. **Data loss (high):** Missing delete rule on line 8 of Destination.swift leaves sights orphaned when a destination is deleted.
2. **Crash (high):** `isEmpty == false` on line 22 crashes at runtime – use `!isEmpty` instead.

End of example.


## References

- `references/core-rules.md` – saving, relationships, delete rules, property restrictions, fetch optimization.
- `references/predicates.md` – supported and crashing predicates, captured values, dynamic queries.
- `references/context-and-actors.md` – container setup, context roles, saving, undo, stores, `@ModelActor`, identity.
- `references/cloudkit.md` – CloudKit schema rules, eventual consistency, duplicates, schema evolution, setup.
- `references/migrations.md` – lightweight changes, `VersionedSchema`, `SchemaMigrationPlan`, testing migrations.
- `references/widgets-and-history.md` – app group store, widgets, App Intents, persistent history (iOS 18+).
- `references/indexing.md` – `#Index` (iOS 18+).
- `references/class-inheritance.md` – model subclassing (iOS 26+).
- `references/testing.md` – in-memory fixtures, store and `@ModelActor` tests.
- `references/troubleshooting.md` – symptoms, SwiftData errors, debug sequence.
