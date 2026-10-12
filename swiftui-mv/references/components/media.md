# Media (images, video, viewer)

## Intent

Load remote images consistently, show lightweight inline previews, and present one full-screen viewer.

## Core patterns

- Use `AsyncImage` for remote images. On iOS 27 it honors HTTP caching headers automatically; do not add an image library or cache just for that. Use a third-party loader only if the project already has one, or after asking.
- Keep inline previews small; load full-size media only in the viewer.
- Use one shared viewer state (a small `@Observable` in the environment) so any view can open media without prop-drilling, and present it from a single place.
- Use `openWindow` on macOS/visionOS and a sheet or `fullScreenCover` on iOS.

## Example: inline media strip

```swift
struct MediaPreviewRow: View {
    @Environment(MediaViewer.self) private var viewer

    let attachments: [MediaAttachment]

    var body: some View {
        ScrollView(.horizontal) {
            LazyHStack {
                ForEach(attachments) { attachment in
                    Button {
                        viewer.show(attachment, in: attachments)
                    } label: {
                        AsyncImage(url: attachment.previewURL) { image in
                            image.resizable().scaledToFill()
                        } placeholder: {
                            ProgressView()
                        }
                        .frame(width: 120, height: 120)
                        .clipShape(.rect(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(attachment.altText ?? String(localized: "Image"))
                }
            }
        }
        .scrollIndicators(.hidden)
    }
}
```

## Example: one viewer at the root

```swift
@MainActor
@Observable
final class MediaViewer {
    var selected: MediaAttachment?
    private(set) var attachments: [MediaAttachment] = []

    func show(_ attachment: MediaAttachment, in attachments: [MediaAttachment]) {
        self.attachments = attachments
        selected = attachment
    }
}

struct AppRoot: View {
    @State private var viewer = MediaViewer()

    var body: some View {
        content
            .environment(viewer)
            .fullScreenCover(item: $viewer.selected) { selected in
                MediaViewerView(selected: selected, attachments: viewer.attachments)
            }
    }
}
```

`$viewer.selected` works because `@State` of an `@Observable` type projects bindings to its properties.

## Pitfalls

- Avoid loading full-size images in rows; use resized previews.
- Don't present several viewers at once; keep a single source of truth.
- Use the alt text from your data for VoiceOver; do not leave remote images unlabeled.
