# Accessibility audit (App Store nutrition labels)

Use this file when the user asks to audit a view or screen for accessibility, to check VoiceOver, Dynamic Type, or contrast support, or to decide whether the app can claim an Accessibility Nutrition Label in App Store Connect. For everyday rules while writing code, `accessibility.md` is enough.

The audit covers three labels: **VoiceOver**, **Larger Text** (Dynamic Type), and **Sufficient Contrast**. Audit each one the user asked for (all three if they asked for an accessibility audit in general) and give each its own verdict.

Source: Apple's `accessibility-voiceover-specialist`, `accessibility-dynamic-type-specialist`, and `accessibility-sufficient-contrast-specialist` skills (Xcode 27), condensed to SwiftUI. Corrections against Apple's API reference and computed ratios are marked *checked*.


## Procedure

1. Read the view file and the subviews it composes. Note where accessibility modifiers are applied elsewhere (shared components, view extensions, design-system modules) – do not flag what a component already handles.
2. Build a list of interactive elements, images, text, and colors with line numbers.
3. Evaluate each label below. Verdicts are binary – **PASS** or **FAIL** – except contrast, which can also be **NEEDS VERIFICATION**. Never use "warning" or "at risk".
4. If Xcode MCP is available, render the previews with the `preview-debug` skill: default, `Dynamic Type: AX 5`, `Color Scheme: Dark Appearance`, `Contrast: Increased Contrast`. Use the images to confirm clipping, truncation, and colors. Source analysis is authoritative; a missing render is not a failure.
5. Report (see "Report").

A single view rarely decides a label on its own: layout adaptation and scrolling are often the parent's job. Say so in "Assumptions" instead of failing the view.


## VoiceOver

### FAIL criteria

1. **Missing label.** Every interactive element and every meaningful image needs a spoken label.
   - Labeled automatically: `Button("Save")`, `Button("Add", systemImage: "plus")`, `Label("Settings", systemImage: "gear")`, `Toggle("Dark Mode", isOn:)`, `Picker("Sort by", …)`, `TextField("Email", …)`, `Slider` with a label closure, `Menu("Options", systemImage: …)`.
   - Needs a label: a button whose label is only an `Image`, `Image("photo")` that is not decorative, `AsyncImage` with meaningful content.
2. **Label not human-readable.** File names (`"IMG_2847.heic"`), identifiers (`"btnSubmit"`, `"btn_submit_v2"`), UUIDs, the element type alone (`"button"`, `"image"`), unexplained abbreviations. Also asset names that SwiftUI reads aloud, e.g. `Image(.newBanner2026)`.
3. **Missing trait on a custom interactive view.** Prefer replacing the view with a `Button` (see `accessibility.md`). Otherwise:

   | Behavior | Modifier |
   | --- | --- |
   | Tappable (`onTapGesture`) | `.accessibilityAddTraits(.isButton)` |
   | Opens a URL | `.accessibilityAddTraits(.isLink)` |
   | Section heading styled with a large or bold font | `.accessibilityAddTraits(.isHeader)` |
   | Value changed by dragging (rating, custom slider) | `.accessibilityAdjustableAction { direction in … }` |

4. **Inaccessible image.** A meaningful image without a label. Pass: `.accessibilityLabel(…)`, `Image(decorative:)`, `.accessibilityHidden(true)`, an SF Symbol inside a labeled `Label` or `Button`. For `Image(variableName)` with unclear intent, flag it and state the assumption.

### Exempt

Elements hidden with `.accessibilityHidden(true)`, decorative images, disabled controls, standard controls with text, layout containers, and system chrome (navigation titles, tab bar items, toolbar items with text).

### Recommendations (never change the verdict)

- **Grouping.** A row or card with several static texts (title, subtitle, date) or an image plus text describing one item: `.accessibilityElement(children: .combine)`; hide a decorative image first. A container that is itself the tap target: combine, so VoiceOver announces one button. Do not combine children that are separately interactive.
- **Custom actions.** A row with `.swipeActions`, a context menu, or several gestures: expose each action with `.accessibilityAction(named: "Delete") { … }`.
- **Reading order.** When visual order differs from source order (a `ZStack` overlay that is visually first but declared last, repositioned content): `.accessibilitySortPriority(_:)`, sparingly.
- **More traits.** `.isSelected` for a custom selected state, `.updatesFrequently` for text that changes more than once a second (timers, scores), `.isSearchField` for a custom search input, `.startsMediaSession` for controls that start playback.


## Larger Text (Dynamic Type)

### FAIL criteria

