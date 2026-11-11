# Sources

- Apple's `xctrace` skill from Xcode 27, as repackaged in [artemnovichkov/xcode-skills](https://github.com/artemnovichkov/xcode-skills) (commit `4768e8d`, 2026-10-15). It is not in the Xcode 27.0 export (`xcrun agent skills export`).
  - `references/apple/` holds Apple's files unchanged; Apple's `SKILL.md` is renamed to `index.md` so agents do not load it as a second skill.
  - Apple ships it without a license file; it is kept in this private repository for personal use.
- `SKILL.md` and `scripts/` are written for this repository. Concepts from Apple's guide (hang tiers, busy vs. blocked, symbolication) are paraphrased.

Apple's guide relies on `xctrace toc`, `show`, `list tracks`, and `triage`, which xctrace 27.0 and 27.1 (27A9275) do not have. `SKILL.md` checks `xctrace help` and uses Apple's guide when they appear, the export workflow otherwise.

To update Apple's part, copy the folder from a newer export or from the repository above:

```bash
rsync -a --delete <source>/xctrace/references/ xctrace/references/apple/
cp <source>/xctrace/SKILL.md xctrace/references/apple/index.md
```


## Verified on 2026-10-27 (Xcode 27.1, xctrace 27A9275, macOS 26.6)

- `record --launch` of a macOS binary with Time Profiler; `export --toc`; `export --xpath` of `time-profile`, `potential-hangs`, `hang-risks`, `syscall`, `thread-state` (column names as listed in `SKILL.md`).
- iOS Simulator (iPhone 18 Pro, iOS 27.0): `--device <UDID> --attach <pid>` works; `--attach Preferences` fails ("Cannot find process matching name") because the process is listed as "Settings".
- `--recording-options` with a partial JSON fails ("The data couldn't be read because it is missing"); the full JSON from `--show-recording-options` with edited values works and sets `record-waiting-threads="1"` and `hangs-threshold="100"`.
- Test app with a 1.5 s busy main-thread loop and a 1.2 s `Thread.sleep`: both appear in `potential-hangs` as "Hang". Busy window: ~1 sample per ms (278 samples at ~5 ms each with waiting threads on), weight ≈ duration. Blocked window: **0 samples** without `recordWaitingThreads`; with it, one sample of 1.2 s with leaf `__semwait_signal`, and `thread-state` still says "Running".
- System Trace: `blocking_calls.py` finds `semwait_signal` 1.20 s on the main thread with the `+[NSThread sleepForTimeInterval:]` stack; idle `mach_msg2_trap` waits in `__CFRunLoopServiceMachPort` are filtered out.
- `time_profile_top.py` on a recursive CPU workload: `fib(_:)` 96.8 % self, with `--binary` 100 %.
- Template contents (`--show-recording-options`): SwiftUI = Hangs + SwiftUI + Time Profiler; Animation Hitches = Hangs + Time Profiler; Swift Concurrency = Hangs + Points of Interest + Time Profiler.

Not verified: physical devices, `symbolicate` (the test binaries were already symbolicated), SwiftUI/Allocations/Hitches table schemas.
