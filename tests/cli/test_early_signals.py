# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The latch that catches SIGTERM before anything can act on it.

Linux discards a signal sent to PID 1 while its disposition is still ``SIG_DFL`` -- it is
not queued for later. A container therefore loses any termination signal that arrives
before its process installs a handler, and the pod runs on until its grace period expires.
For a vibey worker that is two hours, and it was observed on minikube: a pod deleted 0.2s
after its container started sat through the whole window claiming jobs nobody wanted.
"""

from __future__ import annotations

import os
import signal
import threading

from vibey.cli.early_signals import SigtermLatch
from vibey.cli.interfaces import SigtermLatchInterface


def _deliver_sigterm() -> None:
    os.kill(os.getpid(), signal.SIGTERM)


def test_a_latch_starts_empty_and_remembers_one_signal() -> None:
    latch = SigtermLatch()
    assert not latch.fired
    assert latch.arm()
    try:
        _deliver_sigterm()
        assert latch.fired
    finally:
        latch.release()


def test_arming_twice_is_idempotent() -> None:
    """`arm()` is called at import; a second call must not reinstall or report failure."""
    latch = SigtermLatch()
    assert latch.arm()
    try:
        assert latch.arm()
    finally:
        latch.release()


def test_release_restores_the_default_disposition() -> None:
    latch = SigtermLatch()
    latch.arm()
    latch.release()
    assert signal.getsignal(signal.SIGTERM) is signal.SIG_DFL


def test_releasing_a_latch_that_was_never_armed_does_nothing() -> None:
    before = signal.getsignal(signal.SIGTERM)
    SigtermLatch().release()
    assert signal.getsignal(signal.SIGTERM) is before


def test_arming_off_the_main_thread_declines_instead_of_raising() -> None:
    """Importing the CLI from a worker thread is legitimate and must not explode.

    `signal.signal` only works on the main thread. A process that cannot arm the latch
    simply keeps the old behaviour, so the refusal is reported rather than thrown.
    """
    result: list[bool] = []

    def _try() -> None:
        result.append(SigtermLatch().arm())

    thread = threading.Thread(target=_try)
    thread.start()
    thread.join()
    assert result == [False]


def test_the_latch_satisfies_its_declared_interface() -> None:
    assert isinstance(SigtermLatch(), SigtermLatchInterface)
