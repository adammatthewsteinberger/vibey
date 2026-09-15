"""Internal buffered-shipper base for logging transports.

``_BufferedShipper`` is a ``logging.Handler`` base class that provides the
transport-agnostic machinery shared by every network/storage logging sink in
``vibey_bootstrap.transports``:

- **Never blocks** the calling thread — ``emit()`` only appends to an in-memory
  buffer; a daemon thread does the I/O.
- **Never raises** — every public method is wrapped; failures bump a counter and
  route through ``handleError``.
- **Bounded** — a ``deque(maxlen=…)`` drops the oldest record under sustained
  backpressure rather than growing without limit; drops are counted.
- **Flushes** on a configurable interval, when the buffer crosses ``batch_size``,
  when the buffer crosses ``max_batch_bytes``, and at process exit via ``atexit``.
- **Batches by bytes** — if ``max_batch_bytes`` is set, an in-progress batch is
  split before it crosses the limit (always ships at least one record per call).

Subclasses implement a single method::

    def _ship(self, batch: list[str]) -> ShipResult:
        ...

``_ship`` receives a list of already-formatted log lines (strings) and returns a
``ShipResult`` indicating success and record count.  It may raise; the base class
catches all exceptions, bumps ``{counter_prefix}.transport.error``, and continues.

``_BufferedShipper`` is **internal** (underscore-prefixed) and intentionally
absent from ``__all__``.  It is an implementation detail; application code never
imports it directly.
"""

from __future__ import annotations

import atexit
import logging
import threading
from collections import deque
from dataclasses import dataclass

from vibey_bootstrap.counters import bump_counter

# ---------------------------------------------------------------------------
# Public result type (subclasses return this from _ship)
# ---------------------------------------------------------------------------


@dataclass
class ShipResult:
    """Return value of :py:meth:`_BufferedShipper._ship`.

    Attributes
    ----------
    ok:
        ``True`` when the batch was accepted by the remote sink.
    count:
        Number of records successfully shipped (may be less than the batch size
        if the sink accepted a partial write — most sinks treat the batch as
        atomic, in which case ``count`` equals ``len(batch)`` on success and
        ``0`` on failure).
    """

    ok: bool
    count: int


# ---------------------------------------------------------------------------
# Base handler
# ---------------------------------------------------------------------------


