# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Reporting which releases a publish supersedes.

This module used to claim it could yank them. It could not: PyPI exposes no API for
yanking, and every test here mocked the wire, so 100% coverage said nothing about whether
the request was even a real one. `test_the_index_still_has_no_yank_api` is the test that
would have caught it, and it talks to the network on purpose.
"""

from __future__ import annotations

import json
import os
import urllib.error
from pathlib import Path

import pytest

from vibey_gh import yank
from vibey_gh.config import GhConfig, YankConfig, load_config


def _cfg(**kw) -> GhConfig:
    return GhConfig(root=Path("."), yank=YankConfig(**kw))


def test_it_is_off_on_both_indexes_by_default():
    default = YankConfig()
    assert default.pypi is False
    assert default.testpypi is False


@pytest.mark.parametrize("index", [yank.PYPI, yank.TESTPYPI])
def test_disabled_reports_nothing(index):
    report = yank.report_superseded(_cfg(), index, "pkg", "1.2.0")
    assert report.superseded == ()
    assert report.skipped == ("disabled",)


def test_the_version_just_published_is_never_listed():
    """It must never appear in a list of things to yank, however ordering behaves."""
    assert "1.2.0" not in yank.supersede(["1.0.0", "1.1.0", "1.2.0"], "1.2.0", keep=0)


def test_keep_preserves_a_rollback_target():
    versions = ["1.0.0", "1.1.0", "1.2.0", "1.3.0"]
    assert yank.supersede(versions, "1.3.0", keep=0) == ["1.2.0", "1.1.0", "1.0.0"]
    assert yank.supersede(versions, "1.3.0", keep=1) == ["1.1.0", "1.0.0"]
    assert yank.supersede(versions, "1.3.0", keep=99) == []


def test_newer_releases_are_never_listed():
    """A version above the published one is not superseded by it."""
    assert yank.supersede(["1.0.0", "2.0.0", "3.0.0"], "2.0.0", keep=0) == ["1.0.0"]


def test_a_dev_build_is_superseded_by_its_own_release():
    assert yank.order("1.2.0.dev5") < yank.order("1.2.0")
    versions = ["1.2.0.dev4", "1.2.0.dev5", "1.2.0"]
    assert yank.supersede(versions, "1.2.0", keep=0) == ["1.2.0.dev5", "1.2.0.dev4"]


@pytest.mark.parametrize(
    "version",
    [
        "1.0",
        "1.0.0.0",
        "1!1.0.0",
        "1.0.0+local",
        "1.0.0rc1",
        "not-a-version",
        "",
        "1.2.0.devX",
        "1.2.0.dev",
    ],
)
def test_an_unparseable_version_is_left_out(version):
    """Half a PEP 440 parser mis-orders these silently, which here means naming a good
    release in a list of things to yank."""
    assert yank.order(version) is None
    assert yank.supersede([version], "9.9.9", keep=0) == []


def test_an_unparseable_current_version_reports_nothing():
    assert yank.supersede(["1.0.0", "2.0.0"], "not-a-version", keep=0) == []


def _index(monkeypatch, payload: dict) -> None:
    class _Response:
        def __init__(self) -> None:
            self._body = json.dumps(payload).encode()

        def read(self) -> bytes:
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr(yank.urllib.request, "urlopen", lambda *a, **k: _Response())


def test_releases_already_fully_yanked_are_not_listed_again(monkeypatch):
    _index(
        monkeypatch,
        {
            "releases": {
                "1.0.0": [{"yanked": True}],
                "1.1.0": [{"yanked": False}],
                "1.2.0": [{"yanked": False}],
                "1.3.0": [],
            }
        },
    )
    assert sorted(yank.released_versions(yank.PYPI, "pkg")) == ["1.1.0", "1.2.0"]


def test_an_unknown_project_has_no_releases(monkeypatch):
    def raise404(*a, **k):
        raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(yank.urllib.request, "urlopen", raise404)
    assert yank.released_versions(yank.PYPI, "nope") == []


def test_a_non_404_index_error_is_not_swallowed(monkeypatch):
    """A 404 means "no such project", a real answer. A 500 is not, and treating it as "no
    releases" would report success having looked at nothing."""

    def raise500(*a, **k):
        raise urllib.error.HTTPError("u", 500, "Server Error", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(yank.urllib.request, "urlopen", raise500)
    with pytest.raises(urllib.error.HTTPError):
        yank.released_versions(yank.PYPI, "pkg")


def test_an_unreachable_index_never_fails_the_release(monkeypatch):
    def boom(*a, **k):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(yank.urllib.request, "urlopen", boom)
    report = yank.report_superseded(_cfg(pypi=True), yank.PYPI, "pkg", "1.2.0")
    assert not report.ok
    assert report.superseded == ()


def test_nothing_superseded_is_reported_as_such(monkeypatch):
    _index(monkeypatch, {"releases": {"1.2.0": [{"yanked": False}]}})
    report = yank.report_superseded(_cfg(pypi=True), yank.PYPI, "pkg", "1.2.0")
    assert report.skipped == ("nothing superseded",)


def test_the_report_names_where_a_human_can_act_on_it(monkeypatch):
    """The list is only useful with the page that can action it, since nothing else can."""
    _index(
        monkeypatch,
        {
            "releases": {
                "1.0.0": [{"yanked": False}],
                "1.1.0": [{"yanked": False}],
                "1.2.0": [{"yanked": False}],
            }
        },
    )
    report = yank.report_superseded(_cfg(pypi=True), yank.PYPI, "pkg", "1.2.0")
    assert report.superseded == ("1.1.0", "1.0.0")
    assert report.manage_url == "https://pypi.org/manage/project/pkg/releases/"


def test_keep_must_not_be_negative():
    with pytest.raises(ValueError, match="keep"):
        YankConfig(keep=-1)


def test_the_cli_prints_the_list_and_never_fails_the_release(monkeypatch, capsys):
    from vibey_gh import cli

    monkeypatch.setattr(
        yank,
        "report_superseded",
        lambda *a, **k: yank.SupersededReport(
            "pypi", superseded=("1.0.0",), problems=("boom",), manage_url="https://example/manage"
        ),
    )
    code = cli.main(
        ["report-superseded", "--index", "pypi", "--project", "p", "--version", "1.1.0"]
    )
    out = capsys.readouterr()
    assert code == 0
    assert "1.0.0" in out.out
    assert "https://example/manage" in out.out
    assert "boom" in out.err


def test_the_cli_reports_a_skip(monkeypatch, capsys):
    from vibey_gh import cli

    monkeypatch.setattr(
        yank,
        "report_superseded",
        lambda *a, **k: yank.SupersededReport("pypi", skipped=("disabled",)),
    )
    assert (
        cli.main(["report-superseded", "--index", "pypi", "--project", "p", "--version", "1.1.0"])
        == 0
    )
    assert "disabled" in capsys.readouterr().out


@pytest.mark.skipif(
    os.environ.get("VIBEY_GH_NETWORK_TESTS") != "1",
    reason="talks to PyPI; set VIBEY_GH_NETWORK_TESTS=1",
)
@pytest.mark.parametrize(
    "url", ["https://test.pypi.org/legacy/", "https://upload.pypi.org/legacy/"]
)
def test_the_index_still_has_no_yank_api(url):
    """The test that was missing, and the reason a shipped feature could not work.

    An earlier version POSTed `:action=yank` here and every test mocked the wire, so the
    suite was green against a request the endpoint has never accepted. The distinction is
    the whole point: a RECOGNISED action reaches authentication and answers 403 on bad
    credentials, while `yank` answers 405 -- the action does not exist, and no token helps.

    If this ever starts failing, PyPI has shipped
    https://github.com/pypi/warehouse/issues/12708 and yanking can be automated for real.
    """
    import subprocess

    def status(action: str) -> str:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "-X",
                "POST",
                "-F",
                f":action={action}",
                "-F",
                "name=vibey-gh",
                "-F",
                "version=0.0.0.dev0",
                "--user",
                "__token__:bogus",
                url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()

    assert status("file_upload") == "403", "a recognised action should reach authentication"
    assert status("yank") == "405", "if this is no longer 405, PyPI may have shipped a yank API"


def test_governance_paths_match_the_founding_documents_by_default():
    patterns = YankConfig().governance_paths
    for path in (
        "docs/constitution.md",
        "docs/commandments.md",
        "docs/bill-of-rights.md",
        "docs/sd-01-counterparties-trust-verification.md",
    ):
        assert yank.governance_changed(patterns, [path]), path
    assert not yank.governance_changed(patterns, ["docs/architecture.md", "README.md"])
    assert not yank.governance_changed(patterns, [])


def test_a_ratified_governance_change_supersedes_everything(monkeypatch):
    """Article V.4: retention window and per-index switches are both overridden.

    The config below disables reporting on both indexes and keeps two rollback
    targets — and none of that survives a ratified change to the constitution: the
    rule is law, the config is machinery, and no artifact circulates under
    superseded law."""
    _index(
        monkeypatch,
        {
            "releases": {
                "1.0.0": [{}],
                "1.1.0": [{}],
                "1.2.0": [{}],
                "1.3.0": [{}],
            }
        },
    )
    cfg = _cfg(pypi=False, testpypi=False, keep=2)
    report = yank.report_superseded(
        cfg, yank.PYPI, "pkg", "1.3.0", changed_files=["docs/constitution.md"]
    )
    assert report.governance is True
    assert report.superseded == ("1.2.0", "1.1.0", "1.0.0")


def test_an_ordinary_release_never_claims_governance(monkeypatch):
    _index(monkeypatch, {"releases": {"1.0.0": [{}], "1.1.0": [{}]}})
    cfg = _cfg(pypi=True, keep=0)
    report = yank.report_superseded(
        cfg, yank.PYPI, "pkg", "1.1.0", changed_files=["vibey_gh/cli.py", "README.md"]
    )
    assert report.governance is False
    assert report.superseded == ("1.0.0",)


def test_governance_paths_load_from_toml(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[yank]\ngovernance_paths = ["LAW.md"]\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.yank.governance_paths == ("LAW.md",)
    assert yank.governance_changed(cfg.yank.governance_paths, ["LAW.md"])
    assert not yank.governance_changed(cfg.yank.governance_paths, ["docs/constitution.md"])
