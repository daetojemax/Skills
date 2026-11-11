# Performance audit

Use this when the user reports a concrete performance problem – janky or stuttering scrolling, hangs, slow navigation or typing, high CPU, battery drain, memory growth, excessive view updates – or asks for a deep performance review. Routine reviews use `performance.md` only.

Diagnose from code first, ask for profiling evidence when code cannot explain the symptom, separate suspicion from proof, and verify every fix with the same measurement. Fixes stay within MV: narrow what views observe and restructure views and stores – never add view models to "fix" performance.


## 1. Intake

Classify the symptom first:

- janky scrolling or dropped frames (hitches);
- hangs or unresponsive interactions;
- high CPU or battery drain;
- memory growth or image pressure;
- excessive or unexpectedly broad view updates.

Collect:

- the target view or feature code, and its data flow: `@State`, `@Binding`, environment dependencies, observable stores;
- the exact interaction and reproduction steps;
- device or Simulator, Debug or Release, OS version, deployment target (Step 0 in `SKILL.md`).

Debug builds and the Simulator distort SwiftUI timing and allocation; conclusions about smoothness need a Release build on a device.


## 2. Code-first review

Review the code against `performance.md`, then `performance-plus.md` for observation fan-out. Triage in this order – it reflects typical impact:

1. **Broad invalidation and observation fan-out** – many views reading one large observable collection, computed properties on observable types (they subscribe to everything the getter reads), whole structs stored as one dependency, fast-changing values in the environment.
2. **Unstable identity and list churn** – `id: \.self` on mutable data, index or offset identity, IDs generated during `body`, rows whose top-level shape varies.
3. **Main-thread work during render** – sorting, filtering, formatting, allocation in `body` or view initializers.
4. **Image decode and resize cost** – full-size images in rows, decoding on the main actor.
5. **Layout and animation complexity** – `GeometryReader` and preference chains, top-level branch swapping, `View.if()` helpers, animations applied too broadly.

Debugging aids to suggest:

- `let _ = Self._printChanges()` at the top of a suspect `body` (Debug only) prints which dependency triggered the update.
- The launch argument `-LogForEachSlowPath YES` logs `ForEach` instances whose rows vary in shape.

For each finding give the likely cause with a code reference, the specific fix, and – where useful – a minimal repro or instrumentation step.


## 3. Profiling with Instruments

When code review is inconclusive, get runtime evidence. To record and read traces yourself from the command line (Time Profiler, hangs, System Trace), use the `xctrace` skill. Otherwise ask the user:

- Profile a **Release** build on a **device** (Product › Profile), using the **SwiftUI** template – SwiftUI instrument, Time Profiler, and Hangs/Hitches together.
- Reproduce **one** interaction per capture, only long enough to show the issue, and note what was happening.
- Share the trace, or screenshots of the SwiftUI lanes and the Time Profiler call tree, plus device, OS, and build configuration. For memory problems, add the memory graph or Allocations data.
- Ask for a second capture if the first mixes interactions, and a before/after pair once a fix is tried.

Reading the SwiftUI instrument:

- **Long View Body Updates** – orange above 500 µs, red above 1 ms. Set the inspection range on a long update and read the Time Profiler for that range; filter to calls made by the specific `body`.
- **Other Long Updates** – geometry, text, and layout work.
- **Long Platform View Updates** – UIKit/AppKit views hosted in SwiftUI.
- **Update Groups** – long active groups without individual long updates mean *too many* updates rather than slow ones: inspect update counts.
- **Cause & Effect Graph** ("Show Causes") – why updates happen. SwiftUI is declarative, so backtraces rarely answer this; compare the causes with the data flow you expect and fix the highest-frequency unexpected cause.
- **Hitches** – frames that missed their deadline.

Hangs: a hang is a noticeable delay in a discrete interaction (from about 100 ms; the Hangs instrument flags 250 ms by default and can be lowered). It almost always means long-running work on the main thread – the main run loop cannot process events while busy. Move that work off the main actor and keep event handlers short.


## 4. Diagnose

- Map the evidence to one category: invalidation, identity churn, layout thrash, main-thread work, image cost, or animation cost.
- Prioritize by impact, not by how easy a problem is to explain.
- Say explicitly whether each conclusion is code-backed or trace-backed, and what evidence would remove the remaining uncertainty.


## 5. Remediate

- Narrow observation: pass rows their element; split frequently changing fields into separate stored properties; extract a smaller observable where many views read a small slice (`performance-plus.md`).
- Stabilize identity; filter before `ForEach` instead of `if` inside it.
- Move heavy work out of `body` into stores, model-layer precomputation, or background preprocessing. `@State` is for view-owned state, not an ad-hoc cache.
- Use `scrollTransition()` / `visualEffect()` for scroll-driven visuals instead of state updates.
- Downsample images before rendering.
- Use `equatable()` only when equality is cheaper than recomputing the subtree and inputs are genuinely value-semantic – never as a blanket fix.
- Do not change unrelated layout or behavior.


## 6. Verify

Ask the user to repeat the same capture and compare with the baseline: update counts, hitches, CPU, memory peak.


## Report format

```markdown
## Summary

[One short paragraph: the most likely bottleneck, and whether the conclusion is code-backed or trace-backed.]

## Findings

1. [Issue title]
   - Symptom: [what the user sees]
   - Likely cause: [root cause]
   - Evidence: [code reference or profiling evidence]
   - Fix: [specific change]
   - Validation: [what to measure after the fix]

## Metrics

| Metric | Before | After | Notes |
| --- | --- | --- | --- |
| Long body updates / update count | | | |
| Hitches | | | |
| CPU | | | |
| Memory peak | | | |

## Next step

[One concrete action: apply a fix, capture a better trace, or validate on device.]
```

Order findings by impact. Mark hypotheses as hypotheses. If no metrics exist yet, omit the table and say what to measure.
