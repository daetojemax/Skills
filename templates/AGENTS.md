# AGENTS.md

Guidance for coding agents (Claude Code, Codex, and others) working in this repository. Claude Code reads it through `CLAUDE.md`, which contains only `@AGENTS.md`.

<!--
Base template derived from the Template, Brainy, and Communals projects.
Replace every <placeholder>, delete sections that do not apply, and keep product-specific
rules in "Project specifics" at the end. Keep this file short: architecture and rules that
an agent cannot infer from the code. Facts that change often belong in MEMORY.md.
-->


## Project

<App> – iOS SwiftUI app. Pure iOS, no cross-platform layer.

- Swift tools <6.2>, Swift 6 language mode, deployment target iOS <17 | 26>.
- Xcode project: `App/<App>App.xcodeproj`; always work through `Project.xcworkspace`.
- Shared scheme: `<App>`; bundle ID: `<com.example.app>`.
- UI language: <English | Russian>. All app-owned copy – titles, buttons, errors, accessibility labels – uses it.


## Memory and planning

- Read `MEMORY.md` before making changes. After meaningful work – an architecture decision, a non-obvious debugging finding, a user preference, a release fact – add a short dated note in the same change. Do not turn it into a changelog or record tentative experiments.
- When working through a multi-step plan, keep its statuses current as steps finish. If the repository has `Plan.md`, update it when project-level tasks are completed or reprioritized.


## Architecture

Modular Swift Package plus a thin Xcode app target:

```
App/<App>App.swift                 @main entry point (Xcode target); hosts AppRoot
Sources/
├── <App>/                         App orchestration
│   ├── AppRoot, AppState          Root state machine, long-lived services in @State
│   ├── AppTabView, AppTabRootView Authenticated tab shell; tab → root screen mapping
│   ├── AppRegistry/               AppDependencyGraph: AppEnvironment + environment injection modifiers
│   └── Destinations/              Route, sheet, and full-screen → view mappings
├── Features/<Name>UI/             One module per feature: screens, local UI, feature stores
└── Base/
    ├── Design                     Color and font tokens, shared components, resources
    ├── Navigation                 Router, SimpleRouter, AppTab, destinations, deeplinks
    ├── Client                     NetworkClient, APIEndpoint, Auth, CurrentUser, push
    ├── Core                       Toasts/errors, preferences, Keychain, app services
    └── Models                     Domain models, request/response types<, SwiftData models>
```

Dependency direction: `Design` and `Models` are standalone → `Navigation` depends on `Design` + `Models` → `Client` depends on `Models` (+ `Core`) → feature modules depend on the base modules they need → the `<App>` module depends on everything. Feature modules never depend on each other, except on a shared `ComponentsUI` module where one exists. Keep business logic out of `Base/Design` and `Base/Navigation`.

### State and data flow (MV)

The project uses MV, not MVVM – see the `swift-ui` skill, `references/architecture.md`.

- Shared state lives in `@MainActor @Observable` types named by role: `…Store` for feature data (e.g. `MetersStore`), `…Manager` for app-wide behavior (e.g. `ToastManager`), `…Service` for work without UI state. Do not add view models.
- Long-lived services are created once in `AppRoot` and injected with `@Environment(Type.self)` through the `with…Environment` / `with…Dependencies` modifiers in `AppRegistry/AppDependencyGraph.swift` (names vary per project, e.g. `withAuthenticatedAppEnvironment`). Feature views read them from the environment; never construct duplicates inside views.
- Sheets and full-screen covers re-inject the environment values their content needs.
- `AppState` drives root switching (for example `.loading` → `.onboarding` → `.authenticated(currentUser:)` / `.unauthenticated`). `Auth.configurationUpdates` and `NetworkClient.authenticationExpiredUpdates` are `AsyncStream`s consumed in `AppRoot`'s `.task` – not NotificationCenter or callbacks.

### Navigation

`Router<Tab, Destination, Sheet, FullScreen>` holds one path per tab plus the presented sheet and full-screen cover; `AppRouter` is its app-specific typealias. `AppSimpleRouter` drives the single-stack authentication flow.

To add a pushed screen:

1. Add a case to `Sources/Base/Navigation/RouterDestination.swift` (and to its deeplink parser if the screen is linkable).
2. Map it in `Sources/<App>/Destinations/AppDestinations.swift`.
3. Navigate with `router.navigateTo(.yourDestination)` from a view that reads `@Environment(AppRouter.self)`.

Sheets and full-screen covers work the same way through `SheetDestination` / `FullScreenDestination` and their mappers. `DeeplinkManager` only parses links into events; `AppRoot` decides how to open them.