class _BufferedShipper(logging.Handler):
    """Internal base — buffer + flush-thread + batching + atexit + counters.

    Parameters
    ----------
    counter_prefix:
        The dot-separated prefix for ``bump_counter`` keys, e.g. ``"panther"``.
        The base class bumps ``{prefix}.transport.{dropped,error,ok,records}``;
        subclasses may bump additional keys (e.g. ``throttled``, ``posts``).
    batch_size:
        Flush when the buffer contains this many records.  The background thread
        also flushes on ``flush_interval`` regardless.
    max_batch_bytes:
        If set (> 0), a single ``_ship`` call never exceeds this many encoded
        bytes.  The batch is split and ``_ship`` is called multiple times per
        drain cycle.  ``None`` disables byte-aware splitting.
    flush_interval:
        Seconds between background flushes.  The thread also wakes immediately
        when ``batch_size`` is reached.
    max_buffer:
        Maximum number of records held in memory.  When the buffer is full,
        the oldest record is silently evicted (``deque(maxlen=…)`` semantics)
        and the dropped counter is incremented.
    """

    # Subclasses may override the thread name for easier debugging.
    _THREAD_NAME: str = "buffered-shipper"

    def __init__(
        self,
        *,
        counter_prefix: str,
        batch_size: int = 100,
        max_batch_bytes: int | None = None,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
    ) -> None:
        super().__init__()

        self._counter_prefix = counter_prefix
        self._batch_size = max(1, batch_size)
        self._max_batch_bytes: int | None = (
            max(1, max_batch_bytes) if max_batch_bytes and max_batch_bytes > 0 else None
        )
        self._flush_interval = max(0.1, flush_interval)

        max_buffer = max(1, max_buffer)
        self._buffer: deque[str] = deque(maxlen=max_buffer)
        self._lock = threading.Lock()

        self._flush_now = threading.Event()
        self._stop_event = threading.Event()
        self._closed = False
        self._close_lock = threading.Lock()

        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            name=self._THREAD_NAME,
            daemon=True,
        )
        self._flush_thread.start()

        self._atexit_ref = self.close
        atexit.register(self._atexit_ref)

    # ------------------------------------------------------------------
    # logging.Handler API
    # ------------------------------------------------------------------

    def emit(self, record: logging.LogRecord) -> None:
        """Format *record* and append it to the in-memory buffer.

        Never raises.  If the buffer is full the oldest record is evicted by
        the underlying ``deque``; the drop is counted.  If the buffer reaches
        ``batch_size`` after the append, the background thread is signalled to
        flush immediately.
        """
        try:
            line = self.format(record)
            maxlen = self._buffer.maxlen or 0
            with self._lock:
                was_full = maxlen > 0 and len(self._buffer) >= maxlen
                self._buffer.append(line)
                current_size = len(self._buffer)
            if was_full:
                bump_counter(f"{self._counter_prefix}.transport.dropped")
            if current_size >= self._batch_size:
                self._flush_now.set()
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        """Synchronously drain and ship everything currently in the buffer.

        Blocking — intended for explicit flush calls (e.g. test helpers or the
        ``close()`` path).  Safe to call from any thread.  Never raises.
        """
        try:
            self._drain_and_ship()
        except Exception:
            pass

    def close(self) -> None:
        """Stop the background thread, drain remaining records, and clean up.

        Idempotent — safe to call multiple times (e.g. both explicitly and via
        ``atexit``).  Blocks until the flush thread exits or a timeout elapses.
        """
        with self._close_lock:
            if self._closed:
                return
            self._closed = True

        try:
            self._stop_event.set()
            self._flush_now.set()
            if (
                self._flush_thread.is_alive()
                and self._flush_thread is not threading.current_thread()
            ):
                join_timeout = max(self._flush_interval, 2.0) + 1.0
                self._flush_thread.join(timeout=join_timeout)
            # Final synchronous drain — anything the thread didn't pick up.
            self._drain_and_ship()
        except Exception:
            pass
        finally:
            try:
                self._on_close()
            except Exception:
                pass
            try:
                atexit.unregister(self._atexit_ref)
            except Exception:
                pass
            super().close()

    def _on_close(self) -> None:
        """Hook for subclasses to release resources (HTTP sessions, DB engines, …)."""

    # ------------------------------------------------------------------
    # Background flush loop
    # ------------------------------------------------------------------

    def _flush_loop(self) -> None:
        """Daemon thread body — flush on interval or when signalled."""
        while not self._stop_event.is_set():
            self._flush_now.wait(timeout=self._flush_interval)
            self._flush_now.clear()
            try:
                self._drain_and_ship()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Drain + batch-split logic
    # ------------------------------------------------------------------

    def _drain_and_ship(self) -> None:
        """Pull records from the buffer and call ``_ship`` in batches.

        Respects both ``batch_size`` and ``max_batch_bytes`` (if set).  Loops
        until the buffer is empty so a single ``flush()`` call empties it even
        when it holds more than one batch worth of data.
        """
        while True:
            batch = self._take_batch()
            if not batch:
                return
            try:
                result = self._ship(batch)
            except Exception:
                bump_counter(f"{self._counter_prefix}.transport.error")
                return
            if result.ok:
                bump_counter(f"{self._counter_prefix}.transport.ok")
                bump_counter(f"{self._counter_prefix}.transport.records", result.count)
            else:
                bump_counter(f"{self._counter_prefix}.transport.error")

    def _take_batch(self) -> list[str]:
        """Remove up to ``batch_size`` records (and optionally ``max_batch_bytes``
        bytes) from the front of the buffer and return them as a list.

        Returns an empty list when the buffer is empty.  Thread-safe.
        """
        with self._lock:
            if not self._buffer:
                return []
            batch: list[str] = []
            nbytes = 0
            while self._buffer and len(batch) < self._batch_size:
                line = self._buffer[0]
                if self._max_batch_bytes is not None:
                    # +1 for the newline that joins lines on the wire.
                    line_bytes = len(line.encode("utf-8")) + 1
                    if batch and nbytes + line_bytes > self._max_batch_bytes:
                        # Adding this record would exceed the byte cap; stop
                        # here and leave it for the next batch.
                        break
                    nbytes += line_bytes
                self._buffer.popleft()
                batch.append(line)
            return batch

    # ------------------------------------------------------------------
    # Abstract interface for subclasses
    # ------------------------------------------------------------------

    def _ship(self, batch: list[str]) -> ShipResult:
        """Ship *batch* to the remote sink.

        Subclasses **must** override this method.  The base class calls it from
        the background thread (and from ``flush()``/``close()``).  Callers catch
        all exceptions, so subclasses may raise on unrecoverable errors — doing
        so causes the batch to be dropped and
        ``{counter_prefix}.transport.error`` to be incremented.

        Parameters
        ----------
        batch:
            A non-empty list of already-formatted log lines.  Do not modify it
            in place.

        Returns
        -------
        ShipResult
            ``ok=True, count=len(batch)`` on success; ``ok=False, count=0`` on
            failure.  Partial writes (if the sink supports them) may return
            ``ok=True, count=<partial>``.
        """
        raise NotImplementedError(  # pragma: no cover
            f"{type(self).__name__} must implement _ship(batch)"
        )


# _BufferedShipper and ShipResult are intentionally excluded from __all__.
# They are implementation details consumed only by sibling transport modules.
__all__: list[str] = []
