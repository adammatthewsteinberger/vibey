# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""`vibey-gh` — the command the hooks and the CI workflows call."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from vibey_gh import (
    conversation,
    debugging,
    documentation,
    fingerprints,
    github_release,
    install,
    issue_automation,
    merge_train,
    pr_automation,
    promote,
    realign,
    reconcile,
    rulesets,
    surfaces,
    versioning,
)
from vibey_gh.config import load_config
from vibey_gh.interfaces.marketplace_renderer_interface import MarketplaceRendererInterface


def _check(args) -> int:
    cfg = load_config()
    ok, problems = install.installed(cfg, local=not args.ci)
    report = fingerprints.check(cfg, rev_range=args.commits, apply=args.apply)
    docs = documentation.check(cfg)
    scan = pr_automation.check_scan_workflows(cfg)
    # The root marketplace is a rendered file like the workflows: when the repository
    # declares members, the manifest on disk must be what they render to.
    marketplace_ok, marketplace_problem = True, ""
    if cfg.marketplace.members:
        from vibey_gh.marketplace import MarketplaceRenderer

        marketplace_ok, marketplace_problem = MarketplaceRenderer().check(cfg)
    clean = ok and report.ok and docs.ok and scan.ok and marketplace_ok

    if args.quiet:
        return 0 if clean else 1

    for problem in problems:
        print(f"  hooks: {problem}", file=sys.stderr)
    for path in report.missing_header:
        print(f"  {path.relative_to(cfg.root)}: missing the fingerprint header", file=sys.stderr)
    for path in report.superseded_header:
        print(
            f"  {path.relative_to(cfg.root)}: carries a superseded fingerprint header "
            "(`check --apply` replaces it with the current one)",
            file=sys.stderr,
        )
    for path in report.duplicate_header:
        print(
            f"  {path.relative_to(cfg.root)}: fingerprint header appears more than once",
            file=sys.stderr,
        )
    for commit in report.missing_trailer:
        print(f"  commit {commit}: missing the `{cfg.trailer_key}:` trailer", file=sys.stderr)
    for commit in report.invalid_subject:
        print(f"  commit {commit}: subject is not a Conventional Commit", file=sys.stderr)
    for problem in report.branch_logging:
        print(f"  debug logging: {problem}", file=sys.stderr)
    for problem in docs.problems:
        print(f"  documentation: {problem}", file=sys.stderr)
    for problem in scan.problems:
        print(f"  {problem}", file=sys.stderr)
    if not marketplace_ok:
        print(f"  marketplace: {marketplace_problem}", file=sys.stderr)

    if clean:
        scope = f"{report.checked_files} source file(s)"
        if args.commits:
            scope += f" and every commit in {args.commits}"
        print(f"vibey-gh: ok — hooks installed; {scope} carry the fingerprint")
        return 0

    print("\nvibey-gh: FAILED", file=sys.stderr)
    print(f"\n  header:  {cfg.header}", file=sys.stderr)
    print(f"  trailer: {cfg.trailer}", file=sys.stderr)
    print(
        "\n  `vibey-gh check --apply` adds missing headers; `vibey-gh install` installs the hooks.",
        file=sys.stderr,
    )
    return 1


def _install(args) -> int:
    cfg = load_config()
    for action in install.install(cfg):
        print(f"  {action.hook}: {action.outcome}")
    for notice in install.installation_notices():
        print(f"  notice: {notice}")
    print(f"vibey-gh: installed into {cfg.root}")
    return 0


def _conventional_message(args) -> int:
    if args.file:
        message = args.file.read_text(encoding="utf-8")
        args.file.write_text(fingerprints.normalize_commit_message(message), encoding="utf-8")
    else:
        print(fingerprints.normalize_commit_message(sys.stdin.read()), end="")
    return 0


def _conventional_check(args) -> int:
    invalid = fingerprints.commits_with_invalid_subject(args.commits, load_config())
    for commit in invalid:
        print(commit)
    return 1 if invalid else 0


def _version(args) -> int:
    cfg = load_config(config=args.config)
    if args.dev is not None:
        dev = versioning.dev_version(cfg, args.dev)
        if args.apply:
            versioning.apply_version(cfg, dev)
        print(dev)
        return 0
    new, why = versioning.decide(cfg, args.since)
    if args.explain or not new:
        print(f"vibey-gh: {why}", file=sys.stderr)
    if not new:
        print("none")
        return 0
    if args.apply:
        versioning.apply_version(cfg, new)
    print(new)
    return 0


def _summary_rows(rows: list[tuple[int, str, str]], merged: int, skipped: int) -> str:
    """A markdown table for the job summary. A run that merged nothing still has to say
    what it looked at, or the only way to find out is to read the log."""
    lines = ["| PR | Title | Outcome |", "|---|---|---|"]
    lines += [f"| #{n} | {t} | {outcome} |" for n, t, outcome in rows]
    lines += ["", f"Merged {merged}, skipped {skipped}."]
    return "\n".join(lines) + "\n"