| Pattern | Why |
| --- | --- |
| `.font(.system(size: N))` | Fixed size, does not scale |
| `.font(.custom("Name", fixedSize: N))` on readable text | Opts out of Dynamic Type by design |
| `.minimumScaleFactor` as the way to fit large text | Shrinks text the user asked to enlarge |
| `.lineLimit(1)` on primary content that can be long, with no other way to read it | Truncates at large sizes |
| `.frame(height: N)` (or a fixed aspect ratio) around text | Clips text as it grows |
| `.dynamicTypeSize(...)` clamping a whole screen | Caps the user's setting everywhere |

*Checked:* `.custom("Name", size: N)` **does** scale (relative to `.body`), and `.custom(_:size:relativeTo:)` scales relative to the given style. Only `fixedSize:` opts out. Apple's skill implies otherwise; do not fail `size:`.

Pass: text styles (`.body`, `.headline`, …), `.custom(_:size:relativeTo:)`, `.body.scaled(by:)` (iOS 26+), `@ScaledMetric` for spacing, icon sizes, and dimensions, `ViewThatFits`, layouts switched on `dynamicTypeSize.isAccessibilitySize`, a clamp limited to one small element that genuinely cannot grow.

Exempt: hidden text, system chrome, and bar items that provide the Large Content Viewer (`.accessibilityShowsLargeContentViewer()`).

When suggesting a replacement for a fixed size, use the nearest text style: 11–12 pt → `.caption2`/`.footnote`, 13 → `.caption`, 15–17 → `.callout`/`.body`, 17–20 → `.headline`/`.title3`, 20–22 → `.title2`, 22–28 → `.title`, 28–34 → `.largeTitle`.

### Layout adaptation (informational for a single view)

- Horizontal rows with several texts should switch to vertical at accessibility sizes (`ViewThatFits`, or `dynamicTypeSize.isAccessibilitySize`).
- Long or multi-part content must scroll; at AX 5 almost nothing fits on one screen.
- Grids should fall back to a list at accessibility sizes.

Report these, but fail a view on layout alone only when the audit covers the whole screen and the content cannot be reached at AX 5 (confirm with an AX 5 render when possible).


## Sufficient Contrast

### Thresholds (WCAG 2.1)

| Element | Minimum ratio |
| --- | --- |
| Text below 18 pt regular / 14 pt bold | 4.5:1 |
| Text 18 pt+ regular or 14 pt+ bold (`.title3` and larger; `.headline` counts as bold 17 pt) | 3:1 |
| Meaningful non-text UI: icons that carry meaning, control borders, input outlines | 3:1 |
| Decorative elements, disabled controls | Exempt |

### Computing a ratio

1. Resolve foreground and background to sRGB (0–1). If the background is not set on the element, walk up to the nearest ancestor background; if there is none, use the system background (white in light, black in dark).
2. With opacity, composite first: `c = fg × alpha + bg × (1 − alpha)` per channel.
3. Linearize each channel: `c ≤ 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055)^2.4`.
4. Luminance `L = 0.2126 R + 0.7152 G + 0.0722 B`.
5. Ratio `(L_lighter + 0.05) / (L_darker + 0.05)`.

Compute; do not quote remembered ratios. *Checked* with the documented light-mode values: `.secondary` (#3C3C43 at 60 %) on white ≈ 3.4:1 (Apple's skill says ≈ 4.6:1), `systemGray` ≈ 3.3:1, `systemGray2` ≈ 2.2:1, `systemBlue` ≈ 4.0:1, `systemRed` ≈ 3.5:1. So secondary or tinted body text on white can fail 4.5:1 – check it, in both appearances.

### NEEDS VERIFICATION

Asset-catalog colors, design-system tokens whose values are not visible, colors computed at runtime, materials and glass over arbitrary content: do not guess a value and do not fail the element. Mark it NEEDS VERIFICATION and say how to check it – read the asset's Any and Dark sRGB values from the catalog, or render the preview and sample it (Accessibility Inspector's contrast calculator, Digital Color Meter).

Verdict: **FAIL** if any element with known colors is below its threshold (a real failure outranks unknowns; list both); otherwise **NEEDS VERIFICATION** if any color is unresolved; otherwise **PASS**.

Check light and dark appearance. Text over images or Liquid Glass depends on the content behind it; flag it for a rendered check rather than computing a single ratio.


## Report

For each audited label:

```
VoiceOver – FAIL

Failing
- Line 14: `Button { Image(systemName: "trash") }` – no label (criterion 1). Use `Button("Delete", systemImage: "trash") { … }`.

Passing
- Line 9: `Toggle("Notifications", isOn: $isOn)` – labeled by its title.

Recommendations
- Line 20: combine the row's title and date with `.accessibilityElement(children: .combine)`.

Assumptions
- `Image(item.iconName)` treated as meaningful; if decorative, use `Image(decorative:)`.
```

Contrast entries include the foreground and background (hex), the computed ratio, and the required ratio. Fixes reference real lines, names, and modifiers. Keep it short: what fails and how to fix it. If nothing auditable is found, report PASS and say so. Mention which renders were checked, if any.
