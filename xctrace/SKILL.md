---
name: xctrace
description: Records and reads Instruments traces from the command line with xctrace – Time Profiler, System Trace, Hangs, SwiftUI and other templates on macOS, the iOS Simulator, or a device; finding where CPU time goes, triaging hangs as busy or blocked, symbolicating, and reading .trace and .atrc files. Use for profiling and performance work when you need runtime evidence (an app is slow, hangs, uses too much CPU) or when the user hands you a trace.
license: MIT
metadata:
  version: "1.0.0"
  based-on: "Apple's xctrace skill (Xcode 27, via artemnovichkov/xcode-skills) plus a workflow verified with xctrace 27.1 – see SOURCES.md"
---

# xctrace

`xctrace` is the command-line interface to Instruments: it records traces and reads `.trace` and `.atrc` files. Use it when code review is not enough and you need runtime evidence. For SwiftUI-specific diagnosis (invalidation, identity, layout), pair it with the `swift-ui` skill's performance audit.


## Step 0: Which command set is installed

```bash
xcrun xctrace version
xcrun xctrace help
```

- If `help` lists **`toc`, `show`, `list tracks`, and `triage`**, read Apple's guide in `references/apple/` (start with `index.md`, then `xctrace-overview.md`; `xctrace-hangs-triage.md` for hangs). Those commands give curated call trees and hang triage and are preferred over `export`.
- Otherwise (xctrace 27.0 and 27.1 only have `record`, `import`, `export`, `remodel`, `symbolicate`, `list`), use the workflow below: record, export tables as XML, and summarize them with the scripts in `scripts/`.

Concepts in Apple's guide still apply either way: busy vs. blocked hangs, hang severity tiers, symbolication, and stochastic vs. deterministic call trees.


## Recording

```bash
xcrun xctrace list templates
xcrun xctrace list devices
```

Useful templates: **Time Profiler** (CPU samples plus Hangs), **System Trace** (thread states, system calls, context switches), **SwiftUI** (SwiftUI updates plus Time Profiler and Hangs), **Animation Hitches**, **Allocations**, **Leaks**, **App Launch**, **Swift Concurrency**, **Data Persistence**.

```bash
# macOS process: launch it
xcrun xctrace record --template 'Time Profiler' --output app.trace --launch -- ./MyTool arg

# iOS Simulator: launch the app, then attach by PID (attaching by name can fail;
# the process name is the display name, e.g. "Settings" for com.apple.Preferences)
xcrun simctl launch <UDID> com.example.MyApp          # prints "com.example.MyApp: <pid>"
xcrun xctrace record --template 'Time Profiler' --device <UDID> --attach <pid> \
  --time-limit 10s --output app.trace
```

- Always pass `--output` and, when attaching, `--time-limit`; otherwise recording runs until Ctrl-C.
- Reproduce **one** interaction per recording. The user may need to perform it in the simulator or on the device while you record; tell them when recording starts and how long it runs.
- Profile a **Release** build when measuring speed; Debug builds and the Simulator distort timing. Simulator traces are fine for finding *where* time goes and for hangs that reproduce reliably; confirm absolute numbers on a device.
- Add `--no-prompt` in non-interactive runs.

**Recording options.** `--show-recording-options` prints the configurable options of a template as JSON. To change one, save the **complete** JSON, edit it, and pass it back – a file with only some keys fails with "The data couldn't be read because it is missing":

```bash
xcrun xctrace record --template 'Time Profiler' --show-recording-options > opts.json
# edit: "Time Profiler": { "recordWaitingThreads": true }, "Hangs": { "hangsThreshold": 100 }
xcrun xctrace record --template 'Time Profiler' --recording-options opts.json --output app.trace --launch -- ./MyTool
```

`recordWaitingThreads` adds stacks of blocked threads to the time profile (needed to see blocked hangs there); `hangsThreshold` (ms, default 250) lowers the Hangs reporting threshold.


## Reading a trace

```bash
xcrun xctrace export --input app.trace --toc            # runs, target process, tables (by schema)
xcrun xctrace export --input app.trace \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' --output tp.xml
```

The table of contents lists each table by `schema`; some schemas appear several times with different attributes (for example several `os-signpost` tables). Add an attribute to the XPath when needed, e.g. `table[@schema="os-signpost" and @category="PointsOfInterest"]`. Exporting an empty table still prints its columns.

The XML deduplicates repeated values: the first occurrence carries `id="N"`, later ones are `<… ref="N"/>`. Never grep stacks or count values in the raw XML – resolve references, as the scripts do. Exports get large (System Trace: tens of MB for a few seconds), so write them to a file and summarize instead of printing them.

