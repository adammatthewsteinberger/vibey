# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Catch SIGTERM before the process is ready to handle it properly.

Kubernetes sends SIGTERM and waits. Linux treats PID 1 specially: a signal whose
disposition is still ``SIG_DFL`` is **discarded**, not queued -- so a container whose
process has not yet installed a handler does not receive that signal late, it never
receives it at all. The pod then runs until ``terminationGracePeriodSeconds`` expires,
which for a vibey worker is two hours.

The worker already registers its drain handler as the first statement inside the event
loop, before any I/O, and that is still the right place for the *real* handler. It is not
early enough to win this race: everything before it -- interpreter start, importing the
CLI and its dependencies, argument parsing, starting the loop -- is time during which the
signal is thrown away. Measured against a scale-in that deleted a pod 0.2s after its
container started, that window is the whole story.

So this module installs a deliberately tiny handler at import time, whose only job is to
remember. Whatever starts afterwards asks whether SIGTERM already arrived and acts on it
instead of waiting for one that will never come again.
"""

from __future__ import annotations

import signal
import types


class SigtermLatch:
    """A one-bit memory for a SIGTERM that arrived too early to act on."""

    def __init__(self) -> None:
        self._fired = False
        self._armed = False

    @property
    def fired(self) -> bool:
        return self._fired

    def arm(self) -> bool:
        """Install the handler, returning whether it took.

        ``signal.signal`` only works on the main thread. Importing this module from a
        worker thread is legitimate -- a test runner, an embedding host -- and must not
        raise, so a refusal is reported rather than thrown. A process that cannot arm the
        latch simply keeps the old behaviour.
        """
        if self._armed:
            return True
        try:
            signal.signal(signal.SIGTERM, self._remember)
        except ValueError:
            return False
        self._armed = True
        return True

    def release(self) -> None:
        """Give SIGTERM back to the default disposition.

        Called once the real handler is installed. Not strictly required -- the real
        handler replaces this one -- but a latch that outlives its purpose is a handler
        nobody is looking at, and this keeps the disposition honest.
        """
        if not self._armed:
            return
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        self._armed = False

    def _remember(self, _signum: int, _frame: types.FrameType | None) -> None:
        # Deliberately only this. A signal handler runs between bytecodes, on whatever
        # stack happens to be executing; doing anything that can block or allocate
        # meaningfully here is how a drain turns into a hang.
        self._fired = True


#: Armed on import, which is the earliest point the CLI controls.
SIGTERM_LATCH = SigtermLatch()
