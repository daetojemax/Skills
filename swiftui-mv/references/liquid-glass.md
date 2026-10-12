# Liquid Glass

Liquid Glass is the iOS 26+ material for the **functional layer** – navigation and controls that float above content. Building with the iOS 26 SDK or later gives standard components (bars, tab bars, sheets, popovers, menus, toggles, sliders, buttons) the new look automatically. Most adoption work is removing custom styling so the system can do its job; custom glass is the exception.

Sources: Apple's "Adopting Liquid Glass" and "Applying Liquid Glass to custom views". Prefer Apple's documentation for anything not covered here.


## Design rules

- **Glass is for navigation and controls, never for content.** Do not put glass on list rows, cards, cells, images, or text blocks. Content sits underneath; glass floats above it.
- **Use standard components first.** `TabView`, `NavigationStack`/`NavigationSplitView`, toolbars, `sheet`, `popover`, `Menu`, and system button styles adopt glass with no code.
- **Remove custom backgrounds from bars and controls.** Custom `toolbarBackground`, colored tab bars, visual-effect views behind popovers or sheets, and hand-made blur layers interfere with glass and with the scroll edge effect. Flag them on iOS 26+ targets.
- **Use custom glass sparingly** – only for the most important functional elements, such as a floating action cluster over a map or canvas. Overuse distracts from content and costs rendering time.
- **Do not stack glass on glass**, and do not crowd glass elements; keep standard spacing.
- **Color in controls**: use system colors, or custom colors with light, dark, and increased-contrast variants. Use `tint` on glass to signal prominence, not for decoration.
- **Icons in toolbars**: prefer SF Symbols for common actions, always with a text label for accessibility (`Button("Share", systemImage: "square.and.arrow.up", action: share)`). Do not mix text and icon items that share one glass background.
- **Section headers** in lists and forms now render in title case rather than all caps; write headers in title case.
- Accessibility settings (Reduce Transparency, Increase Contrast, Reduce Motion) and the user's glass appearance preference change how glass renders. Standard components adapt automatically; test custom glass with these settings enabled.


## Version gating

All APIs in this file require iOS 26+ unless noted.

- **Target iOS 26+**: use the APIs directly.
- **Target iOS 17–25**: gate custom glass with `if #available(iOS 26, *)` and provide a material fallback. Standard components need no gating – they take the new look automatically on iOS 26 devices.

Put the gate inside a dedicated modifier so call sites stay clean. An availability check never changes at runtime, so this does not cause the identity problems of a `View.if()` helper:

```swift
struct GlassOrMaterial<S: Shape>: ViewModifier {
    let shape: S
    var isInteractive = false

    func body(content: Content) -> some View {
        if #available(iOS 26, *) {
            content.glassEffect(.regular.interactive(isInteractive), in: shape)
        } else {
            content.background(.ultraThinMaterial, in: shape)
        }
    }
}

extension View {
    func glassOrMaterial<S: Shape>(in shape: S, interactive: Bool = false) -> some View {
        modifier(GlassOrMaterial(shape: shape, isInteractive: interactive))
    }
}
```

The `UIDesignRequiresCompatibility` Info.plist key keeps the pre-glass look when building with the new SDK. Treat it as a temporary migration aid; do not add it unasked.


## Custom glass

- `glassEffect()` applies `Glass.regular` in a `Capsule` behind the view. Pass a shape for other forms: `.glassEffect(in: .rect(cornerRadius: 16))`, or `.circle`.
- `Glass` variants: `.regular` (default), `.clear` (more transparent – only over visually rich content such as photos or video, where legibility is still ensured), and `.identity` (no effect – useful to switch glass off without changing the view structure).
- Configure with `.tint(_:)` for prominence and `.interactive()` for elements that respond to touch or pointer: `.glassEffect(.regular.tint(.orange).interactive())`. Make glass interactive only when the element is actually tappable.
- **Apply `glassEffect()` after the modifiers that affect appearance** (padding, frame, font, foreground style). The modifier captures the content as it is at that point.
- Keep shapes consistent across related elements. For shapes next to a screen or sheet edge, prefer `ConcentricRectangle()` so corners follow the container (see `design.md`).

