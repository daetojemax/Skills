---
name: swift-concurrency
description: Writes, reviews, and fixes Swift concurrency code – async/await, tasks and task groups, actors and reentrancy, @MainActor, Sendable, cancellation, continuations, AsyncStream, @Observable stores across actors, and async tests. Use when writing or reviewing concurrent Swift code, or when fixing strict-concurrency compiler errors and data-race diagnostics.
license: MIT
metadata:
  version: "1.0.0"
  based-on: "Swift Concurrency Pro 1.0 (Paul Hudson); Swift Concurrency skill (Antoine van der Lee) – see SOURCES.md"
---

# Swift Concurrency

Write and review Swift concurrency code for correctness first: no data races, no lost errors, no leaked or uncancellable work, and no unnecessary hops. Report only genuine problems – do not nitpick or invent issues.


## Step 0: Check the project's concurrency settings

Where code runs depends on build settings, not only on the code. Establish them before diagnosing or advising, every time – not just for migrations.

```bash
xcodebuild -version
grep -rhoE "(SWIFT_VERSION|SWIFT_STRICT_CONCURRENCY|SWIFT_DEFAULT_ACTOR_ISOLATION|SWIFT_APPROACHABLE_CONCURRENCY|SWIFT_UPCOMING_FEATURE_[A-Z_]+) = [A-Za-z0-9.]+" --include=project.pbxproj . | sort -u
grep -hoE "swiftLanguageModes?:[^]]*\]|defaultIsolation\([A-Za-z.]+\)|enable(Upcoming|Experimental)Feature\(\"[A-Za-z=]+\"\)" Package.swift 2>/dev/null
```

| Setting | Xcode (`.pbxproj`) | SwiftPM (`Package.swift`) | Why it matters |
| --- | --- | --- | --- |
| Language mode | `SWIFT_VERSION` | `swiftLanguageModes` (`swift-tools-version` is not a reliable proxy) | Swift 6 mode makes data-race diagnostics errors |
| Strict concurrency | `SWIFT_STRICT_CONCURRENCY` | `.enableExperimentalFeature("StrictConcurrency=…")` | How much is checked in Swift 5 mode |
| Default isolation | `SWIFT_DEFAULT_ACTOR_ISOLATION` | `.defaultIsolation(MainActor.self)` | Main-actor-by-default makes `@MainActor` implicit |
| Approachable Concurrency | `SWIFT_APPROACHABLE_CONCURRENCY` | individual upcoming features | Bundles several upcoming features, including the one below |
| Caller-actor async | `SWIFT_UPCOMING_FEATURE_NONISOLATED_NONSENDING_BY_DEFAULT` | `.enableUpcomingFeature("NonisolatedNonsendingByDefault")` | Whether `nonisolated async` functions stay on the caller's actor (see `references/new-features.md`) |

- New Xcode 26+ app projects usually start with main-actor default isolation and Approachable Concurrency enabled – treat that as likely, never as confirmed.
- Settings are per target and per package: compare them before assuming two modules behave alike.
- If settings cannot be read (a snippet without a project), ask before giving isolation-sensitive advice.


## Core instructions

- Target Swift 6.2 or later with strict concurrency checking.
- The user's apps use MV architecture: views plus `@MainActor @Observable` stores, services, and clients. Do not introduce view models; express fixes in terms of stores, services, and actors (see `references/observation.md`).
- **Stay on the caller's actor by default.** Awaiting I/O does not block the main actor. Offload only CPU-heavy work, with `@concurrent` on a `nonisolated` function. Do not wrap ordinary async calls in `Task.detached`, `Task { @concurrent in … }`, or `MainActor.run`.
- Do not apply `@MainActor` as a blanket fix; justify why the code is UI-bound. Equally, do not move UI-bound state off the main actor.
- Prefer structured concurrency (`async let`, task groups) over unstructured `Task {}`. In SwiftUI, prefer `.task` / `.task(id:)` over stored tasks or `Task {}` in `onAppear`.
- Prefer Swift concurrency over GCD for new code. GCD remains acceptable in low-level code, framework interop, or performance-critical synchronous sections where queues or locks are the right tool – do not flag those as errors.
- If an API offers both `async`/`await` and closure-based variants, prefer `async`/`await`.
- Do not introduce third-party concurrency packages (including swift-async-algorithms) without asking first.
- Do not suggest `@unchecked Sendable`, `nonisolated(unsafe)`, or `@preconcurrency` to silence errors. If one is truly required, state the safety invariant that makes it correct and how it could later be removed. Prefer actors, value types, `Mutex`, or `sending` parameters.
- Make the smallest safe change. Do not refactor unrelated architecture while fixing concurrency.
- For SwiftUI questions use the `swift-ui` skill; for SwiftData, `swiftdata-pro`.


## Modes

### Fixing compiler errors

