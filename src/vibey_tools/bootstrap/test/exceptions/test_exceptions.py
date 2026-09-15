"""Tests for ``vibey_bootstrap.exceptions``."""

from __future__ import annotations

import vibey_bootstrap.exceptions as exc_mod
from vibey_bootstrap.exceptions import (
    InvalidMessageError,
    NetworkError,
    OversizedAttachmentError,
    RateLimitError,
    TransientError,
    UnrecoverableError,
    ZipBombError,
    is_unrecoverable,
    register_unrecoverable,
)


def test_classifier_marks_unrecoverable() -> None:
    assert is_unrecoverable(InvalidMessageError("x"))
    assert is_unrecoverable(OversizedAttachmentError("x"))
    assert is_unrecoverable(ZipBombError("x"))


def test_classifier_marks_transient_as_recoverable() -> None:
    assert not is_unrecoverable(NetworkError("x"))
    assert not is_unrecoverable(RateLimitError("x"))


def test_classifier_marks_arbitrary_exception_as_recoverable() -> None:
    assert not is_unrecoverable(ValueError("x"))
    assert not is_unrecoverable(RuntimeError("x"))


def test_zip_bomb_inherits_oversized() -> None:
    assert issubclass(ZipBombError, OversizedAttachmentError)
    assert issubclass(ZipBombError, UnrecoverableError)


def test_transient_not_in_unrecoverable_tree() -> None:
    assert not issubclass(TransientError, UnrecoverableError)
    assert not issubclass(NetworkError, UnrecoverableError)


def test_register_unrecoverable_extends_tuple() -> None:
    class MyCustomBreakage(Exception):
        pass

    original = exc_mod.DEFAULT_UNRECOVERABLE_TYPES
    try:
        register_unrecoverable(MyCustomBreakage)
        assert is_unrecoverable(MyCustomBreakage("x"))
        assert MyCustomBreakage in exc_mod.DEFAULT_UNRECOVERABLE_TYPES
    finally:
        exc_mod.DEFAULT_UNRECOVERABLE_TYPES = original


def test_register_unrecoverable_idempotent() -> None:
    """Re-registering the same type shouldn't duplicate it in the tuple."""

    class MyType(Exception):
        pass

    original = exc_mod.DEFAULT_UNRECOVERABLE_TYPES
    try:
        register_unrecoverable(MyType)
        register_unrecoverable(MyType)
        count = sum(1 for t in exc_mod.DEFAULT_UNRECOVERABLE_TYPES if t is MyType)
        assert count == 1
    finally:
        exc_mod.DEFAULT_UNRECOVERABLE_TYPES = original