```swift
Label("Directions", systemImage: "arrow.triangle.turn.up.right.diamond")
    .padding()
    .glassEffect(.regular.interactive(), in: .rect(cornerRadius: 16))
```


## Buttons

Prefer system styles to hand-made glass buttons:

```swift
Button("Add to Library", systemImage: "plus", action: add)
    .buttonStyle(.glass)

Button("Continue", action: next)
    .buttonStyle(.glassProminent)
```

Use `.glassProminent` for the single primary action of an area; `.glass` for the rest. `buttonSizing(_:)` (iOS 26) adjusts how buttons size themselves; controls also offer an extra-large size for more prominent labels.


## Multiple glass elements: containers

- Whenever several custom glass views appear together, wrap them in a `GlassEffectContainer`. It renders them together (better performance) and lets their shapes blend and morph. Too many separate containers or glass views outside containers degrade performance.
- The container's `spacing` controls when effects merge: if it is larger than the spacing of the inner stack, shapes blend together even at rest.
- Use `glassEffectUnion(id:namespace:)` to merge several views into a single glass shape – useful for dynamically generated views or views outside one stack.

```swift
GlassEffectContainer(spacing: 20) {
    HStack(spacing: 20) {
        Button("Draw", systemImage: "pencil", action: draw)
            .glassEffect(.regular.interactive())
        Button("Erase", systemImage: "eraser", action: erase)
            .glassEffect(.regular.interactive())
    }
    .labelStyle(.iconOnly)
}
```


## Morphing transitions

To morph glass shapes as views appear and disappear:

1. Declare `@Namespace private var namespace`.
2. Give each glass view `glassEffectID(_:in:)` inside one `GlassEffectContainer`.
3. Change the hierarchy inside `withAnimation`.

```swift
@State private var isExpanded = false
@Namespace private var namespace

var body: some View {
    GlassEffectContainer(spacing: 40) {
        HStack(spacing: 40) {
            Button("Edit", systemImage: "pencil", action: toggle)
                .glassEffect(.regular.interactive())
                .glassEffectID("edit", in: namespace)

            if isExpanded {
                Button("Erase", systemImage: "eraser", action: erase)
                    .glassEffect(.regular.interactive())
                    .glassEffectID("erase", in: namespace)
            }
        }
        .labelStyle(.iconOnly)
    }
}

private func toggle() {
    withAnimation {
        isExpanded.toggle()
    }
}
```

