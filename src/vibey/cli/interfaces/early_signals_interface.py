# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The contract for remembering a termination signal that arrived during boot."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SigtermLatchInterface(Protocol):
    """Records that SIGTERM was delivered before anything was ready to act on it."""

    @property
    def fired(self) -> bool:
        """Whether SIGTERM has been delivered since the latch was armed."""
        ...

    def arm(self) -> bool:
        """Install the handler. False if this process cannot (not the main thread)."""
        ...

    def release(self) -> None:
        """Hand SIGTERM back to the default disposition."""
        ...