### Networking

`NetworkClient` is the only HTTP transport (Pulse-logged `URLSession`). Endpoints conform to `APIEndpoint`; the host comes from `NetworkConst`. Tokens live in the Keychain through `KeychainWrapper`; set `withToken = true` for authenticated requests. Never create a second `URLSession` or client inside `Core` or a feature.

### Design system

- Colors only through the typed tokens in `Base/Design` (`Color.<Group>.<name>`, for example <`Color.Content.primary`, `Color.Accent.primary`>); never raw hex or RGB values in views.
- Fonts through the font extensions in `Base/Design`.
- Reuse existing components (`PrimaryButton`, `LoadingIndicator`, toasts, …) before writing new ones.
- Use `padding` for fixed spacing and `Spacer()` only to push elements apart.

### Adding a feature module

1. Create `Sources/Features/<Name>UI/`.
2. In `Package.swift`, add a dynamic library product and a target depending on the base modules it needs (usually `Design`, `Core`, `Client`, `Navigation`).
3. Add the target as a dependency of the `<App>` target.
4. Map its screens in `Destinations/` (and in the tab root view for a tab).


## Skills

Installed skills supply language- and framework-level rules. This file supplies project decisions. **When they conflict, this file wins** for project conventions (architecture, naming, design system, build workflow); the skills win for API correctness and version requirements.

| Task | Skill |
| --- | --- |
| Screens, components, navigation, Liquid Glass, SwiftUI review or refactor, SwiftUI performance, accessibility audits | `swift-ui` |
| async/await, actors, `Sendable`, strict-concurrency errors | `swift-concurrency` |
| SwiftData models, queries, migrations, CloudKit, widgets sharing a store | `swift-data` |
| Unit and integration tests | `swift-testing` |
| Profiling with Instruments from the command line: CPU time, hangs, traces | `xctrace` |
| Verifying the UI when the app runs through Xcode MCP (outside the Claude app) | `device-interaction` (Apple) |
| App Store Connect, TestFlight, signing, metadata | the matching `asc-*` skill |
| Implementing a Figma design | the Figma skills / MCP |

- Apply every skill's **Step 0**: the toolchain and the deployment target decide which APIs are allowed. Never raise the deployment target to use an API.
- Check exact Apple API signatures and availability with Xcode MCP `DocumentationSearch` instead of relying on memory.
- During feature work or bug fixes, apply skill rules to the code you touch. Report other modernization opportunities separately; do not refactor unrelated code unasked.


## Build, run, test

- **Running inside the Claude desktop app** (the built-in Claude iOS Simulator tools are available): run the app with those tools. Open the live panel first (`control` → `attach`), build with `build` (`workspace_path`: `Project.xcworkspace`, `scheme`: `<App>`) and poll `build_status`, then `control` → `launch` with the built `.app`. Verify the change with the same tools – `screenshot`, `tap`, `swipe`, `text`, `open_url` – so the user can watch it in the panel.
- **Everywhere else** (Claude Code in a terminal, Codex, other agents): build and run through Xcode MCP – `XcodeOpenWorkspace` with `Project.xcworkspace`, then `BuildProject` / `RunProject` – and verify the UI with the **`device-interaction` skill**: start a workspace session, install and run, read the UI hierarchy and screenshot, and interact by the hierarchy's `hitPoint` coordinates. It also works on a physical device. Use `device-interaction` only when the app runs through Xcode MCP, never alongside the built-in simulator.
- In both cases, Xcode MCP is also the tool for `DocumentationSearch`, `RenderPreview`, `XcodeRefreshCodeIssuesInFile`, and test runs.
- Do not use XcodeBuildMCP (removed from this setup). Do not run shell `xcodebuild` for routine build/run work unless asked.
- `swift build` on the macOS host is not a reliable check for an iOS-only package; build the app scheme instead.
- Run package tests with the Xcode toolchain: `TOOLCHAINS=com.apple.dt.toolchain.XcodeDefault xcrun swift test` (the default `swift` may be a different toolchain).
- Use the simulator only to check the specific change in the current task. Describe any broader flow you want to test and wait for approval first.


## Git

- When asked to commit and push, use the current branch unless told otherwise; do not create a feature branch just because the branch is `main`.
- Keep commits focused; never revert changes you did not make. Check `git status --short` and `git diff --cached --stat` before committing.


## Project specifics

<!--
Product rules that do not follow from the code: data flows, persistence and reset rules,
backend contracts, release procedure ("собирай" = TestFlight upload, …), App Store Connect
profile and app ID, environment URLs, prohibited shortcuts, UI language and tone.
-->