def _merge_train(args) -> int:
    cfg = load_config()
    prs = (
        merge_train.open_pull_requests(cfg, number=args.pr)
        if args.pr is not None
        else merge_train.open_pull_requests(cfg)
    )
    if not prs:
        print(f"vibey-gh: no open pull requests into {cfg.integration_branch}")
        _write_summary(args, "No open pull requests.\n")
        return 0

    merged = skipped = 0
    rows: list[tuple[int, str, str]] = []
    for pr in prs:
        v = merge_train.judge(pr, cfg)

        if not v.ready:
            # Only a pull request held on the owner's approval gets labelled and
            # announced. A draft or a red build is the contributor's to fix and needs no
            # notification; this one is waiting on somebody who does not know yet.
            if v.held_for_review and not args.dry_run and args.label != "":
                merge_train.hold_for_review(v, cfg, label=args.label)
            print(f"  #{v.number} skipped — {v.reason}")
            rows.append((v.number, v.title, f"skipped — {v.reason}"))
            skipped += 1
            continue

        if args.dry_run:
            print(f"  #{v.number} would merge ({args.method})")
            rows.append((v.number, v.title, f"would {args.method}-merge"))
            continue

        method = merge_train.method_for(pr, cfg, args.method)
        # A squash commit takes its body from the pull request, and a bot's pull request
        # never carries the Made-With trailer — so supply a body that does, or the
        # provenance check rejects the very commit this train creates. A rebase preserves
        # the branch's own commits, which the push hooks already stamped.
        squash_body = None
        if method == "squash" and cfg.trailer not in (pr.get("body") or ""):
            existing = (pr.get("body") or "").strip()
            squash_body = (existing + "\n\n" if existing else "") + cfg.trailer
        ok, bypassed, error = merge_train.merge(v.number, method, squash_body)
        if ok:
            note = " (review requirement bypassed)" if bypassed else ""
            cleanup = ""
            if merge_train.should_delete_head(pr, cfg):
                cleanup = (
                    "; deleted merged topic branch"
                    if merge_train.delete_head_branch(pr)
                    else "; topic-branch cleanup failed"
                )
            print(f"  #{v.number} {method}-merged{note}{cleanup}")
            rows.append((v.number, v.title, f"{method}-merged{note}{cleanup}"))
            merged += 1
        else:
            # The stderr is the diagnosis: "refused it" alone once cost an hour of
            # ruleset archaeology when the real cause was a token missing the repository.
            reason = error or "the ruleset refused it"
            print(f"  #{v.number} could not be merged — {reason}")
            rows.append((v.number, v.title, f"blocked: {reason[:120]}"))
            skipped += 1

    print(f"vibey-gh: merged {merged}, skipped {skipped}")
    _write_summary(args, _summary_rows(rows, merged, skipped))
    return 0


def _read_json(value: str) -> dict:
    parsed = json.loads(_read_text(value))
    if not isinstance(parsed, dict):
        raise TypeError("input JSON must be an object")
    return parsed


def _pr_automation(args) -> int:
    cfg = load_config()
    try:
        if args.action == "evaluate":
            print(pr_automation.evaluate_pr(args.pr, args.head_sha, cfg).to_json())
        elif args.action == "ready-draft":
            result = pr_automation.ready_draft(args.pr, args.head_sha, cfg)
            print(json.dumps(result, sort_keys=True))
        elif args.action in {"record-review", "record-repair"}:
            kind = args.action.removeprefix("record-")
            state = pr_automation.record(args.pr, _read_json(args.input), kind)
            print(json.dumps(asdict(state), sort_keys=True))
        elif args.action == "mirror-fork":
            print(json.dumps(pr_automation.mirror_fork(args.pr, cfg), sort_keys=True))
        elif args.action == "self-heal":
            numbers = [args.pr] if args.pr else pr_automation.exhausted_pull_requests(cfg)
            results = [pr_automation.self_heal(number, cfg) for number in numbers]
            print(json.dumps(results, sort_keys=True))
        elif args.action == "ensure-labels":
            pr_automation.ensure_labels()
            print("vibey-gh: PR automation labels are ready")
        else:  # pragma: no cover - argparse constrains this
            raise ValueError(f"unknown action: {args.action}")
    except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    return 0


