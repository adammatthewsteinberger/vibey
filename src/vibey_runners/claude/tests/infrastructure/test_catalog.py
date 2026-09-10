# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Regression tests for the two real bugs live testing against a real Claude
account found in infrastructure/agent/catalog.py: last_modified is
milliseconds, not seconds (a raw int caused `ValueError: year 58576 is out of
range`), and some real sessions have a blank cwd (which used to raise
InvalidSessionSelectorError and crash the whole `claudeloop sessions` listing)."""

from __future__ import annotations

from dataclasses import dataclass

from claudeloop.infrastructure.agent.catalog import _to_session_ref


@dataclass
class _FakeSDKSessionInfo:
    session_id: str
    cwd: str | None = None
    last_modified: int | None = None
    git_branch: str | None = None
    first_prompt: str | None = None


def test_last_modified_is_treated_as_milliseconds_not_seconds() -> None:
    # A real value observed from claude_agent_sdk.list_sessions() during live
    # testing: a 13-digit int. Treating it as seconds raised
    # `ValueError: year 58576 is out of range`.
    info = _FakeSDKSessionInfo(session_id="abc", cwd="/repo", last_modified=1786328953799)
    ref = _to_session_ref(info, cwd="/repo")  # type: ignore[arg-type]
    assert ref.last_modified is not None
    assert 2020 <= ref.last_modified.year <= 2030


def test_last_modified_none_is_preserved_as_none() -> None:
    info = _FakeSDKSessionInfo(session_id="abc", cwd="/repo", last_modified=None)
    ref = _to_session_ref(info, cwd="/repo")  # type: ignore[arg-type]
    assert ref.last_modified is None


def test_blank_cwd_falls_back_to_a_visible_sentinel_instead_of_raising() -> None:
    # A real observed case: list_sessions() with no directory filter returns
    # some entries whose own `cwd` is empty, and the caller-supplied cwd
    # fallback can also be empty for a global listing. domain.SessionRef
    # requires a non-blank cwd, so this used to raise
    # InvalidSessionSelectorError and crash `claudeloop sessions` entirely.
    info = _FakeSDKSessionInfo(session_id="abc", cwd=None)
    ref = _to_session_ref(info, cwd="")  # type: ignore[arg-type]
    assert ref.cwd == "(unknown)"


def test_caller_supplied_cwd_used_when_info_has_none() -> None:
    info = _FakeSDKSessionInfo(session_id="abc", cwd=None)
    ref = _to_session_ref(info, cwd="/fallback")  # type: ignore[arg-type]
    assert ref.cwd == "/fallback"


def test_info_cwd_takes_precedence_over_caller_supplied_cwd() -> None:
    info = _FakeSDKSessionInfo(session_id="abc", cwd="/from-info")
    ref = _to_session_ref(info, cwd="/fallback")  # type: ignore[arg-type]
    assert ref.cwd == "/from-info"


def test_first_prompt_preview_truncated_and_none_when_blank() -> None:
    long_prompt = "x" * 500
    info = _FakeSDKSessionInfo(session_id="abc", cwd="/repo", first_prompt=long_prompt)
    ref = _to_session_ref(info, cwd="/repo")  # type: ignore[arg-type]
    assert ref.first_prompt_preview is not None
    assert len(ref.first_prompt_preview) == 200

    info_blank = _FakeSDKSessionInfo(session_id="abc", cwd="/repo", first_prompt="")
    ref_blank = _to_session_ref(info_blank, cwd="/repo")  # type: ignore[arg-type]
    assert ref_blank.first_prompt_preview is None


def test_git_branch_passthrough() -> None:
    info = _FakeSDKSessionInfo(session_id="abc", cwd="/repo", git_branch="main")
    ref = _to_session_ref(info, cwd="/repo")  # type: ignore[arg-type]
    assert ref.git_branch == "main"


def test_most_recent_returns_none_when_no_sessions() -> None:
    from unittest.mock import patch

    from claudeloop.infrastructure.agent.catalog import SdkSessionCatalog

    with patch("claudeloop.infrastructure.agent.catalog.list_sessions", return_value=[]):
        catalog = SdkSessionCatalog()
        result = catalog.most_recent("/repo")
        assert result is None


def test_most_recent_returns_first_session() -> None:
    from unittest.mock import patch

    from claudeloop.infrastructure.agent.catalog import SdkSessionCatalog

    fake_session = _FakeSDKSessionInfo(
        session_id="sess-1", cwd="/repo", last_modified=1786328953799
    )
    with patch(
        "claudeloop.infrastructure.agent.catalog.list_sessions", return_value=[fake_session]
    ):
        catalog = SdkSessionCatalog()
        result = catalog.most_recent("/repo")
        assert result is not None
        assert result.session_id == "sess-1"


def test_list_all_returns_all_sessions() -> None:
    from unittest.mock import patch

    from claudeloop.infrastructure.agent.catalog import SdkSessionCatalog

    sessions = [
        _FakeSDKSessionInfo(session_id="sess-1", cwd="/repo"),
        _FakeSDKSessionInfo(session_id="sess-2", cwd="/repo"),
    ]
    with patch("claudeloop.infrastructure.agent.catalog.list_sessions", return_value=sessions):
        catalog = SdkSessionCatalog()
        result = catalog.list_all("/repo")
        assert len(result) == 2
        assert result[0].session_id == "sess-1"
        assert result[1].session_id == "sess-2"


def test_list_all_without_cwd_uses_session_cwd() -> None:
    from unittest.mock import patch

    from claudeloop.infrastructure.agent.catalog import SdkSessionCatalog

    sessions = [
        _FakeSDKSessionInfo(session_id="sess-1", cwd="/repo1"),
        _FakeSDKSessionInfo(session_id="sess-2", cwd="/repo2"),
    ]
    with patch("claudeloop.infrastructure.agent.catalog.list_sessions", return_value=sessions):
        catalog = SdkSessionCatalog()
        result = catalog.list_all(cwd=None)
        assert len(result) == 2
        assert result[0].cwd == "/repo1"
        assert result[1].cwd == "/repo2"