1. Step 0.
2. Capture the exact diagnostic and the offending symbol.
3. Identify the isolation boundary being crossed: `@MainActor`, a custom actor, actor-instance isolation, or `nonisolated`.
4. Map the diagnostic to a fix with `references/diagnostics.md`; for `@Observable` stores, `references/observation.md`.
5. Rebuild. Fix one category of errors at a time, and treat any new diagnostic as a fresh triage. Run the tests – a clean build does not prove the absence of behavioral changes.

### Reviewing code

1. Step 0.
2. Scan for known-dangerous patterns with `references/hotspots.md` to prioritize what to inspect.
3. Check Swift 6.2 behavior with `references/new-features.md`.
4. Validate actor reentrancy and isolation with `references/actors.md`.
5. Check that structured concurrency is preferred where appropriate with `references/structured.md`, and unstructured tasks with `references/unstructured.md`.
6. Verify cancellation with `references/cancellation.md`.
7. Validate streams and continuations with `references/async-streams.md` and `references/bridging.md`.
8. Review legacy interop with `references/interop.md`.
9. Check `@Observable` stores with `references/observation.md`.
10. Cross-check common failure modes with `references/bug-patterns.md`.
11. If reviewing tests, use `references/testing.md`.

For a partial review, load only the relevant references.

### Writing new code

Choose the tool by need:

| Need | Tool |
| --- | --- |
| One async operation | `async`/`await` |
| A fixed set of parallel operations | `async let` |
| A dynamic number of parallel operations | `withTaskGroup` / `withThrowingTaskGroup` (`withDiscardingTaskGroup` for side effects) |
| Starting async work from a SwiftUI view | `.task` / `.task(id:)` |
| Starting async work from a synchronous action | `Task { }` – inherits the caller's actor; handle its errors inside |
| State that views read | `@MainActor @Observable` store |
| Shared mutable state off the main actor | `actor`; or `Mutex` when the API must stay synchronous |
| CPU-heavy work | `@concurrent` function on a `nonisolated` type |
| Callback API → async | `withCheckedThrowingContinuation`, resumed exactly once |
| Multi-value callbacks or delegates → async | `AsyncStream.makeStream(of:)` with a buffering policy |


## Output format

Organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after code fix.
4. If the fix depends on a build setting from Step 0, say so.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

Example output:

### DataLoader.swift

**Line 18: Actor reentrancy – state may have changed across the `await`.**

```swift
// Before
actor Cache {
    var items: [String: Data] = [:]

    func fetch(_ key: String) async throws -> Data {
        if items[key] == nil {
            items[key] = try await download(key)
        }
        return items[key]!
    }
}

// After
actor Cache {
    var items: [String: Data] = [:]

    func fetch(_ key: String) async throws -> Data {
        if let existing = items[key] { return existing }
        let data = try await download(key)
        items[key] = data
        return data
    }
}
```

**Line 34: Use `withTaskGroup` instead of creating tasks in a loop.**

```swift
// Before
for url in urls {
    Task { try await fetch(url) }
}

// After
try await withThrowingTaskGroup(of: Data.self) { group in
    for url in urls {
        group.addTask { try await fetch(url) }
    }

    for try await result in group {
        process(result)
    }
}
```

### Summary

1. **Correctness (high):** Actor reentrancy bug on line 18 may cause duplicate downloads and a force-unwrap crash.
2. **Structure (medium):** Unstructured tasks in a loop on line 34 lose cancellation propagation.

End of example.


## References

- `references/hotspots.md` – grep targets: known-dangerous patterns and what to check for each.
- `references/new-features.md` – Swift 6.2: default isolation, isolated conformances, caller-actor async (and the setting that gates it), `@concurrent`, `Task.immediate`, isolated deinit, task naming, priority escalation.
- `references/actors.md` – reentrancy, global and static state, global actor inference, `isolated` parameters, assertions.
- `references/structured.md` – `async let` vs task groups, discarding groups, limiting concurrency, partial results.
- `references/unstructured.md` – `Task` vs `Task.detached`, when `Task {}` is a smell.
- `references/cancellation.md` – propagation, cooperative checks, cancellation handlers, broken patterns.
- `references/async-streams.md` – `makeStream(of:)`, continuation lifecycle, buffering.
- `references/bridging.md` – checked continuations, delegate wrapping, runtime actor assertions, `@unchecked Sendable`.
- `references/interop.md` – wrapping completion handlers, delegates, GCD, locks and `Mutex`, Combine.
- `references/observation.md` – `@Observable` stores with actors: isolation, offloading, snapshots, `Observations`.
- `references/bug-patterns.md` – common concurrency failure modes and fixes.
- `references/diagnostics.md` – compiler errors mapped to fixes.
- `references/testing.md` – async tests with Swift Testing, confirmations, cancellation tests, TSan.
