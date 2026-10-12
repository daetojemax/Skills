# Haptics

## Intent

Reinforce meaningful user actions – selection changes, success, failure, a completed refresh – with subtle tactile feedback, and respect the user's preferences.

## Core patterns

- Use `sensoryFeedback(_:trigger:)` (iOS 17). It is declarative, driven by a value change, and needs no UIKit generators or a shared manager.
- Choose the feedback that matches the moment: `.selection` for picking, `.success` / `.warning` / `.error` for outcomes, `.impact(weight:intensity:)` for physical metaphors, `.increase` / `.decrease` for steppers.
- Use the `condition:` or closure variants when feedback depends on the old and new values.
- Gate optional haptics behind an app preference when the app offers one.

## Examples

```swift
// Selection feedback when the tab changes.
TabView(selection: $selectedTab) { /* tabs */ }
    .sensoryFeedback(.selection, trigger: selectedTab)

// Outcome feedback driven by a save result.
@State private var saveResult: SaveResult?

Form { /* … */ }
    .sensoryFeedback(trigger: saveResult) { _, newValue in
        switch newValue {
        case .success: .success
        case .failure: .error
        case nil: nil
        }
    }

// Only when the user has haptics enabled.
.sensoryFeedback(.impact(weight: .light), trigger: refreshCount) { _, _ in
    preferences.hapticsEnabled
}
```

## Design choices to keep

- Haptics should be subtle and tied to the action that caused them – keep triggers in the view, not deep in services.
- One haptic per action; do not fire several in quick succession.

## Pitfalls

- Do not reach for `UIImpactFeedbackGenerator` and friends in SwiftUI code; use them only inside UIKit integrations.
- The trigger must actually change for feedback to fire; an equal-value assignment does nothing.