def _issue_automation(args) -> int:
    cfg = load_config()
    try:
        if args.action == "evaluate":
            print(issue_automation.evaluate_issue(args.issue, cfg).to_json())
        elif args.action == "context":
            document = issue_automation.context(
                issue_automation.fetch_issue(args.issue), max_bytes=args.max_bytes
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(document, encoding="utf-8")
                print(f"vibey-gh: wrote {len(document.encode())} bytes to {args.output}")
            else:
                print(document, end="")
        elif args.action == "record-solution":
            state = issue_automation.record(args.issue, _read_json(args.input))
            print(json.dumps(asdict(state), sort_keys=True))
        elif args.action == "list-eligible":
            print(
                json.dumps(
                    [json.loads(item.to_json()) for item in issue_automation.eligible_issues(cfg)],
                    sort_keys=True,
                )
            )
        elif args.action == "ensure-labels":
            issue_automation.ensure_labels()
            print("vibey-gh: issue automation labels are ready")
        else:  # pragma: no cover - argparse constrains this
            raise ValueError(f"unknown action: {args.action}")
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    return 0


def _github_release(args) -> int:
    cfg = load_config()
    try:
        result = github_release.publish(cfg, target=args.target, version=args.version)
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


def _write_summary(args, text: str) -> None:
    """Append to the job summary when running in Actions. Best-effort: a summary that
    cannot be written is not a reason to fail a train that merged correctly."""
    path = args.summary or os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        print(f"vibey-gh: could not write the summary: {exc}", file=sys.stderr)


def _promote(args) -> int:
    try:
        result = promote.promote(
            load_config(), dry_run=args.dry_run, method=args.method, wait=args.wait
        )
    except RuntimeError as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    for note in result.notes:
        print(f"  {note}")
    print(f"vibey-gh: {result.changed_files} file(s) differ; version {result.version}")
    _write_summary(args, _promotion_summary(result))
    return 0


def _promotion_summary(result) -> str:
    lines = ["## Promotion", ""]
    lines += [f"- {note}" for note in result.notes]
    lines += ["", f"Files differing: {result.changed_files}", f"Version: `{result.version}`"]
    return "\n".join(lines) + "\n"


def _realign(args) -> int:
    try:
        _changed, message = realign.realign(load_config())
    except RuntimeError as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    print(f"vibey-gh: {message}")
    return 0


def _report_superseded(args) -> int:
    import subprocess

    from vibey_gh import yank

    cfg = load_config()
    changed: list[str] | None = None
    if args.governance_since:
        # The ratifying merge is one push; its range names what it changed. An unreadable
        # range is reported loudly rather than silently waiving Article V.4 — but it never
        # fails the release: the publish already happened, and the amendment is enforced
        # by the review and the humans as well as by this bookkeeping.
        run = subprocess.run(
            ["git", "diff", "--name-only", f"{args.governance_since}...HEAD"],
            capture_output=True,
            text=True,
            cwd=cfg.root,
            check=False,
        )
        if run.returncode == 0:
            changed = [line for line in run.stdout.splitlines() if line.strip()]
        else:
            print(
                "vibey-gh: could not read the governance range "
                f"{args.governance_since!r}: {run.stderr.strip()} — Article V.4 was NOT "
                "evaluated for this release; check it by hand",
                file=sys.stderr,
            )
    report = yank.report_superseded(cfg, args.index, args.project, args.version, changed)
    if report.governance:
        print(
            "vibey-gh: RATIFIED GOVERNANCE CHANGE — Article V.4 of the Constitution: no"
            " artifact circulates under superseded law. Every previous release is named"
            " below, zero exceptions, retention window overridden."
        )
    for problem in report.problems:
        print(f"vibey-gh: {problem}", file=sys.stderr)
    if report.skipped:
        print(f"vibey-gh: {args.index} — {', '.join(report.skipped)}")
    if report.superseded:
        print(
            f"vibey-gh: {len(report.superseded)} release(s) on {args.index} superseded by {args.version}:"
        )
        for version in report.superseded:
            print(f"  - {version}")
        # PyPI has no yank API, so the only thing that can be automated is working out the
        # list. Print where to act on it; see vibey_gh/yank.py for why.
        print(f"\n  Yank at: {report.manage_url}")
    # A publish has already succeeded by the time this runs. Reporting a bookkeeping failure
    # as a failed release would misrepresent it, so problems are printed, not fatal.
    return 0


def _failover(args) -> int:
    from vibey_gh import failover

    cfg = failover.load(Path(args.config).expanduser() if args.config else None)
    state = Path(args.state).expanduser() if args.state else None
    failover.run(cfg, state_path=state, once=args.once)
    return 0


def _tidy(args) -> int:
    from vibey_gh import tidy

    cfg = load_config()
    report = tidy.survey(cfg, local=not args.ci)
    for problem in report.problems:
        print(f"vibey-gh tidy: {problem}", file=sys.stderr)
        return 1
    rows = (
        ("merged remote branches", report.remote_merged),
        ("merged local branches", report.local_merged),
        ("gone-upstream local branches", report.local_gone),
        ("prunable worktrees", report.prunable_worktrees),
        ("draft releases (human decision)", report.draft_releases),
        ("orphan tags (human decision)", report.orphan_tags),
    )
    for label, items in rows:
        if items:
            print(f"vibey-gh tidy: {label}: {', '.join(items)}")
    if report.stashes:
        print(f"vibey-gh tidy: {report.stashes} stash(es) — yours, untouched")
    if report.untracked:
        print(f"vibey-gh tidy: {report.untracked} untracked path(s) — yours, untouched")
    if report.clean:
        print("vibey-gh tidy: clean — no technical clutter (9.a)")
        return 0
    if args.apply:
        for action in tidy.apply(cfg, report):
            print(f"vibey-gh tidy: {action}")
        # Drafts and orphan tags remain: reported above, removed only by a human.
        return 0
    print(
        "vibey-gh tidy: technical clutter present (sub-doctrine 9.a) —"
        " `vibey-gh tidy --apply` removes the provably-lossless classes"
    )
    return 1


def _corpus_index(args) -> int:
    from vibey_gh import corpus

    cfg = load_config()
    if args.check:
        ok, message = corpus.check(cfg)
        print(f"vibey-gh corpus-index: {message}", file=None if ok else sys.stderr)
        return 0 if ok else 1
    target = corpus.write(cfg)
    index = corpus.build(cfg)
    print(
        f"vibey-gh corpus-index: wrote {target.name} — {len(index['chunks'])} chunk(s)"
        f" across {len(index['documents'])} document(s), corpus"
        f" {index['corpus_sha256'][:12]}…"
    )
    return 0


def _marketplace(args, renderer: MarketplaceRendererInterface | None = None) -> int:
    from vibey_gh.marketplace import MarketplaceError, MarketplaceRenderer

    cfg = load_config()
    renderer = renderer or MarketplaceRenderer()
    if args.check:
        ok, message = renderer.check(cfg)
        print(f"vibey-gh marketplace: {message}", file=None if ok else sys.stderr)
        return 0 if ok else 1
    try:
        manifest = renderer.build(cfg)
        target = renderer.write(cfg)
    except MarketplaceError as exc:
        print(f"vibey-gh marketplace: {exc}", file=sys.stderr)
        return 1
    print(
        f"vibey-gh marketplace: wrote {target.relative_to(cfg.root).as_posix()} —"
        f" {len(manifest['plugins'])} plugin(s) from {len(cfg.marketplace.members)}"
        f" member(s) as {manifest['name']!r}"
    )
    return 0


def _sovereign(args) -> int:
    """Publish or read the sovereign heartbeat (doctrine 8.a).

    `--beat` is what the operator's supervisor runs on a timer; the bare form is what
    a workflow runs to decide whether it may schedule the sovereign lane at all. The
    probe prints its verdict and, under Actions, writes `ready=` to `$GITHUB_OUTPUT`
    so a job `if:` can consume it.
    """
    import os

    from vibey_gh import sovereign

    fallback = load_config().pr_automation.fallback
    if args.beat:
        result = sovereign.beat(fallback.heartbeat_ref, remote=args.remote)
    else:
        result = sovereign.probe(
            fallback.heartbeat_ref,
            max_age_minutes=fallback.heartbeat_max_age_minutes,
            remote=args.remote,
        )
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write(f"ready={'true' if result.ready else 'false'}\n")
    print(f"vibey-gh sovereign: {result.reason}")
    # A probe that finds no runner is a fact, not a failure: exiting non-zero would
    # turn "the sovereign lane is not available right now" into a red job.
    return 0 if (result.ready or not args.beat) else 1


def _fit(args) -> int:
    from pathlib import Path

    from vibey_gh import fit
    from vibey_gh.fitloop import FitLoop, recorded_observations

    machine = fit.sample_machine()
    model = fit.sample_model(args.model)
    # With --journal the decision is recorded with everything needed to re-derive it,
    # and prior observations in that journal inform this projection — which is what
    # makes repeated invocations a control loop rather than a series of guesses.
    journal = Path(args.journal) if args.journal else None
    loop = FitLoop(args.model, journal=journal)
    if journal:
        loop._observations.extend(recorded_observations(journal))
    if args.observed_seconds is not None:
        loop.observe(
            payload_bytes=args.payload_bytes,
            elapsed_s=args.observed_seconds,
            concurrent=max(args.queue, 1),
        )
    verdict = loop.admit(
        payload_bytes=args.payload_bytes,
        deadline_s=args.deadline,
        queue_depth=args.queue,
        machine=machine,
        model=model,
    )
    print(
        f"vibey-gh fit: machine {machine.total_gb} GB total, {machine.free_gb} GB free,"
        f" swap {machine.swap_used_gb}/{machine.swap_total_gb} GB —"
        f" {machine.available_gb} GB available"
    )
    if model is None:
        print(f"vibey-gh fit: model {args.model} could not be read from the runner")
    else:
        print(
            f"vibey-gh fit: model {model.name} {model.size_gb} GB, context {model.context_length}"
        )
    print(f"vibey-gh fit: {verdict.verdict.upper()} — {verdict.reason}")
    if verdict.headroom_gb:
        print(f"vibey-gh fit: headroom wanted: {verdict.headroom_gb} GB")
    for note in verdict.notes:
        print(f"vibey-gh fit: note — {note}")
    advice = loop.recommendation()
    if advice:
        print(f"vibey-gh fit: ACTION NEEDED — {advice}")
    return 0 if verdict.ok else 1


def _doctor(args) -> int:
    from vibey_gh import doctor

    findings = doctor.diagnose(root=None)
    for f in findings:
        print(
            f"  {f.severity}: {f.message}", file=sys.stderr if f.severity == "error" else sys.stdout
        )
    errors = sum(1 for f in findings if f.severity == "error")
    if errors:
        print(
            f"vibey-gh doctor: {errors} problem(s) that will break the automation", file=sys.stderr
        )
        return 1
    if findings:
        print(f"vibey-gh doctor: no blockers; {len(findings)} warning(s)")
    else:
        print("vibey-gh doctor: the automation should function")
    return 0


def _paper(args) -> int:
    from vibey_gh import paper

    try:
        tex = paper.render_paper(
            Path(args.source).read_text(encoding="utf-8"),
            author=args.author,
            journal=args.journal,
            keywords=args.keywords,
        )
    except (paper.PaperError, OSError) as error:
        print(f"vibey-gh paper: {error}", file=sys.stderr)
        return 1
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tex, encoding="utf-8")
    print(f"tex: {out}")
    return 0


