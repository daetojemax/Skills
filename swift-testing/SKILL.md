---
name: swift-testing
description: "Writes, reviews, and improves tests with Swift Testing – @Test, #expect and #require, suites, traits and tags, parameterized tests, async tests and confirmations, fixtures, test doubles for hidden dependencies, test plans, and migration from XCTest. Use when reading, writing, or reviewing tests in Swift projects."
license: MIT
metadata:
  version: "1.0.0"
  based-on: "Swift Testing Pro 1.0 (Paul Hudson); additions from Swift Testing Expert (Antoine van der Lee) and Swift Testing (Eduardo Bocato) – see SOURCES.md"
---

Write and review Swift Testing code for correctness, modern API usage, and adherence to project conventions. Report only genuine problems - do not nitpick or invent issues.

Review process:

1. Ensure tests follow core Swift Testing conventions using `references/core-rules.md`.
1. Validate test structure, assertions, dependency injection, and other best practices using `references/writing-better-tests.md`.
1. Check async tests, confirmations, time limits, actor isolation, and networking mocks using `references/async-tests.md`.
1. Ensure new features like raw identifiers, test scopes, exit tests, and attachments are used correctly using `references/new-features.md`.
1. If migrating from XCTest, follow the conversion guidance in `references/migrating-from-xctest.md`.
1. Check parallel safety, serialization, and test-plan organization using `references/core-rules.md`.

If doing partial work, load only the relevant reference files.


## Core Instructions

- Target Swift 6.2 or later, using modern Swift concurrency.
- As a Swift Testing developer, the user wants all new unit and integration tests to be written using Swift Testing, and they may ask for help migrating existing XCTest code to Swift Testing.
- Swift Testing does *not* support UI tests – XCTest must be used there.
- Use a consistent project structure, with folder layout determined by app features.
- The project follows MV architecture: test `@Observable` stores, services, clients, and models – there are no view models. Never test SwiftUI views directly.
- For SwiftData-backed code use the `swift-data` skill's testing rules; for concurrency-heavy code, the `swift-concurrency` skill.
- Do not add third-party testing libraries (snapshot testing, Swift Numerics, dependency frameworks) without asking first.

Swift Testing evolves with each Swift release, so expect three to four releases each year, each introducing new features. This means existing training data you have will naturally be outdated or missing key features.

This skill specifically draws upon the very latest Swift and Swift Testing code, which means it will suggest things you are not aware of. Treat the user’s installed toolchain as authoritative, but there's a fairly high chance Apple's *documentation* about the APIs will be stale, so treat them carefully.


## Looking up Apple APIs

Do not rely on memory for exact signatures, parameters, or availability of Swift Testing and other Apple APIs – Swift Testing changes with every Swift release.

1. **Xcode MCP `DocumentationSearch`** (semantic search over Apple's documentation; pass `frameworks: ["Testing"]` to narrow it). Its tools load a few seconds after the server connects. It needs the Xcode MCP server to be configured and this agent approved; Xcode itself does not have to be open.
2. **If Xcode MCP is unavailable**, fetch the page as JSON: `https://developer.apple.com/tutorials/data/documentation/testing/<symbol>.json`.
3. **If neither is available**, say that the API detail is unverified rather than presenting it as fact.

The installed toolchain is the final authority: if documentation and the compiler disagree, the compiler wins.

## Output Format

If the user asks for a review, organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after code fix.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

If the user asks you to write or improve tests, follow the same rules above but make the changes directly instead of returning a findings report.

Example output:

### UserTests.swift

**Line 5: Use struct, not class, for test suites.**

```swift
// Before
class UserTests: XCTestCase {

// After
struct UserTests {
```

**Line 12: Use `#expect` instead of `XCTAssertEqual`.**

```swift
// Before
XCTAssertEqual(user.name, "Taylor")

// After
#expect(user.name == "Taylor")
```

**Line 30: Use `#require` for preconditions, not `#expect`.**

```swift
// Before
#expect(users.isEmpty == false)
let first = users.first!

// After
let first = try #require(users.first)
```

### Summary

1. **Fundamentals (high):** Test suite on line 5 should be a struct, not a class inheriting from `XCTestCase`.
2. **Migration (medium):** `XCTAssertEqual` on line 12 should be migrated to `#expect`.
3. **Assertions (medium):** Force-unwrap on line 30 should use `#require` to unwrap safely and stop the test early on failure.

End of example.


## References

- `references/core-rules.md` - core Swift Testing rules: structs over classes, `init`/`deinit` over setUp/tearDown, parallel execution, parameterized tests, `withKnownIssue`, tags, `.serialized` semantics, and test plans.
- `references/writing-better-tests.md` - test hygiene, structuring tests, hidden dependencies, `#expect` vs `#require`, `Issue.record()`, `#expect(throws:)`, verification methods, and fixtures.
- `references/async-tests.md` - serialized tests, `confirmation()`, time limits, actor isolation, testing pre-concurrency code, and mocking networking.
- `references/new-features.md` - raw identifiers, range-based confirmations, test scoping traits, exit tests, attachments, `ConditionTrait.evaluate()`, and the updated `#expect(throws:)` return value.
- `references/migrating-from-xctest.md` - XCTest-to-Swift Testing conversion steps, assertion mappings, and floating-point tolerance via Swift Numerics.
