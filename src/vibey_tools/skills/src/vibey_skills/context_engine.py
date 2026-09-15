# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Deterministic, offline retrieval and context compilation for Agent Skills."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import urllib.parse
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import __version__, marketplace_manifest, plugins_root

SCHEMA_VERSION = 1
INDEX_VERSION = 1
MIN_BUDGET = 1_000
MAX_BUDGET = 32_000
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")
_SECRET = re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+")
_SECRET_VALUE = re.compile(r"(?i)\b(?:sk-|ghp_|github_pat_|xox[baprs]-)[-A-Za-z0-9_]{8,}\b")
_REQUEST_FIELDS = {
    "schema_version",
    "title",
    "objective",
    "requirements",
    "acceptance_criteria",
    "phase",
    "job_kind",
    "languages",
    "dependencies",
    "paths",
    "commands",
    "target_files",
    "changed_files",
    "prior_failure_class",
    "error_summary",
    "required_plugins",
    "excluded_plugins",
    "required_skills",
    "excluded_skills",
    "maximum_context_tokens",
    "ranking_mode",
    "compatibility_mode",
}
_LIST_FIELDS = {
    "requirements",
    "acceptance_criteria",
    "languages",
    "dependencies",
    "paths",
    "commands",
    "target_files",
    "changed_files",
    "required_plugins",
    "excluded_plugins",
    "required_skills",
    "excluded_skills",
}
_METADATA_LISTS = {"domains", "phases", "languages", "technologies", "mandatory_sections"}


