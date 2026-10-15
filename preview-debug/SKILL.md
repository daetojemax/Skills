---
name: preview-debug
description: Renders SwiftUI #Preview snapshots through Xcode MCP's RenderPreview so the agent can see a view without running the app – checking a UI change, comparing light/dark, Dynamic Type sizes up to AX5, increased contrast, orientation, or iPhone vs iPad, and detecting stale renders. Use when you need to look at a single SwiftUI view or screen; for navigation flows and interaction, run the app in a simulator instead.
license: MIT
metadata:
  version: "1.0.0"
  based-on: "Fatbobman, 'Letting AI See SwiftUI' (2026-09-30); erin sparling's RenderPreview notes; checks against Xcode 27.0 – see SOURCES.md"
---

# Preview debugging with RenderPreview

`RenderPreview` (Xcode MCP, Xcode 26.3+; headless in Xcode 27) builds and renders one `#Preview` and returns a PNG plus metadata. It is the fastest way to *see* a view: no app launch, no navigating to the screen, and every appearance variant on demand. It does not interact – taps, scrolling, and navigation flows need the simulator.


## When to use

- After changing a view: render its preview and look at the result before reporting the change as done.
- Accessibility pass: render the same preview with the largest Dynamic Type sizes, dark and light appearance, and increased contrast.
- Layout checks across orientation and device family.
- Design exploration: render several variants of a view side by side.

Use the simulator (built-in Claude simulator in the Claude app, Xcode MCP + `device-interaction` elsewhere) for anything involving navigation, input, real data, or state that a preview cannot set up.


## Procedure

### 1. Open the workspace

Call `XcodeOpenWorkspace` with the absolute path to the `.xcworkspace` (or `.xcodeproj`). **Keep the returned `workspaceIdentifier`** and pass it to every later call. Passing the path as `workspaceIdentifier` fails with "Unknown workspace identifier", despite the parameter description (checked on Xcode 27.0).

The response also reports `activeScheme` and `activeRunDestination` – the destination the preview will render on.

### 2. Find the file's navigator path

`sourceFilePath` is the path **in Xcode's project navigator**, not on disk. A disk-relative path such as `Sources/Features/X/View.swift` fails with `FileNotFoundError: File not found in project structure`. Find the right path with `XcodeGlob`:

```json
{ "workspaceIdentifier": "<id>", "pattern": "**/ThreadsEmptyStateView.swift" }
```

With a local Swift package inside an app project, a file can appear twice (for example `BrainyApp/Brainy/Sources/…` and `Brainy/Sources/…`). Prefer the path under the app project; it renders with the app's scheme.

### 3. Render

```json
{
  "workspaceIdentifier": "<id>",
  "sourceFilePath": "<navigator path>",
  "previewDefinitionIndexInFile": 0,
  "timeout": 600
}
```

- `previewDefinitionIndexInFile` is the 0-based index of the `#Preview` (or `PreviewProvider`) in the file.
- The first render includes a build and can take well over a minute; set a generous `timeout`.
- If the response says "Waiting for packages", wait about 60 s and retry, up to four times.
- Parameterized previews (`#Preview(arguments:)`) and timelines (widgets, Live Activities) take `previewCanvasControlOverrides` (`groupItemIndex`, `timelineIndex`, `toggleState`); read the allowed values from `supportedCanvasControlOverrides` in a previous response.

### 4. Verify the render before trusting it

From the response:

- `errors` must be empty.
- `previewSnapshotPath` points to a PNG in a temporary folder – copy it somewhere stable right away, then **open it with the image-reading tool and look at it**. A render can succeed and still show the wrong state.
- `renderedDestination` (`deviceModelName`, `platformName`, `systemVersion`) tells you what it actually rendered on. Check the device *family* you need (iPhone vs iPad). Do not claim an exact model you did not get.
- `sourceLineNumber` confirms which `#Preview` was rendered.
- If freshness matters, check the fingerprint (see "Stale renders").

### 5. Variants

The response lists `supportedPreviewVariantOverrides` and `supportedLocalizations`. Take keys and values from there – never hard-code them. On Xcode 27.0 the variants are:

| Key | Values |
| --- | --- |
| `Color Scheme` | `Light Appearance`, `Dark Appearance` |
| `Dynamic Type` | `X Small` … `XXX Large`, `AX 1` … `AX 5` |
| `Contrast` | `Standard Contrast`, `Increased Contrast` |
| `Orientation` | `Portrait`, `Landscape Left`, `Landscape Right` |
| `Control Borders` | `Hidden`, `Shown` |

```json
{ "workspaceIdentifier": "<id>", "sourceFilePath": "<path>", "previewVariantOverrides": { "Dynamic Type": "AX 5", "Color Scheme": "Dark Appearance" } }
```

A useful accessibility matrix: default, `AX 5`, `Dark Appearance`, `Increased Contrast`, and – for screens that support it – `Landscape Left`. Use `previewLocalizationOverride` with a value from `supportedLocalizations` to check translations and long strings.

### 6. Close

Call `XcodeCloseWorkspace` with the identifier when you are done.


## Choosing the device

`RenderPreview` has no device parameter, and `#Preview` ignores `.previewDevice`. Previews render on the workspace's **active run destination**:

1. `XcodeSwitchRunDestination` with `{ "workspaceIdentifier": "<id>", "displayTitle": "<title>" }`. It accepts the display title directly, so you do not need to list destinations first (`XcodeListRunDestinations` has been reported to hang for minutes).
2. Compare the returned `activeDestinationDisplayTitle` with what you asked for; if it differs, stop.
3. Wait before the first render after a switch (about 45 s has been reported as necessary); an immediate render can still use the old destination.
4. After rendering, check `renderedDestination`. Switching reliably selects iPhone vs iPad, but not an exact model: asking for one iPhone can render another of the same size class.

Use one destination per batch. To compare iPhone and iPad, render all previews on one, switch, then render again.

The other known workaround – a `PreviewProvider` with `.previewDevice(...)` – contradicts the `swift-ui` rule to use `#Preview`. Do not add one unless the user asks.


## Stale renders

`RenderPreview` can return an image from an earlier build without any error, especially when only files the preview depends on changed (not the preview file itself). It has been reported in a sizeable share of renders in Swift-package projects and much less often in plain `.xcodeproj` projects. Touching a file does not help; changing the content of the previewed file does force a rebuild.

When the result matters, fingerprint the render:

1. Compute a short hash of the relevant source files.
2. Write it into the previewed file **as a type name**, not a string literal – previews hot-swap literals without recompiling, while a new type name only appears after a real build:

```swift
#if DEBUG
fileprivate enum PreviewFingerprint_8848880a {}

#Preview {
    ThreadsEmptyStateView()
        .overlay(alignment: .bottomTrailing) {
            Text(String(describing: PreviewFingerprint_8848880a.self))
                .font(.caption2)
                .padding(4)
        }
}
#endif
```

3. Render, and check that the image shows the expected fingerprint. If it does not, render once more; if it still does not, discard the image and say so.
4. Remove the fingerprint overlay when you are done, unless the project keeps dedicated capture previews.

Fatbobman's version records the fingerprint and element frames as JSON from inside the preview process instead of drawing it; see `SOURCES.md`.


## Pitfalls

- **One `#Preview` per line.** Several on one line make `previewDefinitionIndexInFile` pick the wrong one, even though `sourceLineNumber` is right.
- **New or deleted files** may not be seen – `FileNotFoundError` for a new file, `noPreviewInfos` after a deletion – because headless mode caches the project structure. Close and reopen the workspace.
- **Preview host crashes after a file rewrite** (in `DebugReplaceableViewChild.updateValue()`) are common; retry once before investigating.
- **Debug-only fixtures** used by previews must be inside `#if DEBUG` together with the previews, or Release builds fail.
- Previews render with preview data, not the app's real state. A correct preview does not prove the screen is correct in the running app.
- Follow the project's rules about previews: some projects forbid preview-only screens or synthetic data in the app runtime. `#Preview` code is not runtime, but check `AGENTS.md` before adding fixtures.


## Reporting

When you report a preview check, state what was verified: the destination the render reported, the variants used, whether a fingerprint matched, and where the image is. If any check failed, say so instead of presenting the image as current. Name saved images by view, variant, and device family (for example `threads-empty-ax5-dark-iphone.png`) so renders cannot be mixed up.