- `glassEffectTransition(_:)` chooses the transition: `.matchedGeometry` (default for effects within the container's spacing) or `.materialize` (for effects farther apart). Apple recommends sticking to these two for consistency.
- `glassEffectID` and `glassEffectTransition` only matter during hierarchy changes and animations.


## Tab bars

- `tabBarMinimizeBehavior(.onScrollDown)` lets the tab bar recede while scrolling content-led screens; it expands when scrolling back. On iOS 27 the navigation-bar equivalent is `toolbarMinimizationBehavior(_:for:)` (see `api.md`).
- `tabViewBottomAccessory { … }` places a persistent accessory (a mini player, a status view) above the tab bar; when the bar is minimized the accessory moves inline. Read `@Environment(\.tabViewBottomAccessoryPlacement)` to adapt its content to the placement.
- Mark the search tab with `Tab(role: .search)` (iOS 18+). On iOS 26 the system separates it at the trailing end of the tab bar. `tabViewSearchActivation(_:)` controls how search activates when that tab is selected.
- Do not color or replace the tab bar background.

```swift
TabView {
    Tab("Library", systemImage: "books.vertical") { LibraryView() }
    Tab("For You", systemImage: "heart") { ForYouView() }
    Tab(role: .search) { SearchView() }
}
.tabBarMinimizeBehavior(.onScrollDown)
.tabViewBottomAccessory {
    NowPlayingBar()
}
```


## Toolbars

- Toolbar items share a glass background with neighbours in the same logical group. Group related actions; keep groupings consistent.
- `ToolbarSpacer(.fixed)` separates groups that should not share a background; `ToolbarSpacer(.flexible)` pushes items apart. On iOS 27, prefer a `ToolbarItemGroup` for related controls such as previous/next (see `api.md`).
- `sharedBackgroundVisibility(.hidden)` on a `ToolbarItem` removes the shared glass and places the item in its own grouping – for status views or custom imagery that should not sit in a pill.
- Hide a toolbar item by hiding the whole item, not the view inside it; an empty item leaves an empty glass capsule. On Xcode 27.2+ / iOS 26.4+, toggle `.hidden()` on the item (see `api.md`).
- `navigationSubtitle(_:)` (iOS 26) adds a subtitle under the navigation title instead of a hand-built principal item.
- iOS 27 overflow, visibility priority, and `contentMarginsRemoved()` are covered in `api.md`.

```swift
.toolbar {
    ToolbarItemGroup(placement: .topBarTrailing) {
        Button("Share", systemImage: "square.and.arrow.up", action: share)
        Button("Favorite", systemImage: "star", action: favorite)
    }
    ToolbarSpacer(.fixed, placement: .topBarTrailing)
    ToolbarItem(placement: .topBarTrailing) {
        Button("More", systemImage: "ellipsis.circle", action: showMore)
    }
}
```


## Custom bars and scroll edges

- Attach custom bars with `safeAreaBar(edge:)` rather than an overlay with guessed padding: it reserves space and applies the system scroll edge effect to content scrolling beneath. Fallback below iOS 26: `safeAreaInset(edge:)` (see `components/top-bar.md`).
- `scrollEdgeEffectStyle(_:for:)` changes the edge effect style, e.g. `.scrollEdgeEffectStyle(.hard, for: .top)` for a crisper divider under dense controls. Leave the automatic style unless there is a legibility problem.


## Split views and edge-to-edge imagery

- Prefer `NavigationSplitView` and `inspector()` for sidebar and inspector layouts; they get glass sidebars and fluid resizing for free.
- Use `backgroundExtensionEffect()` on hero imagery in the detail column so it appears to extend under the sidebar or inspector (mirrored and blurred). Use one per screen; it clips the view.


## Sheets, popovers, and dialogs

- Sheets now have larger corner radii, and partial-height sheets are inset from the screen edges. Check content and controls near the rounded corners, and what peeks through around inset sheets.
- Remove custom backgrounds and visual-effect views from sheets and popovers; use `presentationBackground` only for a deliberate design need.
- Action sheets originate from their source control. Attach `confirmationDialog()` to the triggering control (see `navigation.md`).


## Review checklist

- [ ] No glass on content (rows, cards, images, text blocks).
- [ ] No custom backgrounds on navigation bars, tab bars, toolbars, sheets, or popovers on iOS 26+.
- [ ] Custom glass limited to key functional elements; several together are wrapped in one `GlassEffectContainer`.
- [ ] `glassEffect()` placed after appearance modifiers; `.interactive()` only on tappable elements.
- [ ] System `.glass` / `.glassProminent` button styles instead of hand-made glass buttons.
- [ ] Morphing uses `@Namespace` + `glassEffectID` inside a container, with changes in `withAnimation`.
- [ ] Every toolbar and tab item has a text label (visible or for accessibility); items are hidden as whole items.
- [ ] Custom bars use `safeAreaBar` (iOS 26+) rather than overlays with manual padding.
- [ ] iOS 17–25 targets gate custom glass with `#available(iOS 26, *)` and a material fallback.
- [ ] Custom glass tested with Reduce Transparency, Increase Contrast, and Reduce Motion.
