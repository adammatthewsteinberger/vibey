# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable automation state carried in exactly one GitHub comment.

Both pull-request and issue automation need the same three awkward things: a JSON payload
hidden in an HTML comment so a human reads prose instead of a blob, a way to find the one
comment holding it among ordinary conversation, and an update path that survives the three
shapes GitHub hands back a comment identity in. That last part is why this is shared code
rather than a copy in each module — the REST/GraphQL fallback below was written once in
response to a real 404 and is not worth getting subtly different twice.

Pull requests and issues are the same object to this API: `gh pr comment` and
`gh issue comment` create, and `repos/{repo}/issues/comments/{id}` edits either one.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Sequence
from typing import Any, cast


def gh_json(*args: str) -> Any:
    run = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"gh {' '.join(args)}: {run.stderr.strip()}")
    return json.loads(run.stdout or "null")


def marker_pattern(marker: str) -> re.Pattern[str]:
    """The regex that finds one automation's state payload and nothing else's."""
    return re.compile(r"<!-- " + re.escape(marker) + r":(\{.*?\}) -->", re.DOTALL)


def parse_payload(
    comments: Sequence[dict[str, Any] | str], pattern: re.Pattern[str]
) -> dict[str, Any] | None:
    """The newest valid payload, ignoring ordinary or malformed comments."""
    for item in reversed(comments):
        body = item if isinstance(item, str) else str(item.get("body", ""))
        match = pattern.search(body)
        if not match:
            continue
        try:
            # The pattern captures a brace-delimited group, so successful JSON here is
            # always an object; a malformed one belongs to some other comment entirely.
            return cast(dict[str, Any], json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return None


def render_body(marker: str, payload: dict[str, Any], heading: str, summary: str) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"<!-- {marker}:{encoded} -->\n## {heading}\n\n{summary.strip()}\n"


def repository() -> str:
    """The `owner/name` every `gh` call is given explicitly rather than inferring."""
    name = os.environ.get("GH_REPO")
    if not name:
        name = str(gh_json("repo", "view", "--json", "nameWithOwner")["nameWithOwner"])
    return name


def upsert_comment(
    number: int,
    body: str,
    comments: Sequence[dict[str, Any]],
    pattern: re.Pattern[str],
    *,
    subject: str = "pr",
    error: str = "could not persist automation state",
) -> None:
    """Create the state comment, or edit the existing one in place."""
    repository_name = repository()
    existing: dict[str, Any] | None = None
    for comment in reversed(comments):
        if pattern.search(str(comment.get("body", ""))):
            existing = comment
            break
    if existing is None:
        run = subprocess.run(
            ["gh", subject, "comment", str(number), "--repo", repository_name, "--body", body],
            capture_output=True,
            text=True,
            check=False,
        )
    elif existing.get("databaseId") is not None:
        comment_id = existing["databaseId"]
        run = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repository_name}/issues/comments/{comment_id}",
                "--method",
                "PATCH",
                "--field",
                f"body={body}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        # GraphQL comments sometimes expose only an opaque `IC_...` node ID. Passing
        # that value to the REST issues/comments endpoint produces a misleading 404.
        comment_id = existing.get("id")
        if not comment_id:
            raise RuntimeError(f"{error}: comment has no ID")
        mutation = (
            "mutation($id:ID!,$body:String!){updateIssueComment(input:{id:$id,body:$body})"
            "{issueComment{id}}}"
        )
        run = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "--field",
                f"query={mutation}",
                "--field",
                f"id={comment_id}",
                "--field",
                f"body={body}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if run.returncode:
        raise RuntimeError(f"{error}: {run.stderr.strip()}")
