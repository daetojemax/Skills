# Sources

Where each file came from, and what was changed. Use this to check upstream updates: diff the upstream repository from the commit below to its current head, then port relevant changes.

| Upstream | Commit | Date |
| --- | --- | --- |
| [twostraws/SwiftUI-Agent-Skill](https://github.com/twostraws/SwiftUI-Agent-Skill) – SwiftUI Pro 2.0.0 | `f980071` | 2026-10-07 |
| [Dimillian/Skills](https://github.com/Dimillian/Skills) – swiftui-ui-patterns, swiftui-view-refactor, swiftui-liquid-glass, swiftui-performance-audit | `05ba982` | 2026-03-29 |
| Apple: "Adopting Liquid Glass", "Applying Liquid Glass to custom views", SwiftUI API reference | – | checked 2026-10-12 |

Check for updates:

```bash
git clone https://github.com/twostraws/SwiftUI-Agent-Skill && git -C SwiftUI-Agent-Skill diff f980071 HEAD -- swiftui-pro
git clone https://github.com/Dimillian/Skills && git -C Skills diff 05ba982 HEAD -- swiftui-ui-patterns swiftui-view-refactor swiftui-liquid-glass swiftui-performance-audit
```


## File map

| File | Source | Changes |
| --- | --- | --- |
| `SKILL.md` | New; structure and core instructions from SwiftUI Pro | MV stance; Step 0 environment check (Xcode, deployment target, isolation); version table; four modes (build, review, refactor, performance audit); file rule relaxed for small private subviews |
| `references/architecture.md` | View Refactor `mv-patterns.md`, UI Patterns `app-wiring.md` and `async-state.md` | Merged; app wiring made generic (no Ice Cubes types, no singletons); state-ownership table updated for iOS 17+ only and `@Bindable`; view model example aligned with Xcode 27 `@State` rules |
| `references/views.md` | SwiftUI Pro `views.md` + View Refactor `SKILL.md` | Removed "place logic in view models"; replaced "one type per file" with the private-subview rule; added member order, actions, stable tree sections |
| `references/navigation.md` | SwiftUI Pro `navigation.md` + UI Patterns `navigationstack.md`, `sheets.md`, `deeplinks.md`, `tabview.md` | Router via `@Bindable` instead of `Binding(get:set:)`; `Tab` API with iOS 17 `tabItem` fallback; tab interception via store property; `NavigationSheet` closure removed |
| `references/liquid-glass.md` | New, from Apple documentation; checklist ideas from Dimillian `swiftui-liquid-glass` | Written from scratch: HIG rules, version gating, toolbars, tab bars, custom bars |
| `references/api.md` | SwiftUI Pro | `tabItem` rule gated by deployment target |
| `references/data.md` | SwiftUI Pro | Cross-references point to local skills |
| `references/swift.md` | SwiftUI Pro | Concurrency pointer → `swift-concurrency-expert` |
| `references/performance.md` | SwiftUI Pro | Added image rules (from Dimillian audit) and a pointer to the audit workflow |
| `references/performance-plus.md` | SwiftUI Pro | Unchanged; loaded only in audit mode |
| `references/performance-audit.md` | Dimillian `swiftui-performance-audit` (`SKILL.md`, `profiling-intake.md`, `report-template.md`, Instruments and WWDC summaries) | Condensed into one file; triage order kept; `code-smells.md` dropped because SwiftUI Pro rules cover it more recently (its shared-formatter advice was also unsafe under Swift 6); fixes constrained to MV |
| `references/accessibility.md`, `design.md`, `hygiene.md`, `localization.md`, `resizability.md` | SwiftUI Pro | Unchanged |
| `references/review.md` | SwiftUI Pro `SKILL.md` output format | Review order extended (architecture, Liquid Glass); MV example finding added |
| `references/components/*` | UI Patterns `references/` | See below |
| `references/components/index.md` | UI Patterns `components-index.md` | Rewritten as a table |


## Component fixes

Upstream UI Patterns examples were checked against SwiftUI Pro rules. Rewritten: `haptics.md` (`sensoryFeedback` instead of UIKit generators), `overlay.md` (`.task(id:)` instead of `DispatchQueue`), `grids.md` (no `cornerRadius()`/`GeometryReader`), `media.md` (`AsyncImage`, `Button`, `scrollIndicators`), `scroll-reveal.md` (`containerRelativeFrame`, `ScrollPosition`, no local file paths), `split-views.md` (`NavigationSplitView` as the default), `tabview.md` (sidebar and dynamic tabs only), `focus.md` (identity-based dynamic fields, no `DispatchQueue`).

Edited: `controls.md` (FormatStyle, `LabeledContent`), `form.md` and `list.md` (value-based `NavigationLink`, `.contentShape(.rect)`, escaped key-path typo), `scrollview.md` and `input-toolbar.md` (`defaultScrollAnchor`, `safeAreaBar`), `searchable.md` (task keyed on query and scope, `ContentUnavailableView.search`), `title-menus.md` (`navigationSubtitle`), `matched-transitions.md` (iOS 18, stable source ID), `lightweight-clients.md` (`Sendable`), `theming.md` (semantic defaults), `macos-settings.md` (FormatStyle), `top-bar.md` (undefined constant).

Unchanged: `loading-placeholders.md`, `previews.md`, `menu-bar.md`.

Not included: UI Patterns `SKILL.md` (superseded by this skill), `app-wiring.md`, `async-state.md`, `navigationstack.md`, `sheets.md`, `deeplinks.md`, `performance.md` (merged into the files above).