class ContextEngineError(ValueError):
    """Invalid corpus, request, or index input."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def estimate_tokens(text: str) -> int:
    """Stable zero-dependency approximation: UTF-8 characters divided by four."""
    return (len(text) + 3) // 4


def redact_secrets(text: str) -> str:
    """Remove common labelled and provider-shaped secrets from persisted query data."""
    return _SECRET_VALUE.sub("[REDACTED]", _SECRET.sub(r"\1=[REDACTED]", text))


def _safe_index_dir(path: Path, *, create: bool) -> Path:
    """Resolve an index directory without accepting a symlink as the write boundary."""
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ContextEngineError(f"index directory must not be a symlink: {expanded}")
    resolved = expanded.resolve()
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    elif not resolved.is_dir():
        raise ContextEngineError(f"index directory does not exist: {expanded}")
    return resolved


def _frontmatter(lines: list[str]) -> tuple[dict[str, Any], int]:
    if not lines or lines[0].strip() != "---":
        raise ContextEngineError("SKILL.md has no frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ContextEngineError("SKILL.md has unterminated frontmatter") from exc
    data: dict[str, Any] = {}
    key = ""
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace() and raw.strip().startswith("-"):
            if key not in _METADATA_LISTS:
                raise ContextEngineError(f"list value is not allowed for {key!r}")
            data.setdefault(key, []).append(raw.strip()[1:].strip().strip("\"'"))
            continue
        if raw[:1].isspace() and key and isinstance(data.get(key), str):
            data[key] = (data[key] + " " + raw.strip()).strip()
            continue
        if ":" not in raw:
            raise ContextEngineError(f"invalid frontmatter line: {raw!r}")
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", key):
            raise ContextEngineError(f"invalid frontmatter key: {key!r}")
        if key in data:
            raise ContextEngineError(f"duplicate frontmatter key: {key}")
        data[key] = [] if not value and key in _METADATA_LISTS else value.strip("\"'")
    return data, end + 1


def _content_class(heading: str, mandatory: set[str]) -> str:
    if heading in mandatory:
        return "mandatory"
    lower = heading.lower()
    if "source" in lower or "reference" in lower:
        return "source" if "source" in lower else "reference"
    if "example" in lower:
        return "example"
    return "procedure"


def _normal(text: str) -> str:
    return " ".join(token.lower() for token in _TOKEN.findall(text))


def build_manifest(root: Path | None = None) -> dict[str, Any]:
    root = (root or plugins_root()).resolve()
    if root.is_symlink() or not root.is_dir():
        raise ContextEngineError(f"invalid plugin root: {root}")
    entries = {item["name"]: item for item in marketplace_manifest().get("plugins", [])}
    skills: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    names: set[str] = set()
    paths = sorted(root.glob("*/skills/*/SKILL.md"), key=lambda p: p.as_posix())
    if not paths:
        raise ContextEngineError(f"no authoritative SKILL.md files under {root}")
    for path in paths:
        resolved = path.resolve()
        if root not in resolved.parents or path.is_symlink():
            raise ContextEngineError(f"skill source escapes plugin root: {path}")
        plugin, directory_name = path.parts[-4], path.parts[-2]
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        metadata, body_start = _frontmatter(lines)
        name = metadata.get("name")
        description = metadata.get("description")
        if name != directory_name or not isinstance(description, str) or not description:
            raise ContextEngineError(f"invalid name or description in {path}")
        if name in names:
            raise ContextEngineError(f"duplicate skill name: {name}")
        names.add(name)
        for field in _METADATA_LISTS:
            if field in metadata and not isinstance(metadata[field], list):
                raise ContextEngineError(f"{field} must be a list in {path}")
        if "retrieval_version" in metadata and metadata["retrieval_version"] != "1":
            raise ContextEngineError(f"unsupported retrieval_version in {path}")
        source_hash = sha256(text)
        heading_stack: list[str] = []
        starts: list[tuple[int, int, list[str], str]] = []
        for index in range(body_start, len(lines)):
            match = _HEADING.match(lines[index].rstrip("\r\n"))
            if match:
                level, title = len(match.group(1)), match.group(2).strip()
                heading_stack = heading_stack[: level - 1] + [title]
                starts.append((index, level, list(heading_stack), title))
        headings = [item[3] for item in starts]
        mandatory = set(metadata.get("mandatory_sections", []))
        missing = mandatory.difference(headings)
        if missing:
            raise ContextEngineError(f"missing mandatory heading(s) in {path}: {sorted(missing)}")
        relative = path.relative_to(root.parent).as_posix()
        skill = {
            "plugin": plugin,
            "name": name,
            "description": description,
            "version": entries.get(plugin, {}).get("version", ""),
            "category": entries.get(plugin, {}).get("category", ""),
            "source_path": relative,
            "source_sha256": source_hash,
            "headings": headings,
            "mandatory_sections": sorted(mandatory),
            "retrieval": {
                k: metadata[k]
                for k in sorted(_METADATA_LISTS | {"retrieval_version"})
                if k in metadata
            },
        }
        skills.append(skill)
        retrieval_terms = " ".join(
            value
            for field in ("domains", "phases", "languages", "technologies")
            for value in metadata.get(field, [])
        )
        for position, (start, _level, heading_path, title) in enumerate(starts):
            end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
            content = "".join(lines[start:end]).rstrip() + "\n"
            content_hash = sha256(content)
            chunks.append(
                {
                    "id": sha256(canonical_json([source_hash, heading_path, start + 1]))[:24],
                    "plugin": plugin,
                    "skill": name,
                    "skill_version": skill["version"],
                    "heading_path": heading_path,
                    "heading": title,
                    "source_path": relative,
                    "line_start": start + 1,
                    "line_end": end,
                    "content_sha256": content_hash,
                    "content_class": _content_class(title, mandatory),
                    "text": content,
                    "normalized_text": _normal(
                        " ".join(heading_path)
                        + " "
                        + description
                        + " "
                        + retrieval_terms
                        + " "
                        + content
                    ),
                    "token_estimate": estimate_tokens(content),
                }
            )
    core = {
        "schema_version": SCHEMA_VERSION,
        "skills_release": __version__,
        "skills": skills,
        "chunks": chunks,
    }
    core["corpus_sha256"] = sha256(canonical_json(core))
    return core


def build_index(output: Path, root: Path | None = None) -> dict[str, Any]:
    output = _safe_index_dir(output, create=True)
    manifest = build_manifest(root)
    temp = output / "index.sqlite3.tmp"
    temp.unlink(missing_ok=True)
    connection = sqlite3.connect(temp)
    try:
        connection.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE chunks (id TEXT PRIMARY KEY, document TEXT NOT NULL);
            CREATE VIRTUAL TABLE chunk_fts USING fts5(id UNINDEXED, plugin, skill, heading, text, tokenize='unicode61');
        """)
        connection.execute(
            "INSERT INTO metadata VALUES (?, ?)", ("index_version", str(INDEX_VERSION))
        )
        connection.execute(
            "INSERT INTO metadata VALUES (?, ?)", ("corpus_sha256", manifest["corpus_sha256"])
        )
        for chunk in manifest["chunks"]:
            connection.execute(
                "INSERT INTO chunks VALUES (?, ?)", (chunk["id"], canonical_json(chunk))
            )
            connection.execute(
                "INSERT INTO chunk_fts VALUES (?, ?, ?, ?, ?)",
                (
                    chunk["id"],
                    chunk["plugin"],
                    chunk["skill"],
                    " ".join(chunk["heading_path"]),
                    chunk["normalized_text"],
                ),
            )
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()
    temp.replace(output / "index.sqlite3")
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _load_manifest(index_dir: Path) -> tuple[Path, dict[str, Any]]:
    index_dir = _safe_index_dir(index_dir, create=False)
    try:
        manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextEngineError(f"invalid index manifest in {index_dir}: {exc}") from exc
    required = {"schema_version", "skills_release", "corpus_sha256", "skills", "chunks"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ContextEngineError(f"invalid index manifest schema in {index_dir}")
    core = {key: manifest[key] for key in ("schema_version", "skills_release", "skills", "chunks")}
    if manifest["corpus_sha256"] != sha256(canonical_json(core)):
        raise ContextEngineError(f"index manifest digest mismatch in {index_dir}")
    if not (index_dir / "index.sqlite3").is_file():
        raise ContextEngineError(f"index database is missing in {index_dir}")
    return index_dir, manifest


def inspect_index(index_dir: Path) -> dict[str, Any]:
    _, manifest = _load_manifest(index_dir)
    return {
        "schema_version": manifest["schema_version"],
        "index_version": INDEX_VERSION,
        "skills_release": manifest["skills_release"],
        "corpus_sha256": manifest["corpus_sha256"],
        "skill_count": len(manifest["skills"]),
        "chunk_count": len(manifest["chunks"]),
    }


def validate_request(request: dict[str, Any], *, budget: int | None = None) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ContextEngineError("request must be a JSON object")
    compatibility = request.get("compatibility_mode", "strict")
    unknown = set(request).difference(_REQUEST_FIELDS)
    if unknown and compatibility != "forward-1":
        raise ContextEngineError(f"unknown request field(s): {sorted(unknown)}")
    clean = {k: v for k, v in request.items() if k in _REQUEST_FIELDS}
    if clean.get("schema_version", 1) != 1:
        raise ContextEngineError("unsupported request schema_version")
    for field in _LIST_FIELDS:
        if field in clean and (
            not isinstance(clean[field], list) or not all(isinstance(v, str) for v in clean[field])
        ):
            raise ContextEngineError(f"{field} must be a list of strings")
    for field, value in clean.items():
        if (
            field not in _LIST_FIELDS
            and field not in {"schema_version", "maximum_context_tokens"}
            and not isinstance(value, str)
        ):
            raise ContextEngineError(f"{field} must be a string")
    maximum = budget if budget is not None else clean.get("maximum_context_tokens", 6000)
    if not isinstance(maximum, int) or not MIN_BUDGET <= maximum <= MAX_BUDGET:
        raise ContextEngineError(f"budget must be between {MIN_BUDGET} and {MAX_BUDGET}")
    clean["maximum_context_tokens"] = maximum
    clean.setdefault("schema_version", 1)
    clean.setdefault("ranking_mode", "deterministic")
    if clean["ranking_mode"] != "deterministic":
        raise ContextEngineError("only deterministic ranking is available")
    return _redact_request(clean)


def _redact_request(request: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in request.items():
        if isinstance(value, str):
            redacted[key] = redact_secrets(value)
        elif isinstance(value, list):
            redacted[key] = [redact_secrets(item) for item in value]
        else:
            redacted[key] = value
    return redacted


def _request_text(request: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "title",
        "objective",
        "requirements",
        "acceptance_criteria",
        "phase",
        "job_kind",
        "languages",
        "dependencies",
        "paths",
        "commands",
        "target_files",
        "changed_files",
        "prior_failure_class",
        "error_summary",
    ):
        value = request.get(key, [])
        parts.extend(value if isinstance(value, list) else [value])
    return redact_secrets(" ".join(parts))


def _fts_query(text: str) -> str:
    words = sorted(set(token.lower() for token in _TOKEN.findall(text) if len(token) > 1))
    return " OR ".join('"' + word.replace('"', '""') + '"' for word in words[:128])


def search(
    index_dir: Path, request: dict[str, Any] | str, *, limit: int = 20
) -> list[dict[str, Any]]:
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        raise ContextEngineError("search limit must be between 1 and 500")
    request = (
        validate_request({"objective": request})
        if isinstance(request, str)
        else validate_request(request)
    )
    fts = _fts_query(_request_text(request))
    if not fts and not request.get("required_plugins") and not request.get("required_skills"):
        return []
    required_plugins, excluded_plugins = (
        set(request.get("required_plugins", [])),
        set(request.get("excluded_plugins", [])),
    )
    required_skills, excluded_skills = (
        set(request.get("required_skills", [])),
        set(request.get("excluded_skills", [])),
    )
    index_dir, _ = _load_manifest(index_dir)
    # URI-escape the path: SQLite's URI parser truncates at `?` or `#` and %-decodes,
    # so an unescaped checkout path containing those opens the wrong file or none.
    escaped = urllib.parse.quote(str(index_dir / "index.sqlite3"))
    connection = sqlite3.connect(f"file:{escaped}?mode=ro", uri=True)
    try:
        rows = []
        if fts:
            rows.extend(
                connection.execute(
                    "SELECT c.document, bm25(chunk_fts, 0.0, 4.0, 6.0, 2.0) FROM chunk_fts "
                    "JOIN chunks c ON c.id = chunk_fts.id WHERE chunk_fts MATCH ? "
                    "ORDER BY 2, chunk_fts.id LIMIT 500",
                    (fts,),
                ).fetchall()
            )
        if required_plugins or required_skills:
            # Explicit activation precedes lexical ranking. The identifiers remain values,
            # never SQL fragments, and duplicate documents are removed below.
            for (raw,) in connection.execute("SELECT document FROM chunks ORDER BY id"):
                chunk = json.loads(raw)
                if chunk["plugin"] in required_plugins or chunk["skill"] in required_skills:
                    rows.append((raw, 0.0))
    finally:
        connection.close()
    signals = {
        token.lower()
        for field in ("phase", "languages", "dependencies", "commands", "paths")
        for token in _TOKEN.findall(
            " ".join(request.get(field, []))
            if isinstance(request.get(field), list)
            else str(request.get(field, ""))
        )
    }
    ranked = []
    seen_ids: set[str] = set()
    for raw, bm25 in rows:
        chunk = json.loads(raw)
        if chunk["id"] in seen_ids:
            continue
        seen_ids.add(chunk["id"])
        if (required_plugins and chunk["plugin"] not in required_plugins) or chunk[
            "plugin"
        ] in excluded_plugins:
            continue
        if (required_skills and chunk["skill"] not in required_skills) or chunk[
            "skill"
        ] in excluded_skills:
            continue
        matched = sorted(signals.intersection(set(chunk["normalized_text"].split())))
        boost = (
            len(matched) * 10
            + (100 if chunk["plugin"] in required_plugins else 0)
            + (100 if chunk["skill"] in required_skills else 0)
            + (50 if chunk["content_class"] == "mandatory" else 0)
        )
        chunk["score"] = round(-float(bm25) + boost, 6)
        chunk["reasons"] = (
            ["lexical_match"]
            + ["signal:" + value for value in matched]
            + (["required_plugin"] if chunk["plugin"] in required_plugins else [])
            + (["required_skill"] if chunk["skill"] in required_skills else [])
        )
        ranked.append(chunk)
    ranked.sort(key=lambda item: (-item["score"], item["plugin"], item["skill"], item["id"]))
    return ranked[:limit]


def compile_packet(
    index_dir: Path, raw_request: dict[str, Any], *, budget: int | None = None
) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter_ns()
    request = validate_request(raw_request, budget=budget)
    index_dir, manifest = _load_manifest(index_dir)
    ranked = search(index_dir, request, limit=60)
    activated: list[tuple[str, str]] = []
    required_skills = set(request.get("required_skills", []))
    required_plugins = set(request.get("required_plugins", []))
    for skill in manifest["skills"]:
        pair = (skill["plugin"], skill["name"])
        if skill["name"] in required_skills or skill["plugin"] in required_plugins:
            activated.append(pair)
    for item in ranked:
        pair = (item["plugin"], item["skill"])
        if pair not in activated:
            activated.append(pair)
        if len(activated) >= max(4, len(required_skills) + len(required_plugins)):
            break
    by_id = {chunk["id"]: chunk for chunk in manifest["chunks"]}
    mandatory = sorted(
        (
            chunk
            for chunk in manifest["chunks"]
            if chunk["content_class"] == "mandatory"
            and (chunk["plugin"], chunk["skill"]) in activated
        ),
        key=lambda item: (item["plugin"], item["skill"], item["line_start"]),
    )
    selected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    header = "# Vibey Skills Context Packet\n\n"
    for chunk in mandatory:
        if chunk["content_sha256"] not in seen_hashes:
            selected.append({**chunk, "score": None, "reasons": ["mandatory_section"]})
            seen_hashes.add(chunk["content_sha256"])
    maximum = request["maximum_context_tokens"]
    query_hash = sha256(canonical_json(request))
    base = {
        "schema_version": 1,
        "index_version": INDEX_VERSION,
        "query_sha256": query_hash,
        "corpus_sha256": manifest["corpus_sha256"],
        "skills_release": manifest["skills_release"],
    }
    mandatory_markdown = _render_packet(header, selected)
    used = estimate_tokens(mandatory_markdown)
    if used > maximum:
        return "", {
            **base,
            "status": "budget_insufficient",
            "maximum_context_tokens": maximum,
            "mandatory_token_estimate": used,
            "included_chunks": [],
            "omitted_chunks": [],
        }
    omitted: list[dict[str, Any]] = []
    for item in ranked:
        chunk = by_id[item["id"]]
        if chunk["content_sha256"] in seen_hashes:
            continue
        candidate_chunk = {**chunk, "score": item["score"], "reasons": item["reasons"]}
        candidate_markdown = _render_packet(header, [*selected, candidate_chunk])
        if estimate_tokens(candidate_markdown) <= maximum:
            selected.append(candidate_chunk)
            seen_hashes.add(chunk["content_sha256"])
            used = estimate_tokens(candidate_markdown)
        else:
            omitted.append(
                {"id": chunk["id"], "reason": "budget", "token_estimate": chunk["token_estimate"]}
            )
    if not selected:
        return "", {
            **base,
            "status": "low_confidence",
            "fallback": "activate_full_native_skills",
            "maximum_context_tokens": maximum,
            "included_chunks": [],
            "omitted_chunks": omitted,
        }
    markdown = _render_packet(header, selected)
    included = [
        {
            k: chunk[k]
            for k in (
                "id",
                "plugin",
                "skill",
                "heading_path",
                "source_path",
                "line_start",
                "line_end",
                "content_sha256",
                "token_estimate",
                "score",
                "reasons",
            )
        }
        for chunk in selected
    ]
    packet = {
        **base,
        "status": "ok",
        "deterministic_signals": json.loads(canonical_json(request)),
        "selected_plugins": sorted({c["plugin"] for c in selected}),
        "selected_skills": sorted({c["skill"] for c in selected}),
        "included_chunks": included,
        "omitted_chunks": omitted,
        "mandatory_token_estimate": sum(
            c["token_estimate"] for c in selected if c["content_class"] == "mandatory"
        ),
        "retrieved_token_estimate": sum(
            c["token_estimate"] for c in selected if c["content_class"] != "mandatory"
        ),
        "packet_token_estimate": estimate_tokens(markdown),
        "maximum_context_tokens": maximum,
        "retrieval_latency_ns": time.perf_counter_ns() - started,
        "fallback": None,
        "packet_sha256": sha256(markdown),
    }
    return markdown, packet


def _render_packet(header: str, chunks: Iterable[dict[str, Any]]) -> str:
    sections = [header.rstrip()]
    sections.extend(
        f"<!-- {chunk['source_path']}:{chunk['line_start']}-{chunk['line_end']} "
        f"sha256:{chunk['content_sha256']} -->\n{chunk['text'].rstrip()}"
        for chunk in chunks
    )
    return "\n\n".join(sections) + "\n"


def evaluate(index_dir: Path, cases_path: Path, *, top_k: int = 10) -> dict[str, Any]:
    """Evaluate replayable retrieval cases without persisting task or repository text."""
    if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
        raise ContextEngineError("top_k must be between 1 and 100")
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextEngineError(f"invalid evaluation cases: {exc}") from exc
    if not isinstance(cases, list) or len(cases) < 50:
        raise ContextEngineError("evaluation set must contain at least 50 cases")
    results: list[dict[str, Any]] = []
    expected_total = 0
    found_total = 0
    mandatory_total = 0
    mandatory_found = 0
    for position, case in enumerate(cases, 1):
        if not isinstance(case, dict) or not isinstance(case.get("request"), dict):
            raise ContextEngineError(f"evaluation case {position} has no request object")
        expected = case.get("expected_skills", [])
        mandatory = case.get("mandatory_headings", [])
        if not isinstance(expected, list) or not all(isinstance(v, str) for v in expected):
            raise ContextEngineError(f"evaluation case {position} has invalid expected_skills")
        if not isinstance(mandatory, list) or not all(isinstance(v, str) for v in mandatory):
            raise ContextEngineError(f"evaluation case {position} has invalid mandatory_headings")
        matches = search(index_dir, case["request"], limit=top_k)
        found_skills = {item["skill"] for item in matches}
        found_headings = {item["heading"] for item in matches}
        expected_total += len(expected)
        found_total += len(set(expected).intersection(found_skills))
        mandatory_total += len(mandatory)
        mandatory_found += len(set(mandatory).intersection(found_headings))
        results.append(
            {
                "case_id": str(case.get("id", position)),
                "query_sha256": sha256(canonical_json(validate_request(case["request"]))),
                "expected_skills": expected,
                "found_skills": sorted(found_skills),
                "missing_skills": sorted(set(expected).difference(found_skills)),
                "missing_mandatory_headings": sorted(set(mandatory).difference(found_headings)),
            }
        )
    return {
        "schema_version": 1,
        "case_count": len(cases),
        "top_k": top_k,
        "skill_recall": found_total / expected_total if expected_total else 1.0,
        "mandatory_recall": mandatory_found / mandatory_total if mandatory_total else 1.0,
        "passed_mandatory_recall": mandatory_found == mandatory_total,
        "results": results,
    }
