# Overlays and toasts

## Intent

Show transient UI – toasts, banners, small loaders – without affecting the layout underneath.

## Core patterns

- Use `.overlay(alignment:) { … }` (the builder form) to place transient UI without changing layout.
- Keep the overlay content stable and vary visibility through state, so transitions animate correctly.
- Auto-dismiss with `.task(id:)` and `Task.sleep(for:)`; the task is cancelled automatically if the toast changes or the view disappears. Never use `DispatchQueue.main.asyncAfter`.
- If many features show toasts, put a small `@Observable` `ToastCenter` in the environment and render it once at the root.

## Example: toast overlay

```swift
struct AppRootView: View {
    @State private var toast: Toast?

    var body: some View {
        content
            .overlay(alignment: .top) {
                if let toast {
                    ToastView(toast: toast)
                        .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            .animation(.smooth, value: toast)
            .task(id: toast) {
                guard toast != nil else { return }
                try? await Task.sleep(for: .seconds(2))
                toast = nil
            }
    }
}
```

`Toast` must be `Equatable`, both for the animation and for `task(id:)`.

## Design choices to keep

- Align overlays to a clear edge (`.top` or `.bottom`), clear of system bars.
- Use short auto-dismiss timers, and let VoiceOver users reach the message: post an announcement with `AccessibilityNotification.Announcement(message).post()` for important toasts.

## Pitfalls

- Avoid overlays that block all interaction unless that is the point.
- Don't stack many overlays; queue toasts or replace the current one.
- Do not put a toast queue in the environment as a closure; use an observable object (see `api.md`).