def _book(args) -> int:
    from vibey_gh import book

    meta = {
        "title": args.title,
        "author": args.author,
        "subtitle": args.subtitle,
        "publisher": args.publisher,
        "description": args.description,
        "language": args.language,
    }
    try:
        written = book.build_book(
            site_dir=Path(args.site_dir),
            config_text=Path(args.config_file).read_text(encoding="utf-8"),
            output_dir=Path(args.output_dir),
            meta={k: v for k, v in meta.items() if v},
        )
    except (book.BookError, OSError) as error:
        print(f"vibey-gh book: {error}", file=sys.stderr)
        return 1
    for kind, path in written.items():
        print(f"{kind}: {path}")
    return 0


def _local_authority(args) -> int:
    from vibey_gh import local_authority

    paths = (
        [Path(p) for p in args.repos]
        if args.repos
        else local_authority.discover(Path(args.root).expanduser())
    )
    if not paths:
        print("vibey-gh local-authority: no repositories found", file=sys.stderr)
        return 1
    protected = tuple(b for b in (args.protected or "").split(",") if b)
    local_authority.run(
        paths,
        interval=args.interval,
        once=args.once,
        protected=protected,
        check=not args.no_check,
    )
    return 0


def _local_triage(args) -> int:
    from vibey_gh import local_review

    forwarded: list[str] = []
    if args.issue:
        forwarded += ["--issue", args.issue]
    forwarded += ["--model", args.model] if args.model else []
    forwarded += ["--base-url", args.base_url] if args.base_url else []
    if args.max_chars is not None:
        forwarded += ["--max-chars", str(args.max_chars)]
    if args.timeout is not None:
        forwarded += ["--timeout", str(args.timeout)]
    return local_review.triage(forwarded)


