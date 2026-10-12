# Working with predicates

SwiftData predicates support only a subset of Swift functionality. Some things are marked as being unsupported, meaning that they will not build. Other things are *not* marked as unsupported and yet are still not supported, meaning that they will build but crash at runtime.

This guide contains specific guidance on what to use and when.


## String matching

When writing a query predicate to perform string matching, always use `localizedStandardContains()` rather than trying to use `lowercased().contains()` or similar.

For example, this is correct:

```swift
@Query(filter: #Predicate<Movie> {
    $0.name.localizedStandardContains("titanic")
}) private var movies: [Movie]
```


## hasPrefix()

`hasPrefix()` and `hasSuffix()` are not supported in SwiftData predicates. If you want to use `hasPrefix()`, you should use `starts(with:)` instead, like this:

```swift
@Query(filter: #Predicate<Website> {
    $0.type.starts(with: "https://apple.com")
}) private var appleLinks: [Website]
```


## Unsupported predicates

Many common methods have no equivalent in SwiftData, and will not compile. For example, all these common operations are not supported:

- `String.hasSuffix()`
- `String.lowercased()`
- `Sequence.map()`
- `Sequence.reduce()`
- `Sequence.count(where:)`
- `Collection.first`

Custom operators are also not allowed.


## Dangerous predicates

Some SwiftData predicates will compile cleanly then fail or even crash at runtime.

For example, this is a valid predicate designed to show only movies that have a non-empty cast list:

```swift
@Query(filter: #Predicate<Movie> { !$0.cast.isEmpty }, sort: \Movie.name) private var movies: [Movie]
```

However, *this* query looks like it does the same thing, but will crash at runtime:

```swift
@Query(filter: #Predicate<Movie> { $0.cast.isEmpty == false }, sort: \Movie.name) private var movies: [Movie]
```

Never attempt to create query predicates that use computed properties, `@Transient` properties, or use custom `Codable` struct data. They might compile cleanly, but they will crash at runtime.

All predicates must rely on data that is actually stored in the database as `@Model` classes.

Never attempt to use regular expressions in predicates. They will compile cleanly then fail at runtime. So, this is *not* allowed:

```swift
@Query(filter: #Predicate<Movie> {
    $0.name.contains(/Titanic/)
}, sort: \Movie.name)
private var movies: [Movie]
```


## Capture values outside the predicate

Compute dates, search strings, and other inputs before building the predicate, and refer to the captured constants inside it. Do not call functions or static members such as `Date.now` inside `#Predicate` – `$0.endDate < Date.now` does not compile:

```swift
let now = Date.now
let expired = #Predicate<Trip> { $0.endDate < now }
```


## Dynamic queries

When filter or sort depends on input, rebuild the `@Query` in the view's initializer:

```swift
struct TripList: View {
    @Query private var trips: [Trip]

    init(searchText: String) {
        _trips = Query(
            filter: #Predicate<Trip> {
                searchText.isEmpty || $0.name.localizedStandardContains(searchText)
            },
            sort: \.startDate
        )
    }

    var body: some View {
        List(trips) { trip in
            TripRow(trip: trip)
        }
    }
}
```

- Always give user-visible lists an explicit sort order.
- When several screens show the same subset (a list and a map, a list and a badge count), build the predicate in one static helper on the model, e.g. `Trip.predicate(searchText:)`, so they cannot drift apart.
- Filter in the predicate, not with `.filter { }` on the results in `body`.
