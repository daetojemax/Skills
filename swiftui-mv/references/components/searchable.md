# Searchable

## Intent

Use `searchable` to add native search UI with optional scopes and async results.

## Core patterns

- Bind `searchable(text:)` to local state.
- Use `.searchScopes` for multiple search modes.
- Restart the search with `.task(id:)` keyed on everything that affects results (query and scope); sleeping first inside the task debounces it, because a new key cancels the old task.
- Show `ContentUnavailableView.search` for empty results; it includes the search term automatically.
- In a tab app on iOS 18+, prefer a dedicated `Tab(role: .search)` (see `navigation.md` and `liquid-glass.md`).
- Show placeholders or progress states while results load.

## Example: searchable with scopes

```swift
@MainActor
struct ExploreView: View {
  @State private var searchQuery = ""
  @State private var searchScope: SearchScope = .all
  @State private var isSearching = false
  @State private var results: [SearchResult] = []

  var body: some View {
    List {
      if isSearching {
        ProgressView()
      } else {
        ForEach(results) { result in
          SearchRow(result: result)
        }
      }
    }
    .searchable(
      text: $searchQuery,
      placement: .navigationBarDrawer(displayMode: .always),
      prompt: Text("Search")
    )
    .searchScopes($searchScope) {
      ForEach(SearchScope.allCases, id: \.self) { scope in
        Text(scope.title)
      }
    }
    .task(id: SearchKey(query: searchQuery, scope: searchScope)) {
      await runSearch()
    }
    .overlay {
      if !isSearching, !searchQuery.isEmpty, results.isEmpty {
        ContentUnavailableView.search
      }
    }
  }

  private func runSearch() async {
    guard !searchQuery.isEmpty else {
      results = []
      return
    }
    do {
      try await Task.sleep(for: .milliseconds(250))
      isSearching = true
      defer { isSearching = false }
      results = try await fetchResults(query: searchQuery, scope: searchScope)
    } catch {
      // Cancellation means a newer query replaced this one.
    }
  }
}

private struct SearchKey: Equatable {
  let query: String
  let scope: SearchScope
}
```

## Design choices to keep

- Show a placeholder when search is empty or has no results.
- Debounce input to avoid spamming the network.
- Keep search state local to the view.

## Pitfalls

- Avoid running searches for empty strings.
- Don’t block the main thread during fetch.
