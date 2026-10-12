# Sources

| Upstream | Commit | Date |
| --- | --- | --- |
| [twostraws/Swift-Concurrency-Agent-Skill](https://github.com/twostraws/Swift-Concurrency-Agent-Skill) – Swift Concurrency Pro 1.0 | `bee3f69` | 2026-05-17 |
| [AvdLee/Swift-Concurrency-Agent-Skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill) – swift-concurrency | `d577081` | 2026-09-14 |

Check for updates:

```bash
git clone https://github.com/twostraws/Swift-Concurrency-Agent-Skill && git -C Swift-Concurrency-Agent-Skill diff bee3f69 HEAD -- swift-concurrency-pro
git clone https://github.com/AvdLee/Swift-Concurrency-Agent-Skill && git -C Swift-Concurrency-Agent-Skill diff d577081 HEAD -- skills/swift-concurrency/SKILL.md skills/swift-concurrency/references/observation.md
```


## File map

| File | Source | Changes |
| --- | --- | --- |
| `SKILL.md` | Hudson `SKILL.md`; Step 0 settings table and tool-selection idea from van der Lee `SKILL.md` | Step 0 with detection commands; MV and "stay on the caller's actor" core rules; three modes (fix errors, review, write); output format kept |
| `references/new-features.md` | Hudson | **Corrected:** caller-actor async behavior (SE-0461) is gated by `NonisolatedNonsendingByDefault` / Approachable Concurrency, not by the compiler version alone |
| `references/bug-patterns.md` | Hudson | Same SE-0461 correction |
| `references/cancellation.md` | Hudson | `ViewModel` → `@MainActor` store; `deinit` → `isolated deinit` with fallback; prefer `.task(id:)` in SwiftUI |
| `references/testing.md` | Hudson | `ViewModel` examples → stores; Swift Testing Pro link removed; **corrected** `.serialized` on a suite: it serializes all contained tests, not only parameterized ones (verified by running tests on 2026-10-12, matches Apple's `ParallelizationTrait` docs and Hudson's own Swift Testing Pro) |
| `references/actors.md` | Hudson | SwiftUI Pro link → `swift-ui` |
| `references/diagnostics.md` | Hudson + van der Lee `SKILL.md` diagnostics table | Added: main-actor from nonisolated context, `SendableMetatype`, `Thread.current`, XCTest `wait`, SwiftLint `async_without_await`, `@Observable` pointer |
| `references/observation.md` | van der Lee `observation.md` | Rewritten for MV stores: `@concurrent` helper instead of `Task.detached`; no `MainActor.run` hops for I/O; background-actor `@Observable` discouraged for views; `Observations` example without swift-async-algorithms; ObservableObject migration table dropped |
| `references/hotspots.md`, `structured.md`, `unstructured.md`, `async-streams.md`, `bridging.md`, `interop.md` | Hudson | Unchanged |


## Deliberately not included

- van der Lee's "task entry isolation" rule (`Task { @concurrent in … }` + `await MainActor.run { … }` for network calls). It conflicts with the MV store pattern and with Hudson's guidance: awaiting I/O does not block the main actor, and the extra hops add Sendable friction.
- van der Lee's `migration.md` (Swift 6 migration) – not needed.
- van der Lee's other references (actors, sendable, tasks, threading, async-sequences, async-algorithms, core-data, memory-management, performance, linting, glossary) – largely overlap with Hudson's files or target topics outside this user's stack. Revisit `memory-management.md` if retain cycles in long-lived tasks become a recurring issue.
- Thomas Ricouard's `swift-concurrency-expert` – fully covered by the files above.
