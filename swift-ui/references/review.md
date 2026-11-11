# Review process and output format

Review Swift and SwiftUI code for correctness, modern API usage, MV architecture, and adherence to project conventions. Report only genuine problems – do not nitpick or invent issues. Include deprecated and soft-deprecated API as findings.

Run Step 0 from `SKILL.md` first: findings must respect the project's deployment target and toolchain. Never recommend an API the project cannot compile or run.


## Review order

1. Deprecated and soft-deprecated API – `api.md`.
2. Architecture: view models where plain state would do, logic in `body`, singletons reached from views – `architecture.md`.
3. View structure, member order, extraction, stable trees, animations – `views.md`.
4. Data flow, property wrappers, bindings, identity – `data.md`.
5. Navigation, sheets, alerts, deep links – `navigation.md`.
6. Liquid Glass usage and custom bar backgrounds (iOS 26+ targets, or code using glass) – `liquid-glass.md`.
7. HIG-aligned, flexible design – `design.md`.
8. Window resizing, size classes, safe areas, iPhone Duo – `resizability.md`.
9. Accessibility – `accessibility.md`.
10. Localization – `localization.md`.
11. Everyday performance – `performance.md`.
12. Swift and concurrency – `swift.md`.
13. Hygiene – `hygiene.md`.

For a partial review ("check the navigation", "is this accessible?"), load only the relevant files. For a deep performance review, follow `performance-audit.md` instead; for an accessibility audit with verdicts, `accessibility-audit.md`.


## Output format

Organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated (e.g., "Use `foregroundStyle()` instead of `foregroundColor()`").
3. Show a brief before/after code fix.
4. If the fix depends on the OS version or toolchain, say so.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

Example output:

### ContentView.swift

**Line 12: Use `foregroundStyle()` instead of `foregroundColor()`.**

```swift
// Before
Text("Hello").foregroundColor(.red)

// After
Text("Hello").foregroundStyle(.red)
```

**Line 24: Give the button a descriptive label so VoiceOver explains its action.**

```swift
// Before
Button(action: addUser) {
    Image(systemName: "plus")
}

// After
Button("Add User", systemImage: "plus", action: addUser)
```

**Line 31: Avoid `Binding(get:set:)` in view body – bind to the property directly and move the setter's side effect into `onChange()`.**

```swift
// Before
TextField("Username", text: Binding(
    get: { store.username },
    set: { store.username = $0; store.save() }
))

// After
TextField("Username", text: $store.username)
    .onChange(of: store.username) {
        store.save()
    }
```

Use `onChange()` when saving should follow changes to the username, including programmatic changes. Equal-value assignments will not trigger a save.

**Line 40: `ProfileViewModel` only mirrors local state and wraps an environment service – replace it with `@State` plus `@Environment` (MV).**

```swift
// Before
@State private var viewModel = ProfileViewModel()

// After
@Environment(ProfileService.self) private var profileService
@State private var profile: Profile?
```

### Summary

1. **Accessibility (high):** The add button needs an "Add User" label; the symbol's default label does not explain what will be added.
2. **Architecture (medium):** `ProfileViewModel` adds a layer without behavior of its own.
3. **Deprecated API (medium):** `foregroundColor()` on line 12 should be `foregroundStyle()`.
4. **Data flow (medium):** The manual binding on line 31 is fragile and harder to maintain.

End of example.