Tables worth knowing:

| Schema | Template | Content |
| --- | --- | --- |
| `time-profile` | Time Profiler, SwiftUI | CPU samples: time, thread, weight, backtrace |
| `potential-hangs` | Time Profiler, SwiftUI, System Trace | Hang intervals: start, duration, type, thread |
| `hang-risks` | same | Runtime warnings about hang risks, with backtraces |
| `syscall` | System Trace | Every system call: duration, wait time, backtrace |
| `thread-state` | System Trace | Thread state intervals (running, blocked, …) |
| `os-signpost`, `os-log` | most | Signposts and log messages, including your own |

For other templates (SwiftUI, Allocations, Animation Hitches), read the table of contents first and export the relevant table; do not assume schema names.

### Where does CPU time go

```bash
python3 scripts/time_profile_top.py tp.xml --process MyApp --top 25
python3 scripts/time_profile_top.py tp.xml --thread "Main Thread" --binary MyApp
```

It prints the heaviest functions by self weight (leaf frame) and total weight, and the heaviest stacks. `--binary` keeps only your own frames, `--thread` and `--process` filter by name substring, `--window START DURATION` limits to a time range in seconds from the start of the recording. Samples are statistical: a Time Profiler sample every ~1 ms on a running thread. Do not read small differences as meaningful.


## Hangs

A hang is a period when the main thread cannot handle input or update the UI. Severity tiers used by Apple's tools: above 33 ms potential interaction delay, 100 ms brief unresponsiveness, 250 ms microhang, 500 ms hang, 2 s severe hang. Frame drops during animation and scrolling are hitches – a separate problem, recorded with the Animation Hitches template.

1. Record with Time Profiler (or SwiftUI) while the user reproduces the freeze. Lower `hangsThreshold` if the problem is short.
2. Export `potential-hangs` to get start and duration of each hang (`fmt` attributes give readable times).
3. For each hang, summarize the main thread for exactly that window:
   ```bash
   python3 scripts/time_profile_top.py tp.xml --thread "Main Thread" --window 3.98 1.2
   ```
4. Decide **busy vs. blocked** before reading stacks:
   - **Busy:** the window has about one sample per millisecond and the matched weight is close to the hang's duration. Read the heaviest stacks and your own frames: that is the work to move off the main actor or make cheaper.
   - **Blocked:** few or no samples in the window. Without `recordWaitingThreads`, a blocked main thread produces **no samples at all**; with it, the wait shows up as one sample whose weight is the whole wait (the script's "waiting" figure). Find what it waited on:
     ```bash
     xcrun xctrace record --template 'System Trace' --output st.trace …
     xcrun xctrace export --input st.trace \
       --xpath '/trace-toc/run[@number="1"]/data/table[@schema="syscall"]' --output syscall.xml
     python3 scripts/blocking_calls.py syscall.xml --process MyApp --min-ms 100 --window 3.98 1.2
     ```
     It lists long system calls on the main thread with their stacks (a lock, a semaphore, synchronous I/O, a `sleep`, a synchronous XPC call). Idle run-loop waits are filtered out.
   - A hang can be both; say which dominates.
5. Report each hang with its time, duration, category, the responsible frames from your code, and the evidence (script output). If the trace lacks the data you need (no waiting-thread stacks, no System Trace), say so and ask for a new recording rather than guessing.


## Symbolication

Frames shown as addresses (`0x10ba0fb8c (MyApp +0xa2fb97) <UUID>`) need symbols. Match the build by UUID, then symbolicate:

```bash
dwarfdump --uuid path/to/MyApp.app.dSYM
xcrun xctrace symbolicate --input app.trace --dsym path/to/dSYMs --output app-symbolicated.trace
```

`--dsym` may be a directory (searched recursively); without it xctrace searches the system. A rebuilt binary has a different UUID even from identical source. If no matching dSYM is found, ask the user for it.


## Pitfalls

- A Time Profiler trace without `recordWaitingThreads` cannot explain a blocked thread – absence of samples is the clue, not a gap in the data.
- `mach_msg` waits inside `__CFRunLoopServiceMachPort` are an idle run loop, not a blocked thread.
- Short-running processes yield few samples; make the workload run long enough (seconds) to get a stable picture.
- `--attach <name>` matches the process's display name, which can differ from the executable or bundle name; prefer the PID.
- Recording requires the target to be running (attach) or launchable on that device; for physical devices, the device must be paired and unlocked.
- The scripts read the XML schemas of xctrace 27.1. If a newer xctrace changes the format, check the raw XML header (`<schema>` columns) and adjust, or switch to `show`/`triage` if they exist.
