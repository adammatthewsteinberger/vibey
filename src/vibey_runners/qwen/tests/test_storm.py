# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from qwenloop.application.storm import build_plan
from qwenloop.domain.model import RepoItem


def test_build_plan_reports_unavailable_backlog_sections() -> None:
    plan = build_plan(repo="widgets", issues=None, pull_requests=None, author="A Author")
    assert "# qwenstorm plan for widgets" in plan
    assert "### Open issues\n(none, or issues disabled)\n" in plan
    assert "### Open PRs\n(none)\n" in plan
    assert 'vibey-gh paper --author "A Author" --journal' in plan
    assert 'vibey-gh book --site-dir site --title "widgets" --author "A Author"' in plan


def test_build_plan_renders_empty_backlog_as_blank() -> None:
    plan = build_plan(repo="widgets", issues=[], pull_requests=[], author="A Author")
    assert "### Open issues\n\n### Open PRs\n" in plan


def test_build_plan_renders_items_with_indented_multiline_bodies() -> None:
    issues = [RepoItem(number=1, title="fix it", body="line one\nline two")]
    pull_requests = [RepoItem(number=7, title="a pr", body="")]
    plan = build_plan(repo="widgets", issues=issues, pull_requests=pull_requests, author="Author")
    assert "- #1 fix it\n\n  line one\n  line two\n" in plan
    assert "- #7 a pr\n\n  \n" in plan
