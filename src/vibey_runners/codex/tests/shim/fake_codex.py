#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fake `codex` CLI for tests. Driven by FAKE_CODEX_SCRIPT and FAKE_CODEX_MODE."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

HUGE_LINE_BYTES = 2 * 1024 * 1024 + 1
HANG_SECONDS = 3600


def _emit_script() -> None:
    path = os.environ.get("FAKE_CODEX_SCRIPT")
    if not path:
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            sys.stdout.write(line)
            sys.stdout.flush()


def _stream() -> int:
    _emit_script()
    print("fake-codex: mode=stream", file=sys.stderr, flush=True)
    return 0


def _hang() -> int:
    print("fake-codex: mode=hang", file=sys.stderr, flush=True)
    time.sleep(HANG_SECONDS)
    return 0


def _exit_nonzero() -> int:
    _emit_script()
    print("fake-codex: mode=exit_nonzero", file=sys.stderr, flush=True)
    return 2


def _huge_line() -> int:
    sys.stdout.write("A" * HUGE_LINE_BYTES + "\n")
    sys.stdout.flush()
    print("fake-codex: mode=huge_line", file=sys.stderr, flush=True)
    return 0


def _both_streams() -> int:
    """Write enough to both pipes that a sequential reader deadlocks."""
    out_line = ("O" * 64 + "\n").encode()
    err_line = ("E" * 64 + "\n").encode()
    for i in range(8_000):
        sys.stdout.buffer.write(out_line)
        sys.stderr.buffer.write(err_line)
        if i % 100 == 0:
            sys.stdout.buffer.flush()
            sys.stderr.buffer.flush()
    sys.stdout.buffer.flush()
    print("fake-codex: mode=both_streams", file=sys.stderr, flush=True)
    return 0


def _stdin_probe() -> int:
    is_tty = sys.stdin.isatty()
    eof = sys.stdin.read(1) == ""
    msg = f"fake-codex: mode=stdin_probe tty={is_tty} eof={eof}"
    print(msg, flush=True)
    print(msg, file=sys.stderr, flush=True)
    return 0


def _orphan_child() -> int:
    child_src = (
        "import signal, time\n"
        "signal.signal(signal.SIGHUP, signal.SIG_IGN)\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "time.sleep(3600)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", child_src],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(
        f"fake-codex: orphan parent_pid={os.getpid()} child_pid={proc.pid}",
        file=sys.stderr,
        flush=True,
    )
    marker = os.environ.get("FAKE_CODEX_ORPHAN_MARKER")
    if marker:
        Path(marker).write_text(f"{os.getpid()} {proc.pid}\n", encoding="utf-8")
    time.sleep(HANG_SECONDS)
    return 0


def main() -> int:
    mode = os.environ.get("FAKE_CODEX_MODE", "stream")
    if mode == "hang":
        return _hang()
    if mode == "exit_nonzero":
        return _exit_nonzero()
    if mode == "orphan_child":
        return _orphan_child()
    if mode == "huge_line":
        return _huge_line()
    if mode == "both_streams":
        return _both_streams()
    if mode == "stdin_probe":
        return _stdin_probe()
    return _stream()


if __name__ == "__main__":
    raise SystemExit(main())
