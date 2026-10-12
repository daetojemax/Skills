# Diagnostics

Maps common strict-concurrency compiler errors to likely fixes.

## "Sending 'x' risks causing data races"

The compiler found a value crossing an isolation boundary where it could still be accessed from the sending side.

Likely fixes (try in order):

1. **Check whether region-based isolation already handles it.** If the sender demonstrably stops using the value after passing it, the compiler may accept it without changes. Avoid adding `Sendable` prematurely.
2. **Mark the parameter `sending`.** This tells the compiler the caller transfers ownership and won't touch the value afterward. (This can be useful, but is not that common.)
3. **Make the type `Sendable`** if it genuinely can be shared safely (value type, immutable class, or internally synchronized).
4. **Check whether `nonisolated(nonsending)` resolves it.** If the function no longer hops executors, the value may not actually cross a boundary.
5. **Last resort: `@unchecked Sendable`** only if the type uses manual synchronization (locks) and you've verified correctness. See `bridging.md`.


## "Static property 'x' is not concurrency-safe"

A global or static variable is accessible from multiple isolation domains with no protection.

Likely fixes:

1. **Annotate the declaration with `@MainActor`**: `@MainActor static let shared = MyType()`. This is the simplest code-local fix.
2. **If the value is truly constant and immutable**, consider whether it can conform to `Sendable` (e.g., a `let`-only struct). The compiler won't flag `Sendable` constants.
3. **Use `nonisolated(unsafe)`** only for genuinely immutable state where the compiler can't prove safety (e.g., C interop constants). This is a dangerous tool, and misuse will hide real races.
4. **If the entire module is predominantly single-threaded**, default main-actor isolation may explain why similar declarations behave differently in another target. That's a build-setting difference, not a code fix.


## "Capture of 'x' with non-sendable type in a `@Sendable` closure"

A closure that crosses isolation boundaries (e.g., passed to `Task {}`, `Task.detached {}`, or `addTask`) captures a non-Sendable value.

Likely fixes:

1. **Check whether the captured value can be made `Sendable`.** Structs and enums with only `Sendable` stored properties just need the conformance declared. Final classes with immutable (`let`) stored properties can conform too.
2. **Restructure to avoid the capture.** Pass the needed data as a parameter to the task rather than closing over a large non-Sendable object. For example, `let id = object.id; Task { use(id) }`
3. **Move the work onto the same actor.** If the closure doesn't need to run concurrently, keep it on the caller's actor.
4. **Use `sending` on the parameter** if you can transfer ownership cleanly. This is relatively niche.

It’s tempting to reach for `@unchecked Sendable`, but rarely a good idea unless the user is *absolutely certain* their code is safe.


## "Conformance of 'X' to protocol 'Y' crosses into main actor-isolated code and can cause data races"

The protocol and the type describe different call boundaries. Fix the boundary mismatch directly:

| Actual requirement | Shape to use |
|---|---|
| Type-level actor isolation is incidental rather than required | Remove the type isolation. See `actors.md`. |
| The conformance should only be usable on `MainActor` | `extension MyType: @MainActor SomeProtocol {}` |

These are different boundary choices, not interchangeable suppressions.


## "Expression is 'async' but is not marked with 'await'"

A call crosses an isolation boundary and requires an async hop. This often surprises when calling actor-isolated methods from outside the actor, or when accessing `@MainActor` state from a non-isolated context.

Likely fix: Add `await`. If the call is in synchronous code that cannot be made async, wrap it in `Task {}` (but see `unstructured.md` for when that's appropriate).


## "Main actor-isolated conformance of 'X' to 'Y' cannot be used in nonisolated context"

An isolated conformance (e.g., `extension X: @MainActor Y`) is being used from code that doesn't share that isolation. The compiler prevents this because calling the protocol methods off-actor would be a data race.

Likely fixes:

1. **Move the use site onto the same actor.** If the consuming code can be `@MainActor`, the conformance is usable.
2. **Remove the isolation from the conformance** if the protocol methods don't actually need actor-protected state.


## "Main actor-isolated 'x' cannot be used from a nonisolated context"

Code that is not on the main actor touches main-actor state synchronously.

Likely fixes:

1. **Ask whether the caller is genuinely UI-bound.** If it is, isolate the caller (function or type) to `@MainActor`. Do not apply `@MainActor` as a blanket fix to code that is not UI-related.
2. **If the caller is async and must stay off the main actor**, `await` the main-actor member, or move the main-actor part into a `@MainActor` method and `await` that.
3. **Check the target's default isolation.** In a main-actor-by-default module, a `nonisolated` annotation may be what made this code leave the main actor.

Prefer an `@MainActor` function over `await MainActor.run { }`; reach for `MainActor.run` only when a small block inside otherwise non-isolated code must touch main-actor state (see `hotspots.md`).


## "… cannot satisfy conformance requirement for a 'Sendable' type parameter" (`SendableMetatype`)

A type's conformance is isolated to a global actor (for example, `extension Item: @MainActor Codable`), and its metatype is being passed somewhere that requires `SendableMetatype` – often a generic function that may use the conformance from another isolation domain.

Likely fixes:

1. **Remove the actor isolation from the conformance** if the protocol requirements do not actually need actor-protected state. Value types with plain stored properties rarely need an isolated conformance.
2. **Keep the metatype within the same isolation domain** – do not pass it across actors or into concurrently executing generic code.


## "Class property 'current' is unavailable from asynchronous contexts" (`Thread.current`)

Swift 6 forbids `Thread.current` in async code, because tasks are not tied to threads.

Fix: reason in terms of isolation, not threads. Use `MainActor.assertIsolated()` / `assumeIsolated()` for checks, and Instruments or the debugger to observe execution. Do not route around the restriction.


## "Instance method 'wait(for:timeout:)' is unavailable from asynchronous contexts"

Legacy XCTest waiting inside an `async` test.

Fix: in XCTest, use `await fulfillment(of: [expectation], timeout: …)`. In Swift Testing, await the real work or use `confirmation()` (see `testing.md`). Never add sleeps.


## SwiftLint `async_without_await`

A function is marked `async` but never awaits.

Fix: remove `async` unless a protocol requirement, an override, or `@concurrent` requires it. If `async` must stay, use a narrow, documented suppression. Never add a fake `await` (such as `await Task.yield()`) just to satisfy the linter.


## `@Observable` isolation and Sendable errors

Errors such as "Capture of non-sendable type 'MyStore' in a `@Sendable` closure" or "Sending value of non-Sendable type 'MyStore'" usually mean an `@Observable` class has no isolation, or is being passed across an isolation boundary. See `observation.md`.
