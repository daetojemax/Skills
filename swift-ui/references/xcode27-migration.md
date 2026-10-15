# Xcode 27 SDK: new compile errors and their fixes

Building existing SwiftUI code with the Xcode 27 SDK can surface new errors, because `@State` became a macro and `@ViewBuilder` was unified into `@ContentBuilder`. These apply to every deployment target – they come from the SDK, not the OS. Use this file when a project that compiled with Xcode 26 fails with Xcode 27.

Source: Apple's `swiftui-whats-new-27` skill from Xcode 27.0; cases marked *verified* were reproduced with the iOS 27.0 SDK.


## `@State` is a macro

- **Memberwise init missing for views with `@State`** *(verified)*. A view whose stored members are all `private` normally gets a private memberwise initializer usable from extensions; with `@State` it no longer does, and calls fail with `extraneous argument label …`. Fix: write the initializer explicitly.
- **`variable 'self.x' used before being initialized`** when an `init` assigns a `@State` property before other stored properties. Fix: drop the initial value from the `@State` declaration and assign it only in `init`. Do **not** just reorder the assignments.
- **Assigning in `init` to a `@State` that already has an initial value is an anti-pattern even when it compiles**: `body` still sees the declaration's value. Initialize each `@State` in exactly one place (see `data.md`).
- **`invalid redeclaration of synthesized property '_x'`** when another property wrapper is composed with `@State`: both synthesize the same backing name. Remove the redundant wrapper or restructure; if unsure, ask the user.
- New code: always `@State private` (Apple's guidance and `data.md`). Existing non-private `@State`: recommend `private`, but do not change it unasked – callers may rely on it.


## `@ContentBuilder` replaces `@ViewBuilder`

`@ViewBuilder` still compiles as a name for the same builder; existing uses need no change. The unified builder no longer constrains its contents to `View`, which removes a disambiguation the compiler used to rely on:

- **`ambiguous use of 'opacity'` / `'blendMode'`** in `overlay(…)` or `background(…)` with a style expression as a direct argument, e.g. `.overlay(Color.blue.opacity(0.7).blendMode(.overlay))`. Fix: use the builder-closure form, `.overlay { Color.blue.opacity(0.7).blendMode(.overlay) }`.
- **`ambiguous use of 'red'`** (or `.clear`, `.green`, a type name such as `Text`) when another module declares a type or static member with a SwiftUI name. In modular projects, check `Design` and other local modules for their own `Color`, `Text`, `Image`, or `Font` types. Fix: qualify the type (`SwiftUI.Color.clear`) or rename the module's type or members.
- **`cannot convert … TupleContent<…> to … TupleView<(…)>`** where `TupleView` is spelled inside a generic parameter (e.g. `VStack<TupleView<(Text, Text)>>`). Fix: prefer `some View`; if the concrete type must be spelled, use `TupleContent<Text, Text>`; below an OS 27 deployment target, construct `TupleView((…))` explicitly inside the builder.
- **`return type of property 'body' requires that 'EmptyMapContent' conform to 'View'`** for an empty builder block – including a `#if` without `#else` – in a file that sees MapKit (even indirectly, without member import visibility). Fix: put `EmptyView()` in the block.
- **Swift Charts type-check timeouts** with deeply branching chart content, only when the deployment target is below OS 27. Fix: move the branching into a dedicated `@ChartContentBuilder` function.
