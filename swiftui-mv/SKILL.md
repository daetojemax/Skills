---
name: swiftui-mv
description: Builds, reviews, and refactors SwiftUI code using MV (model–view) architecture, modern version-aware APIs, Liquid Glass, accessibility, and adaptive layouts. Use when writing new SwiftUI screens or components, reviewing or refactoring SwiftUI views, wiring navigation, tabs, sheets, or app dependencies, adopting Liquid Glass, checking SwiftUI code for deprecated API, or diagnosing SwiftUI performance problems such as janky scrolling, hangs, high CPU or memory, and excessive view updates.
license: MIT
metadata:
  version: "1.0.0"
  based-on: "SwiftUI Pro 2.0.0 (Paul Hudson); SwiftUI UI Patterns, View Refactor, Liquid Glass, Performance Audit (Thomas Ricouard) – see SOURCES.md"
---

# SwiftUI (MV)

Write and review SwiftUI the way a senior Apple-platform engineer would: vanilla SwiftUI data flow, small explicit views, modern API chosen for the project's actual deployment target and toolchain, and system components before custom ones.


## Step 0: Check the environment

Before giving version-specific advice, establish these facts. Read them from the project; do not assume.

```bash
xcodebuild -version
grep -rhoE "IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+" --include=project.pbxproj . | sort -u
grep -rhoE "SWIFT_DEFAULT_ACTOR_ISOLATION = [A-Za-z]+" --include=project.pbxproj . | sort -u
grep -hoE "\.iOS\(\.v[0-9_]+\)|defaultIsolation\([A-Za-z.]+\)" Package.swift 2>/dev/null
```

- **Toolchain (Xcode version)** decides which *declarations exist*. `@ContentBuilder`, `alert(_:item:)`, `ForEach` in `toolbar()`, and every iOS 27 API need Xcode 27; toolbar `.hidden()` needs Xcode 27.2. A `#available` check cannot make an older SDK recognize a new declaration.
- **Deployment target** decides which *runtime APIs* can be used unconditionally. The user's projects target **iOS 17** or **iOS 26**. Use newer APIs only within `if #available`, with a fallback for older systems. Never change the deployment target.
- **Default actor isolation** decides whether `@MainActor` annotations are needed (see `references/data.md` and `references/swift.md`).

| Feature | Needs |
| --- | --- |
| Observation, `@Bindable`, `ContentUnavailableView`, `sensoryFeedback`, two-parameter `onChange` | iOS 17 – always available |
| `Tab` API, `TabSection`, `.sidebarAdaptable`, zoom transitions, `onScrollGeometryChange` | iOS 18 |
| Liquid Glass, `safeAreaBar`, `ConcentricRectangle`, `WebView`, `ForEach(items.enumerated())` | iOS 26 |
| `ToolbarOverflowMenu`, `reorderable`, `swipeActionsContainer`, `presentationPlacement` | iOS 27 + Xcode 27 |
| `ArrangementView`, vertical-bar APIs, fold/camera regions | iOS 27.1 + Xcode 27.1 |

If the environment cannot be checked (a code snippet with no project), ask for the deployment target, or default to the conservative choice and mark version-dependent advice explicitly.


## Core instructions

- **Architecture is MV, not MVVM.** Views hold local UI state and orchestrate; `@Observable` stores and services hold shared state and real work; dependencies arrive via `@Environment` or the initializer. Do not introduce view models unless the user asks or the codebase already uses them – see `references/architecture.md`.
- Prefer small, dedicated `View` structs over computed `some View` fragments. A small `private` subview may share its screen's file; reused or independently meaningful views and all non-view types get their own file – see `references/views.md`.
- Prefer system components (`NavigationStack`, `TabView`, `Form`, `List`, toolbars, sheets) over custom ones; on iOS 26+ they adopt Liquid Glass automatically.
- Use modern Swift concurrency only (no GCD); defer deep concurrency work to the `swift-concurrency-expert` skill and SwiftData specifics to the `swiftdata-pro` skill.
- Avoid UIKit unless requested or required for an integration.
- Do not introduce third-party frameworks without asking first.
- Organize the project by feature folders.
- During feature work or bug fixes, complete the requested change and *suggest* unrelated modernization separately; do not apply it without being asked. In reviews, include deprecated API as findings.


## Modes

### Building a screen or feature

1. Step 0.
2. Decide state ownership and where logic lives (`references/architecture.md`).
3. Wire navigation, tabs, and sheets (`references/navigation.md`).
4. Find the closest component pattern in `references/components/index.md` and read only that file.
5. Write the view following `references/views.md` and `references/api.md`; check `references/design.md` and `references/accessibility.md` before finishing.
6. On iOS 26+ targets, follow `references/liquid-glass.md` for bars, toolbars, and any custom glass.
7. Add `#Preview`s for the main and non-happy states (`references/components/previews.md`).

### Reviewing code

Follow `references/review.md`: it lists the review order, which reference to load for each pass, and the output format. Report only genuine problems; do not nitpick or invent issues. For a partial review, load only the relevant references.

### Refactoring a view

1. Reorder members and extract subviews (`references/views.md`).
2. Move actions and business logic out of `body` into methods, stores, or services (`references/architecture.md`).
3. Stabilize the view tree; remove top-level branch swapping and `View.if()`-style helpers (`references/performance.md`).
4. Replace unnecessary or optional view models with plain state (`references/architecture.md`).
5. Keep behavior intact: do not change layout or logic unless asked.

### Performance audit

Only when the user reports a concrete performance problem (janky scrolling, hangs, slow typing or navigation, high CPU or memory, excessive updates) or asks for a deep performance review: follow `references/performance-audit.md`, using `references/performance.md` and `references/performance-plus.md`. Keep `performance-audit.md` and `performance-plus.md` out of routine work and reviews.


## References

- `references/architecture.md` – MV architecture, state ownership, dependency injection, async state, when a view model is justified.
- `references/views.md` – view structure, member order, extraction, files, actions, stable trees, animation, reordering, swipe actions.
- `references/data.md` – Observation, property wrappers, bindings, identity.
- `references/navigation.md` – router, tabs, sheets, alerts, confirmation dialogs, deep links.
- `references/api.md` – modern API, soft deprecations, iOS 27 toolbars.
- `references/liquid-glass.md` – Liquid Glass design rules, custom glass, tab bars, toolbars, version gating.
- `references/design.md` – HIG-aligned, flexible design.
- `references/accessibility.md` – Dynamic Type, VoiceOver, Voice Control, Reduce Motion.
- `references/resizability.md` – resizable windows, size classes, safe areas, iPhone Duo.
- `references/localization.md` – localizable text, bundles, locale-aware formatting.
- `references/performance.md` – everyday performance rules for writing and routine review.
- `references/performance-plus.md` – deeper restructuring to narrow what views depend on (audit only).
- `references/performance-audit.md` – audit workflow, Instruments profiling, report format (audit only).
- `references/swift.md` – modern Swift and concurrency rules.
- `references/hygiene.md` – secrets, tests, launch screen, project hygiene.
- `references/review.md` – review process and output format.
- `references/components/index.md` – component patterns (forms, lists, grids, search, focus, media, overlays, and more).
