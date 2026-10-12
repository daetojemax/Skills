# Liquid Glass

Liquid Glass is the iOS 26+ material for the **functional layer** – navigation and controls that float above content. Building with the iOS 26 SDK or later gives standard components (bars, tab bars, sheets, popovers, menus, toggles, sliders, buttons) the new look automatically. Most adoption work is removing custom styling so the system can do its job; custom glass is the exception.

This file holds the rules and decisions. For exact signatures and parameters, look the APIs up (see "Looking up Apple APIs" in `SKILL.md`); Apple's articles "Adopting Liquid Glass" and "Applying Liquid Glass to custom views" are the primary sources.


## Design rules

- **Glass is for navigation and controls, never for content.** No glass on list rows, cards, cells, images, or text blocks.
- **Standard components first.** `TabView`, `NavigationStack` / `NavigationSplitView`, toolbars, `sheet`, `popover`, `Menu`, and system button styles adopt glass with no code.
- **Remove custom backgrounds from bars and controls** on iOS 26+: custom `toolbarBackground`, colored tab bars, visual-effect views behind sheets or popovers, hand-made blurs. They fight the glass and the scroll edge effect.
- **Custom glass sparingly** – only for the most important functional elements, such as a floating control cluster over a map or canvas. Overuse distracts from content and costs rendering time.
- **No glass on glass**, no crowding; keep standard spacing.
- **Color**: system colors, or custom colors with light, dark, and increased-contrast variants. Tint glass to signal prominence, not for decoration.
- **Toolbar icons**: SF Symbols for common actions, always with a text label for accessibility. Do not mix text and icon items that share one glass background.
- **Section headers** in lists and forms render in title case – write them that way.
- Reduce Transparency, Increase Contrast, Reduce Motion, and the user's glass appearance preference all change rendering. Standard components adapt; test custom glass with these settings.


## Version gating

All glass APIs need iOS 26+.

- **Target iOS 26+**: use them directly.
- **Target iOS 17–25**: gate custom glass with `if #available(iOS 26, *)` and a material fallback. Standard components need no gating.

Keep the gate inside one modifier so call sites stay clean. An availability check never flips at runtime, so this does not cause the identity problems of a `View.if()` helper:

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

The `UIDesignRequiresCompatibility` Info.plist key keeps the pre-glass look under the new SDK. Treat it as a temporary migration aid; never add it unasked.


## Custom glass – rules that are easy to get wrong

- **Apply `glassEffect()` after the modifiers that affect appearance** (padding, frame, font, foreground style); it captures the content as it is at that point.
- **`.interactive()` only on elements that are actually tappable.**
- **Several glass views together → one `GlassEffectContainer`.** It renders them in one pass and lets shapes blend and morph; separate glass views and many containers cost performance. Container `spacing` larger than the inner stack's spacing makes shapes merge even at rest.
- **Variants**: `.regular` by default; `.clear` only over visually rich content (photos, video) where legibility is still ensured; `.identity` to switch glass off without changing view structure.
- **Morphing** needs all three: a `@Namespace`, `glassEffectID(_:in:)` on each view inside one container, and the hierarchy change inside `withAnimation`. Stick to the two system transitions – `.matchedGeometry` (default, nearby shapes) and `.materialize` (shapes farther apart than the container spacing).
- `glassEffectUnion(id:namespace:)` merges several views into one glass shape.
- **Buttons**: use `.buttonStyle(.glass)` / `.glassProminent` rather than hand-made glass buttons; `.glassProminent` for the single primary action of an area.
- Keep shapes consistent across related elements; next to screen or sheet edges prefer `ConcentricRectangle()` (`design.md`).


## Bars and navigation

- **Tab bar**: `tabBarMinimizeBehavior(.onScrollDown)` for content-led screens; `tabViewBottomAccessory { }` for a persistent mini player or status (read `tabViewBottomAccessoryPlacement` to adapt it); `Tab(role: .search)` for search, which iOS 26 separates at the trailing end. Never recolor or replace the tab bar background.
- **Toolbars**: neighbouring items share one glass background – group related actions deliberately. `ToolbarSpacer(.fixed)` separates groups; on iOS 27 prefer `ToolbarItemGroup` and the overflow and priority APIs in `api.md`. `sharedBackgroundVisibility(.hidden)` takes an item (status view, custom image) out of the shared pill.
- **Hide whole toolbar items**, never the view inside an item – that leaves an empty glass capsule. On Xcode 27.2+ / iOS 26.4+ toggle `.hidden()` on the item.
- **`navigationSubtitle(_:)`** instead of a hand-built `.principal` title stack.
- **Custom bars**: attach with `safeAreaBar(edge:)`, which reserves space and applies the scroll edge effect; below iOS 26 use `safeAreaInset(edge:)` (`components/top-bar.md`). Change `scrollEdgeEffectStyle` only for a real legibility problem.
- **Split views**: prefer `NavigationSplitView` and `inspector()`; use `backgroundExtensionEffect()` on hero imagery in the detail column, once per screen (it clips the view).


## Sheets, popovers, dialogs

- Sheets have larger corner radii and partial-height sheets are inset from the edges: check content near the corners and what peeks through.
- Remove custom backgrounds and visual-effect views from sheets and popovers; `presentationBackground` only for a deliberate design need.
- Action sheets originate from their source: attach `confirmationDialog()` to the triggering control (`navigation.md`).


## Review checklist

- [ ] No glass on content (rows, cards, images, text blocks).
- [ ] No custom backgrounds on navigation bars, tab bars, toolbars, sheets, or popovers on iOS 26+.
- [ ] Custom glass limited to key functional elements; several together share one `GlassEffectContainer`.
- [ ] `glassEffect()` after appearance modifiers; `.interactive()` only on tappable elements.
- [ ] System `.glass` / `.glassProminent` button styles instead of hand-made glass buttons.
- [ ] Morphing uses `@Namespace` + `glassEffectID` inside a container, with changes in `withAnimation`.
- [ ] Every toolbar and tab item has a text label; items are hidden as whole items.
- [ ] Custom bars use `safeAreaBar` (iOS 26+) rather than overlays with manual padding.
- [ ] iOS 17–25 targets gate custom glass with `#available(iOS 26, *)` and a material fallback.
- [ ] Custom glass tested with Reduce Transparency, Increase Contrast, and Reduce Motion.
