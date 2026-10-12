# Sources

| Upstream | Commit | Date |
| --- | --- | --- |
| [twostraws/SwiftData-Agent-Skill](https://github.com/twostraws/SwiftData-Agent-Skill) – SwiftData Pro 1.0 | `922d989` | 2026-03-11 |
| [vanab/swiftdata-agent-skill](https://github.com/vanab/swiftdata-agent-skill) – SwiftData Expert | `4819a53` | 2026-02-08 |
| [akshaypimprikar/ios-swiftdata-testing-agent-skill](https://github.com/akshaypimprikar/ios-swiftdata-testing-agent-skill) – SwiftData Testing | `e8a9875` | 2026-07-19 |
| Apple: "Syncing model data across a person's devices", "Fetching and filtering time-based model changes", SwiftData API reference | – | checked 2026-10-12 |

Check for updates:

```bash
git clone https://github.com/twostraws/SwiftData-Agent-Skill && git -C SwiftData-Agent-Skill diff 922d989 HEAD -- swiftdata-pro
git clone https://github.com/vanab/swiftdata-agent-skill && git -C swiftdata-agent-skill diff 4819a53 HEAD
git clone https://github.com/akshaypimprikar/ios-swiftdata-testing-agent-skill && git -C ios-swiftdata-testing-agent-skill diff e8a9875 HEAD
```


## File map

| File | Source | Changes |
| --- | --- | --- |
| `SKILL.md` | Hudson `SKILL.md`; project intake and search commands from Kudrin | Step 0 with CloudKit / app group / migration detection (globs quoted for zsh); MV rules; five modes; output format kept |
| `references/core-rules.md` | Hudson + condensed notes from Kudrin (`model-context-and-lifecycle.md`, `concurrency-and-actors.md`) and Pimprikar (fixtures, `@ModelActor` tests) | Hudson's rules unchanged except links and the CloudKit gate on uniqueness; new section "Containers, contexts, and tests" replaces the former `context-and-actors.md`, `testing.md`, and `troubleshooting.md` |
| `references/predicates.md` | Hudson + Kudrin `querying-and-fetching.md` | Added: capture values outside predicates, dynamic `@Query` in `init`, shared predicate helpers |
| `references/indexing.md`, `class-inheritance.md` | Hudson | Unchanged |
| `references/cloudkit.md` | Hudson `cloudkit.md` + Kudrin `cloudkit-sync.md` + Apple docs | Hudson's rules kept; setup from Apple; new sections on eventual consistency, deterministic deduplication, additive-only evolution |
| `references/migrations.md` | Kudrin `migrations-and-history.md` + Apple docs + Pimprikar's in-memory gotcha | Full `VersionedSchema` / plan example; `static let` version identifiers for strict concurrency; CloudKit pointer |
| `references/widgets-and-history.md` | Kudrin history notes + Apple "Fetching and filtering time-based model changes" | App group factory, widgets, App Intents, iOS 17 fallback; history types use API-reference names (`DefaultHistoryTransaction`, `HistoryChange`, `changedPersistentIdentifier`), not the article's older beta names; migrator-authored history transactions (found by testing) |


## Deliberately not included

- Kudrin: Core Data adoption and coexistence; implementation playbooks; the "duplicates → add `@Attribute(.unique)`" advice without a CloudKit caveat; the model example with both `#Unique` and `@Attribute(.unique)` and a UI flag stored in the model; `.now` called inside `#Predicate`.
- Pimprikar: mock-repository pattern for view-model tests (MVVM); `Decimal` money values and import-hash deduplication (specific to one finance app); the claim that SwiftData never infers related models (disproved – see below).


## Verified on 2026-10-12

Checked by compiling (Swift 6 language mode) and running small SwiftData programs on macOS with Xcode 26.6:

- `$0.endDate < Date.now` inside `#Predicate` **does not compile**; a captured `let now = Date.now` works. (Kudrin's example is wrong.)
- `$0.stops.isEmpty == false` compiles but **crashes at runtime** with an `NSException`; `!$0.stops.isEmpty` works. (Hudson's rule confirmed.)
- `ModelContainer(for: Trip.self)` **includes `Stop`**, reachable only through a relationship. (Pimprikar's claim that relationships are not walked is wrong; the skill still recommends listing every model.)
- A migration plan on an in-memory store: **no failures** in 600 saves with a single-version plan. Pimprikar's report was not reproduced; the skill keeps the harmless "skip the plan in memory" branch with softened wording.
- The `migrations.md` example (two `VersionedSchema`s, custom stage, container with plan) **compiles and migrates** a real V1 store file to V2; `didMigrate` fills the new field.
- `static var versionIdentifier` **fails** strict concurrency checking (error); `static let` works. A `static let` migration stage compiles fine too (an earlier claim that it does not was removed).
- The `widgets-and-history.md` history code **compiles and works**: author filtering, `DefaultHistoryUpdate<Trip>` casting, `changedPersistentIdentifier`, JSON token round-trip, "after token" returns nothing new.
- **New finding:** a schema migration writes history transactions authored by `com.apple.coredata.schemamigrator: …`, so `author != "app"` filters pick them up.

Deliberately removed in the slimming pass (models already know this, or `DocumentationSearch` covers it): the separate `context-and-actors.md`, `testing.md`, and `troubleshooting.md` files; their non-obvious points live in `core-rules.md`.
