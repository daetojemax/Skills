# Sources

- Fatbobman, ["Letting AI See SwiftUI"](https://fatbobman.com/en/posts/letting-ai-see-swiftui/) (2026-09-30): stale renders and the type-name fingerprint, device selection limits, one `#Preview` per line, cached project structure, preview host crashes. His `DesignProbe` implementation (fingerprint and element frames written as JSON from the preview process): https://gist.github.com/fatbobman/94179c301e75e5a390b34888d57e9b2e
- erin sparling, [RenderPreview workarounds](https://gist.github.com/everyplace/67df76ddf3d88f8f35ff202a85080ee2) (Xcode 27.0 RC): `previewVariantOverrides` for orientation, `XcodeSwitchRunDestination` before rendering, waiting after a switch, `XcodeListRunDestinations` hangs, "Waiting for packages" retries, checking `renderedDestination`.

The skill paraphrases both; no text or code is copied. The fingerprint overlay example is a simplified variant of the idea.


## Verified on 2026-10-12 (Xcode 27.0, Brainy workspace)

- `RenderPreview` rendered `ThreadsEmptyStateView` on iPhone 18 Pro / iOS 27.0 in about 80 s including the build; `errors` empty; PNG checked visually.
- `workspaceIdentifier` must be the identifier returned by `XcodeOpenWorkspace`; the absolute workspace path is rejected ("Unknown workspace identifier") although the parameter description allows it.
- `sourceFilePath` must be the navigator path found with `XcodeGlob` (`BrainyApp/Brainy/Sources/…`); the disk-relative path fails with `FileNotFoundError`.
- Response fields: `displayName`, `errors`, `previewSnapshotPath`, `renderedDestination`, `sourceLineNumber`, `supportedLocalizations`, `supportedPreviewVariantOverrides` (Color Scheme, Contrast, Control Borders, Dynamic Type, Orientation).

Not verified here (taken from the sources): stale-render frequency, the fingerprint check, device switching and the 45 s wait, `XcodeListRunDestinations` hangs, multi-`#Preview`-per-line selection, host crashes.