def _local_review(args) -> int:
    from vibey_gh import local_review

    forwarded: list[str] = []
    for flag, value in (
        ("--diff", args.diff),
        ("--model", args.model),
        ("--base-url", args.base_url),
        ("--max-chars", args.max_chars),
        ("--timeout", args.timeout),
    ):
        if value is not None:
            forwarded += [flag, str(value)]
    return local_review.review(forwarded)


def _conversation(args) -> int:
    cfg = load_config()
    try:
        subject = conversation.fetch_subject(args.subject)
        comments = list(subject.get("comments") or [])
        comment: dict = {}
        if args.comment_id:
            comment = next(
                (item for item in comments if conversation.matches_comment(item, args.comment_id)),
                comments[-1] if comments else {},
            )
        else:
            comment = comments[-1] if comments else {}
        if args.action == "evaluate":
            decision = conversation.evaluate(
                comment, subject, cfg, stored=conversation.parse_state(comments)
            )
            print(decision.to_json())
        elif args.action == "context":
            document = conversation.context(subject, comment, cfg, max_bytes=args.max_bytes)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(document, encoding="utf-8")
                print(f"vibey-gh: wrote {len(document.encode())} bytes to {args.output}")
            else:
                print(document, end="")
        elif args.action == "reply":
            body = _read_text(args.body)
            if not conversation.reply(args.subject, body, cfg):
                raise RuntimeError("could not post the reply")
            print(f"vibey-gh: replied on #{args.subject}")
        else:  # record-response
            state = conversation.record(args.subject, _read_json(args.input))
            print(json.dumps(asdict(state), sort_keys=True))
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    return 0


def _read_text(value: str) -> str:
    """A literal value, the contents of a file at that path, or stdin for `-`."""
    if value == "-":
        return sys.stdin.read()
    path = Path(value)
    try:
        is_file = path.is_file()
    except OSError:
        # An inline value may exceed the platform's filename length limit. A failed path
        # probe must not prevent using the value itself.
        is_file = False
    return path.read_text(encoding="utf-8") if is_file else value


def _reconcile(args) -> int:
    cfg = load_config()
    try:
        outcomes = reconcile.reconcile(cfg, dry_run=args.dry_run)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    stalled = 0
    for outcome in outcomes:
        print(
            f"  #{outcome['pr']} ({outcome['branch']}): {outcome['action']} — {outcome['reason']}"
        )
        # Deciding an action and performing it are different things: a rebase can conflict
        # and abort, a push can be refused by a lease, GitHub can decline an update. Print
        # the decision and the outcome separately, because a decision reported alone reads
        # exactly like a success and hides a branch that never moved.
        if "applied" in outcome and not outcome["applied"]:
            stalled += 1
            print(f"      not applied: {outcome.get('detail', 'no detail reported')}")
        elif outcome.get("deleted") is False:
            print("      branch deletion was refused by GitHub")
    summary = f"vibey-gh: reconciled {len(outcomes)} open pull request(s)"
    if stalled:
        summary += f"; {stalled} action(s) did not take effect"
    print(summary)
    return 0


def _rulesets(args) -> int:
    cfg = load_config()
    try:
        outcomes = rulesets.reconcile(cfg, dry_run=args.dry_run)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    for outcome in outcomes:
        state = "changed" if outcome["changed"] else "current"
        note = ""
        if outcome["unexpected_rules"]:
            note = f" — unexpected rule(s) preserved: {', '.join(outcome['unexpected_rules'])}"
        print(f"  {outcome['ruleset']} ({outcome['branch']}): {state}{note}")
    print(f"vibey-gh: reconciled {len(outcomes)} ruleset(s)")
    return 0


def _surface(args) -> int:
    try:
        arguments = json.loads(args.arguments)
        if not isinstance(arguments, list):
            raise TypeError("arguments must be a JSON array")
        capability_exit = 0
        if args.cmd == "api":
            status, payload = surfaces.api_dispatch(
                "POST",
                f"/v1/capabilities/{args.capability}",
                json.dumps({"arguments": arguments}).encode(),
            )
            if status == 200:
                capability_exit = int(payload["exit_code"])
        elif args.cmd == "mcp":
            payload = surfaces.mcp_dispatch(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": args.capability, "arguments": {"arguments": arguments}},
                }
            )
            status = 200 if "result" in payload else 400
            if status == 200:
                result_text = payload["result"]["content"][0]["text"]
                capability_exit = int(json.loads(result_text)["exit_code"])
        elif args.cmd == "sdk":
            result = surfaces.invoke(args.capability, arguments)
            status, payload = 200, result.as_dict()
            capability_exit = result.exit_code
        else:
            secret = os.environ.get("VIBEY_GH_WEBHOOK_SECRET", "").encode()
            body = json.dumps({"capability": args.capability, "arguments": arguments}).encode()
            signature = (
                "sha256="
                + __import__("hmac").new(secret, body, __import__("hashlib").sha256).hexdigest()
            )
            state_dir = Path(
                os.environ.get(
                    "VIBEY_GH_WEBHOOK_STATE_DIR",
                    str(load_config().root / ".vibey-gh" / "webhook-deliveries"),
                )
            )
            status, payload = surfaces.WebhookDispatcher(secret, delivery_dir=state_dir).dispatch(
                args.delivery, signature, body
            )
            if status == 200:
                capability_exit = int(payload["exit_code"])
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"vibey-gh: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True))
    return capability_exit if status == 200 else 1


