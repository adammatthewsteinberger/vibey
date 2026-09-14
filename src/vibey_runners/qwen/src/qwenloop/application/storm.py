# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Storm-mode plan text: one repo's open backlog turned into one qwenloop plan.

Ports the plan built by the `qwenstorm.sh` bash prototype: clear every open issue and PR
first, then write an academic paper, then build a comprehensive book, each gated on the
repo not already having one.
"""

from qwenloop.domain.model import RepoItem


def _indent_body(body: str) -> str:
    return body.replace("\n", "\n  ")


def _render_items(items: list[RepoItem] | None, unavailable_message: str) -> str:
    """Format an issue/PR list for the plan.

    None (the fetch failed, or issues/PRs are disabled) renders as `unavailable_message`.
    An empty list (the fetch succeeded; there is simply nothing open) renders as nothing,
    the same way the bash script's `gh ... --jq` pipeline produced no output for zero
    results without ever reaching its `|| echo` fallback.

    The return value always either is empty or ends with its own trailing newline, exactly
    like the bash script's per-item jq output and its `echo` fallback both did — so the
    caller can join sections with a single separating "\n" and get one blank line between
    them regardless of which case applies.
    """
    if items is None:
        return f"{unavailable_message}\n"
    if not items:
        return ""
    return "\n".join(
        f"- #{item.number} {item.title}\n\n  {_indent_body(item.body)}\n" for item in items
    )


def build_plan(
    *,
    repo: str,
    issues: list[RepoItem] | None,
    pull_requests: list[RepoItem] | None,
    author: str,
) -> str:
    """Build the qwenloop plan text for one repo's storm-mode run."""
    issues_block = _render_items(issues, "(none, or issues disabled)")
    prs_block = _render_items(pull_requests, "(none)")
    return (
        f"# qwenstorm plan for {repo}\n\n"
        "## 1. Clear the backlog\n"
        "Work every open issue and PR below to a merged/closed state, smallest first.\n"
        "Open a PR for each change; never force-push over another author's commits;\n"
        "never push directly to the default branch.\n\n"
        "### Open issues\n"
        f"{issues_block}"
        "\n### Open PRs\n"
        f"{prs_block}"
        "\n## 2. Academic paper\n"
        "If docs/paper.md is missing, write one grounded only in what this repo actually\n"
        "does: abstract, introduction, related work, architecture/method, evaluation,\n"
        "conclusion, and a References section — no invented benchmarks or citations.\n"
        "Then run:\n"
        "    pip install --quiet vibey-gh\n"
        f'    vibey-gh paper --author "{author}" --journal\n\n'
        "## 3. Comprehensive book\n"
        "If docs/ lacks a full chapter set (overview, architecture, usage, configuration,\n"
        "operations, contributing) and a properdocs.yml (mkdocs-shaped) nav ordering them,\n"
        "write the missing chapters from this repo's actual source and README — no\n"
        "placeholder content. Then run:\n"
        "    pip install --quiet mkdocs\n"
        "    mkdocs build -f properdocs.yml -d site\n"
        f'    vibey-gh book --site-dir site --title "{repo}" --author "{author}"\n'
    )
