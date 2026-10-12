# Troubleshooting

## Symptom → first check

| Symptom | First check |
| --- | --- |
| Inserts fail, fetches always empty | Is a `ModelContainer` attached for this code path, and does its schema include the model? |
| Data missing after relaunch | Was the context saved? Is the app opening a different store (app group added later, different configuration name, in-memory flag)? |
| Crash when a query runs | Predicate uses something unsupported at runtime: `== false` on a Boolean expression, computed or `@Transient` properties, regular expressions, `Codable` struct contents (see `predicates.md`) |
| Orphaned records after delete | Missing or wrong delete rule (`core-rules.md`) |
| Everything of a type disappeared | `delete(model:where:)` without a predicate, or a too-broad one |
| Duplicates appear | CloudKit: expected without dedup (`cloudkit.md`). Without CloudKit: missing `#Unique` / `@Attribute(.unique)`, which makes inserts with an existing key update the stored record instead |
| Undo does nothing | Undo not enabled, or the change was made in a background context |
| Widget or intent changes not visible in the app | Did the extension save? Does the app catch up on activation (`widgets-and-history.md`)? |
| Sync does nothing | Capabilities, remote notifications, container selection, schema initialized and promoted (`cloudkit.md`) |
| App fails to open the store after an update | Migration path broken – see errors below and `migrations.md` |
| Data race or isolation errors around models | A `@Model` or `ModelContext` crossed actors (`context-and-actors.md`) |


## SwiftData errors

| Error | Meaning |
| --- | --- |
| `missingModelContext` | No valid container or context for this code path |
| `modelValidationFailure` | A model violates schema constraints at save time (for example, a required relationship is missing) |
| `unsupportedPredicate` / `unsupportedSortDescriptor` | The expression cannot be evaluated by the store – simplify it to stored properties and supported operations |
| `includePendingChangesWithBatchSize` | `includePendingChanges` combined with a batch size in one `FetchDescriptor` – not allowed |
| `historyTokenExpired` | The history token points to transactions that were already deleted – reset the token |
| `unknownSchema` / `backwardMigration` | The stored schema version is not in the migration plan, or the plan cannot reach the current version |


## Debug sequence

1. Confirm container wiring and the schema list.
2. Confirm the deployment target supports the APIs in use (Step 0 in `SKILL.md`).
3. Reproduce with a minimal `FetchDescriptor` – no predicate, no sort – then add conditions back one at a time.
4. Check save boundaries: what is saved, when, and by which context.
5. Check delete rules and delete predicates.
6. With CloudKit: check the configuration and test on two devices.
7. With history: check how tokens are loaded, stored, and cleaned up.
