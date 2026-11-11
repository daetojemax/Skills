#!/usr/bin/env python3
"""List long system calls from a System Trace – what a blocked thread waited on.

Usage:
  xcrun xctrace export --input app.trace \
    --xpath '/trace-toc/run[@number="1"]/data/table[@schema="syscall"]' \
    --output syscall.xml
  python3 blocking_calls.py syscall.xml [--thread "Main Thread"] [--process MyApp]
                            [--min-ms 100] [--window START DURATION] [--frames 12]

Prints each syscall that lasted at least --min-ms, with its start (seconds from
the start of the recording), duration, wait time, and the top of its stack.
Idle run-loop waits (mach_msg inside __CFRunLoopServiceMachPort) are skipped:
they mean the thread had nothing to do, not that it was blocked.
"""
import argparse
import sys
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser()
    p.add_argument("xml")
    p.add_argument("--thread", default="Main Thread", help="substring of the thread name")
    p.add_argument("--process", help="substring of the process name")
    p.add_argument("--min-ms", type=float, default=100)
    p.add_argument("--window", nargs=2, type=float, metavar=("START", "DURATION"),
                   help="seconds from the start of the recording; calls overlapping it are shown")
    p.add_argument("--frames", type=int, default=12)
    a = p.parse_args()

    by_id = {}
    rows = []
    for _, el in ET.iterparse(a.xml, events=("end",)):
        if el.get("id") is not None:
            by_id[el.get("id")] = el
        if el.tag == "row":
            rows.append(el)

    def resolve(el):
        ref = el.get("ref")
        return by_id[ref] if ref is not None else el

    found = 0
    for row in rows:
        cells = [resolve(c) for c in row]
        get = lambda tag: next((c for c in cells if c.tag == tag), None)
        thread, process, call = get("thread"), get("process"), get("syscall")
        start, duration, waiting = get("start-time"), get("duration"), get("duration-waiting")
        bt = next((c for c in cells if c.tag.endswith("backtrace")), None)
        if None in (thread, start, duration):
            continue
        if a.thread not in thread.get("fmt", ""):
            continue
        if a.process and (process is None or a.process not in process.get("fmt", "")):
            continue
        t0, dur = int(start.text) / 1e9, int(duration.text) / 1e9
        if dur * 1000 < a.min_ms:
            continue
        if a.window and (t0 + dur <= a.window[0] or t0 >= a.window[0] + a.window[1]):
            continue
        frames = [resolve(f).get("name") or resolve(f).get("addr") for f in bt.iter("frame")] if bt is not None else []
        if "__CFRunLoopServiceMachPort" in frames[:6]:
            continue
        found += 1
        wait = f", waiting {waiting.get('fmt')}" if waiting is not None else ""
        print(f"{t0:8.3f}s  {call.get('fmt') if call is not None else '?'}  {duration.get('fmt')}{wait}  [{thread.get('fmt')}]")
        for name in frames[: a.frames]:
            print(f"            {name}")
        print()
    if not found:
        print("no matching calls")


if __name__ == "__main__":
    sys.exit(main())
