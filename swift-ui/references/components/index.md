# Components index

Example-driven patterns for building screens. Read only the file for the component at hand. Every pattern follows the rules in the parent `references/` files; if an example ever conflicts with a rule, the rule wins.

Navigation, tabs, sheets, and deep links live in `../navigation.md`; app wiring and async state in `../architecture.md`; Liquid Glass in `../liquid-glass.md`.

| Component | File | Use when |
| --- | --- | --- |
| Tab sidebars, sections, dynamic tabs | `tabview.md` | iPad/Mac sidebars, `TabSection`, data-driven tabs (iOS 18+) |
| Split views and columns | `split-views.md` | Multi-column layouts, inspectors, a permanent secondary column |
| Form and settings | `form.md` | Settings screens, grouped input, modal data entry |
| Controls | `controls.md` | Toggles, sliders, pickers |
| List and Section | `list.md` | Feeds, settings rows, scroll-to-top |
| ScrollView and lazy stacks | `scrollview.md` | Custom feeds, chat, horizontal strips |
| Grids | `grids.md` | Icon pickers, galleries, square thumbnails |
| Scroll-reveal surfaces | `scroll-reveal.md` | Detail screens that reveal a second layer on scroll (iOS 18+) |
| Searchable | `searchable.md` | Native search, scopes, debounced async results |
| Focus | `focus.md` | Field chaining, keyboard focus, dynamic fields |
| Input toolbar | `input-toolbar.md` | Chat or composer with a bar pinned above the keyboard |
| Top bar | `top-bar.md` | Pinned selector or pill row under the navigation bar |
| Title menus | `title-menus.md` | Filters or context switching from the navigation title |
| Overlays and toasts | `overlay.md` | Transient banners, toasts, loaders |
| Media | `media.md` | Remote images, media strips, a full-screen viewer |
| Matched transitions | `matched-transitions.md` | Zoom transitions from thumbnails (iOS 18+), in-place matched geometry |
| Loading and placeholders | `loading-placeholders.md` | Redacted skeletons, empty and error states |
| Haptics | `haptics.md` | Tactile feedback with `sensoryFeedback` |
| Theming | `theming.md` | App-wide theme tokens and Dynamic Type |
| Lightweight clients | `lightweight-clients.md` | Closure-based, swappable API clients injected into stores |
| Previews | `previews.md` | `#Preview` setup, fixtures, mock environments |
| macOS Settings | `macos-settings.md` | A Mac `Settings` scene |
| Menu bar commands | `menu-bar.md` | Mac/iPad menu bar commands |

## Adding a component

Create `<component>.md` with: intent, core patterns, a minimal example, design choices to keep, and pitfalls. Check the example against `../api.md` and `../views.md` before adding it, then list it here.
