# Sources

| Upstream | Commit | Date |
| --- | --- | --- |
| [twostraws/Swift-Testing-Agent-Skill](https://github.com/twostraws/Swift-Testing-Agent-Skill) – Swift Testing Pro 1.0 | `2d6bba1` | 2026-05-17 |
| [AvdLee/Swift-Testing-Agent-Skill](https://github.com/AvdLee/Swift-Testing-Agent-Skill) – Swift Testing Expert | `798e9b1` | 2026-04-22 |
| [bocato/swift-testing-agent-skill](https://github.com/bocato/swift-testing-agent-skill) – Swift Testing | `c2dd1b0` | 2026-01-28 |

Check for updates:

```bash
git clone https://github.com/twostraws/Swift-Testing-Agent-Skill && git -C Swift-Testing-Agent-Skill diff 2d6bba1 HEAD -- swift-testing-pro
```


## File map

| File | Source | Changes |
| --- | --- | --- |
| `SKILL.md` | Hudson | Renamed; MV, local-skill, and third-party-library rules; "Looking up Apple APIs"; review step for parallel safety |
| `references/core-rules.md` | Hudson + van der Lee (`parallelization-and-isolation.md`, `xcode-workflows.md`, `migration-from-xctest.md`) | `!` rule now explains the actual problem (inverted values in failure reports); new section on parallelism, `.serialized` semantics, `@MainActor` cost, XCTest for UI and `XCTMetric`, tags and test plans |
| `references/writing-better-tests.md` | Hudson + Bocato (`fixtures.md`) | View models → MV stores; links → local skills; new "Fixtures" section (factory with defaults, fixed values, placement) |
| `references/async-tests.md` | Hudson | View-model examples → stores and a loader; `.serialized` wording clarified; link → `swift-concurrency` |
| `references/new-features.md`, `migrating-from-xctest.md` | Hudson | Unchanged |


## Verified on 2026-10-12

Compiled and run with Xcode 26.6's toolchain (`TOOLCHAINS=com.apple.dt.toolchain.XcodeDefault xcrun swift test` – the machine's default `swift` is a separate swiftly toolchain that cannot import Xcode's Testing module):

- **`.timeLimit(.seconds(5))` does not compile** ("'seconds' is unavailable: Time limit must be specified in minutes"). Hudson is right; van der Lee's and Bocato's examples are wrong.
- **`.serialized` on a suite serializes all contained tests**, parameterized or not: three 0.4 s tests in a serialized suite ran back to back (1.25 s), the same tests without it ran concurrently (0.43 s). Matches Apple's `ParallelizationTrait` docs and Hudson's Swift Testing Pro. Hudson's Swift Concurrency Pro claimed the opposite; that error was corrected in the `swift-concurrency` skill.
- **`#expect(!x)`**: the macro does expand negation, but the failure report shows inverted values (`user.isLoggedIn → false` when it is `true`); `#expect(x == false)` reports the real values. Hudson's rule holds, with a corrected reason.
- **All 11 examples in `new-features.md` compile and pass**: raw identifiers (plain and parameterized), range-based confirmations, test scoping traits with `@TaskLocal`, exit tests, attachments, `ConditionTrait.evaluate()`, typed `#expect(throws:)` return value, `withKnownIssue(isolation:)`, tags with `.bug(id:)`, and verification methods with `#_sourceLocation`.


## Deliberately not included

- Bocato: fixtures and test doubles placed in production code by default (kept only as an option for preview-shared fixtures); sleep-based tests for debouncing and cancellation; mutation of captured `var`s from async closures (rejected by Swift 6); `XCTFail` inside Swift Testing doubles; Point-Free dependencies (swift-snapshot-testing, swift-dependencies, XCTestDynamicOverlay); `#expect(!…)`; the full Fowler test-double taxonomy.
- van der Lee: `.timeLimit(.seconds(…))`; reference material that largely repeats Hudson (fundamentals, expectations, parameterized testing).