def main(argv: list[str] | None = None) -> int:
    debugging.enable()
    parser = argparse.ArgumentParser(prog="vibey-gh", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="verify hooks and fingerprints")
    c.add_argument("--apply", action="store_true", help="add missing file headers")
    c.add_argument("--commits", metavar="RANGE", help="also check commit trailers, e.g. main..HEAD")
    c.add_argument("--quiet", action="store_true", help="exit status only, for hooks")
    c.add_argument(
        "--ci",
        action="store_true",
        help="skip the local core.hooksPath check, which no runner can satisfy",
    )
    c.set_defaults(func=_check)

    i = sub.add_parser("install", help="install the git hooks")
    i.set_defaults(func=_install)

    v = sub.add_parser("version", help="derive the version to release")
    v.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="derive against an alternate configuration — a second distribution this "
        "repository publishes. Repository-root-relative, and it does not move the root.",
    )
    v.add_argument("--since", default="origin/main")
    v.add_argument("--dev", metavar="BUILD", help="print <release>.dev<BUILD> instead")
    v.add_argument("--apply", action="store_true")
    v.add_argument("--explain", action="store_true")
    v.set_defaults(func=_version)

    for name, attr in (("trailer", "trailer"), ("trailer-key", "trailer_key")):
        p = sub.add_parser(name, help=f"print the {name}")
        p.set_defaults(func=lambda a, _attr=attr: (print(getattr(load_config(), _attr)), 0)[1])

    conventional = sub.add_parser(
        "conventional-message", help="normalize a commit message to Conventional Commits"
    )
    conventional.add_argument("--file", type=Path, help="rewrite this commit-message file")
    conventional.set_defaults(func=_conventional_message)

    conventional_check = sub.add_parser(
        "conventional-check", help="verify Conventional Commit subjects in a range"
    )
    conventional_check.add_argument("--commits", required=True, metavar="RANGE")
    conventional_check.set_defaults(func=_conventional_check)

    m = sub.add_parser("merge-train", help="merge every ready pull request")
    m.add_argument("--method", default="squash", choices=("squash", "rebase", "merge"))
    m.add_argument("--pr", type=int, help="evaluate only this pull request")
    m.add_argument("--dry-run", action="store_true")
    m.add_argument(
        "--label",
        default=merge_train.NEEDS_REVIEW_LABEL,
        help="label applied to a pull request held for the owner's review; "
        "pass an empty string to apply none",
    )
    m.add_argument(
        "--summary",
        metavar="FILE",
        help="write a markdown table here (default: $GITHUB_STEP_SUMMARY)",
    )
    m.set_defaults(func=_merge_train)

    automation = sub.add_parser(
        "pr-automation", help="evaluate and persist event-driven PR automation state"
    )
    automation_sub = automation.add_subparsers(dest="action", required=True)
    evaluate = automation_sub.add_parser("evaluate", help="classify one exact PR head")
    evaluate.add_argument("--pr", type=int, required=True)
    evaluate.add_argument("--head-sha", required=True)
    evaluate.set_defaults(func=_pr_automation)
    ready = automation_sub.add_parser(
        "ready-draft", help="mark an exact stable draft head ready for review"
    )
    ready.add_argument("--pr", type=int, required=True)
    ready.add_argument("--head-sha", required=True)
    ready.set_defaults(func=_pr_automation)
    for command in ("record-review", "record-repair"):
        record = automation_sub.add_parser(command, help=f"persist a structured {command[7:]}")
        record.add_argument("--pr", type=int, required=True)
        record.add_argument("--input", required=True, help="JSON object, file, or - for stdin")
        record.set_defaults(func=_pr_automation)
    mirror = automation_sub.add_parser(
        "mirror-fork", help="open a repository-owned replacement for a fork PR"
    )
    mirror.add_argument("--pr", type=int, required=True)
    mirror.set_defaults(func=_pr_automation)
    heal = automation_sub.add_parser(
        "self-heal", help="refill an exhausted repair budget, itself bounded"
    )
    heal.add_argument("--pr", type=int, help="one pull request; omit to sweep every exhausted one")
    heal.set_defaults(func=_pr_automation)
    labels = automation_sub.add_parser("ensure-labels", help="create or update automation labels")
    labels.set_defaults(func=_pr_automation)

    issues = sub.add_parser(
        "issue-automation", help="evaluate issues and persist autonomous solution state"
    )
    issues_sub = issues.add_subparsers(dest="action", required=True)
    issue_evaluate = issues_sub.add_parser("evaluate", help="classify one issue")
    issue_evaluate.add_argument("--issue", type=int, required=True)
    issue_evaluate.set_defaults(func=_issue_automation)
    issue_context = issues_sub.add_parser(
        "context", help="render one issue as a bounded, explicitly untrusted briefing"
    )
    issue_context.add_argument("--issue", type=int, required=True)
    issue_context.add_argument("--output", type=Path, help="write here instead of stdout")
    issue_context.add_argument(
        "--max-bytes", type=int, default=issue_automation.DEFAULT_CONTEXT_BYTES
    )
    issue_context.set_defaults(func=_issue_automation)
    issue_record = issues_sub.add_parser(
        "record-solution", help="persist a structured solution attempt"
    )
    issue_record.add_argument("--issue", type=int, required=True)
    issue_record.add_argument("--input", required=True, help="JSON object, file, or - for stdin")
    issue_record.set_defaults(func=_issue_automation)
    issue_list = issues_sub.add_parser(
        "list-eligible", help="every open issue a recovery sweep should dispatch"
    )
    issue_list.set_defaults(func=_issue_automation)
    issue_labels = issues_sub.add_parser(
        "ensure-labels", help="create or update issue automation labels"
    )
    issue_labels.set_defaults(func=_issue_automation)

    release = sub.add_parser(
        "github-release", help="idempotently create an immutable version tag and GitHub Release"
    )
    release.add_argument("--target", required=True, help="exact main commit SHA to tag")
    release.add_argument("--version", help="version override (default: configured version file)")
    release.set_defaults(func=_github_release)

    p = sub.add_parser("promote", help="promote the integration branch to the release branch")
    p.add_argument(
        "--method", default=promote.DEFAULT_METHOD, choices=("rebase", "squash", "merge")
    )
    p.add_argument("--dry-run", action="store_true")
    wait_mode = p.add_mutually_exclusive_group()
    wait_mode.add_argument(
        "--wait",
        action="store_true",
        help="legacy synchronous mode: wait for checks and merge in this process",
    )
    wait_mode.add_argument(
        "--no-wait",
        action="store_false",
        dest="wait",
        help="open the promotion PR and let event-driven automation merge it (default)",
    )
    p.add_argument(
        "--summary", metavar="FILE", help="write markdown here (default: $GITHUB_STEP_SUMMARY)"
    )
    p.set_defaults(func=_promote)

    r = sub.add_parser("realign", help="realign the integration branch with the release branch")
    r.set_defaults(func=_realign)

    y = sub.add_parser(
        "report-superseded",
        help="report which releases the published one supersedes (PyPI has no yank API)",
    )
    y.add_argument("--index", choices=["pypi", "testpypi"], required=True)
    y.add_argument("--project", required=True, help="the distribution name on the index")
    y.add_argument("--version", required=True, help="the version just published; never listed")
    y.add_argument(
        "--governance-since",
        default="",
        help=(
            "git ref opening the release range; if the range touches a governance file"
            " (constitution, commandments, bill of rights, standing subdoctrines), every"
            " previous release is reported superseded — Article V.4, zero exceptions"
        ),
    )
    y.set_defaults(func=_report_superseded)

    local = sub.add_parser(
        "local-review",
        help="review a diff with a local model when the paid review path returns no verdict",
    )
    local.add_argument("--diff", help="path to a diff file (default: stdin)")
    local.add_argument("--model", help="override [pr_automation.fallback] model")
    local.add_argument("--base-url", help="override [pr_automation.fallback] base_url")
    local.add_argument("--max-chars", type=int, help="override max_diff_chars")
    local.add_argument("--timeout", type=int, help="override timeout_seconds")
    local.set_defaults(func=_local_review)

    doc = sub.add_parser(
        "doctor",
        help="will the automation actually work? — the adoption preflight, offline",
    )
    doc.set_defaults(func=_doctor)

    ty = sub.add_parser(
        "tidy",
        help="the clean repo (9.a): survey technical clutter; --apply removes the lossless classes",
    )
    ty.add_argument(
        "--apply", action="store_true", help="delete merged/gone refs and prune worktrees"
    )
    ty.add_argument(
        "--ci", action="store_true", help="cloud classes only (no local-clone judgments)"
    )
    ty.set_defaults(func=_tidy)

    la = sub.add_parser(
        "local-authority",
        help="keep remotes tracking green local branches — the capped-lane sync loop",
    )
    la.add_argument("--repos", nargs="*", help="explicit repository paths (default: scan --root)")
    la.add_argument(
        "--root", default="~/git", help="scanned for work trees carrying .vibey-gh.toml"
    )
    la.add_argument("--interval", type=int, default=120, help="seconds between passes")
    la.add_argument("--once", action="store_true", help="one pass, then exit")
    la.add_argument(
        "--protected",
        default="",
        help="comma-separated branches never pushed (default: each repo's own integration and release branches)",
    )
    la.add_argument("--no-check", action="store_true", help="skip the per-repo provenance check")
    la.set_defaults(func=_local_authority)

    fo = sub.add_parser(
        "failover",
        help="hand the operator seat to a local agent while the paid lane is out of credit",
    )
    fo.add_argument(
        "--config",
        default="",
        help="machine-level TOML (default ~/.config/vibey-gh/failover.toml); missing file = disabled",
    )
    fo.add_argument(
        "--state",
        default="",
        help="seat-state file (default ~/.local/state/vibey-gh/failover.json)",
    )
    fo.add_argument("--once", action="store_true", help="one probe and transition, then exit")
    fo.set_defaults(func=_failover)

    ci_ = sub.add_parser(
        "corpus-index",
        help="build the governance corpus index — chunked, hashed, deterministic (#249)",
    )
    ci_.add_argument("--check", action="store_true", help="fail loudly on corpus drift")
    ci_.set_defaults(func=_corpus_index)

    mk = sub.add_parser(
        "marketplace",
        help="render the root Claude Code marketplace from the workspace members",
    )
    mk.add_argument(
        "--check", action="store_true", help="fail loudly when the root manifest drifts"
    )
    mk.set_defaults(func=_marketplace)

    sv = sub.add_parser(
        "sovereign",
        help="sovereign readiness (8.a): publish or read the local runner's heartbeat",
    )
    sv.add_argument("--beat", action="store_true", help="publish a heartbeat (run on a timer)")
    sv.add_argument("--remote", default="origin", help="git remote carrying the heartbeat ref")
    sv.set_defaults(func=_sovereign)

    ft = sub.add_parser(
        "fit",
        help="the fit calculus (#263): both sides measured, the projection stated",
    )
    ft.add_argument("--model", default="qwen2.5-coder:14b", help="the model actually wanted")
    ft.add_argument("--queue", type=int, default=0, help="jobs already ahead of this one")
    ft.add_argument("--payload-bytes", type=int, default=8192, help="size of the work")
    ft.add_argument("--deadline", type=float, default=900.0, help="the caller's deadline")
    ft.add_argument(
        "--observed-seconds",
        type=float,
        help="record what this payload ACTUALLY took, feeding the estimate (#263)",
    )
    ft.add_argument(
        "--journal",
        help="record this decision, and read prior ones back, so repeated calls"
        " form a self-adjusting loop (#263)",
    )
    ft.set_defaults(func=_fit)

    pp = sub.add_parser(
        "paper",
        help="render docs/paper.md as a journal-class LaTeX document (IEEEtran)",
    )
    pp.add_argument("--source", default="docs/paper.md")
    pp.add_argument("--output", default="paper/paper.tex")
    pp.add_argument("--author", required=True)
    pp.add_argument("--journal", action="store_true", help="journal layout instead of conference")
    pp.add_argument("--keywords", default="")
    pp.set_defaults(func=_paper)
    bk = sub.add_parser(
        "book",
        help="export the built docs site as an EPUB and a KDP print-ready HTML",
    )
    bk.add_argument("--site-dir", required=True, help="the built site directory")
    bk.add_argument(
        "--config-file",
        default="properdocs.yml",
        help="site configuration whose nav orders the chapters",
    )
    bk.add_argument("--output-dir", default="book", help="where book files are written")
    bk.add_argument("--title", required=True)
    bk.add_argument("--author", required=True)
    bk.add_argument("--subtitle", default="")
    bk.add_argument("--publisher", default="")
    bk.add_argument("--description", default="")
    bk.add_argument("--language", default="en")
    bk.set_defaults(func=_book)

    lt = sub.add_parser(
        "local-triage",
        help="triage an issue with a local model when the paid solver produced nothing",
    )
    lt.add_argument("--issue", help="path to a file with the issue text (default: stdin)")
    lt.add_argument("--model", default="")
    lt.add_argument("--base-url", default="")
    lt.add_argument("--max-chars", type=int, default=None)
    lt.add_argument("--timeout", type=int, default=None)
    lt.set_defaults(func=_local_triage)

    talk = sub.add_parser("conversation", help="respond to a mention in a comment")
    talk_sub = talk.add_subparsers(dest="action", required=True)
    for name, helptext in (
        ("evaluate", "decide whether one comment gets a response"),
        ("context", "render the thread as a bounded, untrusted briefing"),
        ("reply", "post an answer as a comment"),
        ("record-response", "persist one interaction against the thread"),
    ):
        item = talk_sub.add_parser(name, help=helptext)
        item.add_argument("--subject", type=int, required=True, help="issue or PR number")
        item.add_argument("--comment-id", help="exact comment; omit for the newest")
        if name == "context":
            item.add_argument("--output", type=Path)
            item.add_argument("--max-bytes", type=int, default=conversation.DEFAULT_CONTEXT_BYTES)
        if name == "reply":
            item.add_argument("--body", required=True, help="text, file, or - for stdin")
        if name == "record-response":
            item.add_argument("--input", required=True, help="JSON object, file, or - for stdin")
        item.set_defaults(func=_conversation)

    rec = sub.add_parser(
        "reconcile-branches",
        help="rebase, close, or leave open branches stranded by a realign rewrite",
    )
    rec.add_argument("--dry-run", action="store_true", help="decide without mutating anything")
    rec.set_defaults(func=_reconcile)

    rs = sub.add_parser("rulesets", help="reconcile the integration and release branch rulesets")
    rs.add_argument("--dry-run", action="store_true", help="decide without applying anything")
    rs.set_defaults(func=_rulesets)

    for surface in ("api", "mcp", "sdk", "webhook"):
        adapter = sub.add_parser(surface, help=f"invoke a capability through the {surface} adapter")
        adapter.add_argument("capability", choices=surfaces.CAPABILITIES)
        adapter.add_argument("--arguments", default="[]", help="JSON array of capability arguments")
        if surface == "webhook":
            adapter.add_argument("--delivery", required=True, help="unique webhook delivery ID")
        adapter.set_defaults(func=_surface)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
