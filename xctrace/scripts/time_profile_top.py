#!/usr/bin/env python3
"""Summarize a time-profile table exported by `xctrace export --xpath`.

Usage:
  xcrun xctrace export --input app.trace \
    --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
    --output tp.xml
  python3 time_profile_top.py tp.xml [--thread "Main Thread"] [--process MyApp] [--binary MyApp]
                               [--window START DURATION] [--top 25]

Prints the heaviest functions by self weight (the leaf frame) and by total
weight (any frame of the stack, counted once per sample), the heaviest
stacks. A running thread is sampled about every millisecond; with
recordWaitingThreads a waiting thread gets one sample whose weight is the whole
wait, so a high "waiting" weight means a blocked rather than a busy thread. --window limits samples to a time range in seconds from the start of
the recording, e.g. a hang from the potential-hangs table. Weights are summed from the `weight` column, in milliseconds.
The export deduplicates elements with id/ref; this script resolves them.
"""
import argparse
import collections
import sys
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser()
    p.add_argument("xml")
    p.add_argument("--thread", help="substring of the thread name, e.g. 'Main Thread'")
    p.add_argument("--process", help="substring of the process name")
    p.add_argument("--binary", help="only count frames from binaries whose name contains this")
    p.add_argument("--window", nargs=2, type=float, metavar=("START", "DURATION"),
                   help="seconds from the start of the recording")
    p.add_argument("--top", type=int, default=25)
    a = p.parse_args()

    by_id = {}

    def resolve(el):
        ref = el.get("ref")
        return by_id[ref] if ref is not None else el

    rows = []
    for _, el in ET.iterparse(a.xml, events=("end",)):
        if el.get("id") is not None:
            by_id[el.get("id")] = el
        if el.tag == "row":
            rows.append(el)

    self_w = collections.Counter()
    total_w = collections.Counter()
    stack_w = collections.Counter()
    samples = 0
    long_w = 0.0
    all_w = 0.0
    for row in rows:
        thread = process = weight = bt = when = None
        for child in row:
            c = resolve(child)
            if c.tag == "sample-time":
                when = int(c.text or 0) / 1e9
            elif c.tag == "thread":
                thread = c.get("fmt", "")
            elif c.tag == "process":
                process = c.get("fmt", "")
            elif c.tag == "weight":
                weight = int(c.text or 0) / 1e6
            elif c.tag in ("tagged-backtrace", "backtrace"):
                bt = c
        if bt is None or weight is None:
            continue
        if a.window and (when is None or not a.window[0] <= when < a.window[0] + a.window[1]):
            continue
        if a.thread and a.thread not in (thread or ""):
            continue
        if a.process and a.process not in (process or ""):
            continue
        frames = []
        for f in bt.iter("frame"):
            f = resolve(f)
            binary = f.find("binary")
            binary = resolve(binary).get("name", "?") if binary is not None else "?"
            if a.binary and a.binary not in binary:
                continue
            frames.append(f"{f.get('name') or f.get('addr')}  [{binary}]")
        if not frames:
            continue
        all_w += weight
        samples += 1
        if weight >= 10:
            long_w += weight
        self_w[frames[0]] += weight
        for name in set(frames):
            total_w[name] += weight
        stack_w[" <- ".join(frames[:6])] += weight

    print(f"samples matched: {all_w:.0f} ms")
    print(f"samples: {samples}; weight in samples of 10 ms or more (waiting): {long_w:.0f} ms\n")
    for title, counter in (("SELF", self_w), ("TOTAL", total_w)):
        print(f"== {title} (ms, % of matched)")
        for name, w in counter.most_common(a.top):
            print(f"{w:9.1f}  {100 * w / all_w:5.1f}%  {name}")
        print()
    print("== HEAVIEST STACKS (leaf first, 6 frames)")
    for s, w in stack_w.most_common(min(a.top, 10)):
        print(f"{w:9.1f}  {s}")


if __name__ == "__main__":
    sys.exit(main())
