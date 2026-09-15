# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The governance corpus index (#249): the founding documents, chunked and hashed.

Builds a deterministic, content-addressed index of the governance corpus — the
Twelve Doctrines, the Constitution, the Ten Commandments, the Bill of Rights, and
the standing subdoctrines — in the spirit of vibey-skills' retrieval engine: each
document split at its headings into retrieval-grade chunks, every chunk carrying
its sha256, its source document, and its heading anchor, so any agent or human tool
can pull exactly the clause it needs and verify it in one hash.

Three properties are load-bearing:

- **deterministic**: the same corpus always produces the same bytes — the index is
  built FROM the documents at publish time, never hand-maintained, never a second
  source of truth;
- **integrity-walkable**: the index's chunk hashes chain into a single corpus hash,
  so drift between published law and its index is detectable in one comparison —
  the mechanical property Articles IV.5–6 and V.4 assume;
- **human order preserved**: the canonical Markdown stays the human's first-class
  document, untouched; this index is the machine's layer, second, as doctrine 7
  orders.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from vibey_gh.config import GhConfig

__all__ = ["CORPUS_DOCUMENTS", "Chunk", "build", "check", "write"]

# The governance corpus, in the constitutional cluster's own order. sd-*.md globs in
# the standing subdoctrines so future SD filings index without a code change.
CORPUS_DOCUMENTS = (
    "docs/doctrines.md",
    "docs/constitution.md",
    "docs/commandments.md",
    "docs/bill-of-rights.md",
    "docs/sd-*.md",
)

INDEX_PATH = "corpus-index.json"


@dataclass(frozen=True)
class Chunk:
    document: str  # repository-relative source path
    anchor: str  # the heading line this chunk begins at ("" for a preamble)
    start_line: int  # 1-based line of the heading (or 1 for a preamble)
    sha256: str  # hash of the chunk's exact text
    text_lines: int


def _documents(cfg: GhConfig) -> list[Path]:
    found: list[Path] = []
    for pattern in CORPUS_DOCUMENTS:
        if "*" in pattern:
            base, _, glob = pattern.rpartition("/")
            found.extend(sorted((cfg.root / base).glob(glob)))
        else:
            path = cfg.root / pattern
            if path.is_file():
                found.append(path)
    # De-duplicate while preserving the constitutional order.
    seen: set[Path] = set()
    ordered = []
    for path in found:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _chunks_of(cfg: GhConfig, path: Path) -> list[Chunk]:
    rel = path.relative_to(cfg.root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    chunks: list[Chunk] = []
    anchor, start = "", 1
    buffer: list[str] = []

    def flush() -> None:
        text = "\n".join(buffer)
        if text.strip():
            chunks.append(
                Chunk(
                    document=rel,
                    anchor=anchor,
                    start_line=start,
                    sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    text_lines=len(buffer),
                )
            )

    for i, line in enumerate(lines, start=1):
        if line.startswith("#"):
            flush()
            anchor, start = line.lstrip("#").strip(), i
            buffer = [line]
        else:
            buffer.append(line)
    flush()
    return chunks


def build(cfg: GhConfig) -> dict:
    """The whole index: every chunk, plus one corpus hash chaining them all."""
    chunks = [c for path in _documents(cfg) for c in _chunks_of(cfg, path)]
    walk = hashlib.sha256()
    for c in chunks:
        walk.update(c.sha256.encode("ascii"))
    return {
        "corpus_sha256": walk.hexdigest(),
        "documents": [p.relative_to(cfg.root).as_posix() for p in _documents(cfg)],
        "chunks": [asdict(c) for c in chunks],
    }


def write(cfg: GhConfig, out: Path | None = None) -> Path:
    """Deterministic bytes: same corpus, same file, byte for byte."""
    target = out or (cfg.root / INDEX_PATH)
    index = build(cfg)
    target.write_text(
        json.dumps(index, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def check(cfg: GhConfig, index_path: Path | None = None) -> tuple[bool, str]:
    """Drift between the published index and the documents fails loudly (#249)."""
    target = index_path or (cfg.root / INDEX_PATH)
    if not target.is_file():
        return False, f"{target.name} is missing — the corpus has law but no index"
    try:
        stored = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, f"{target.name} is not valid JSON"
    current = build(cfg)
    if stored.get("corpus_sha256") != current["corpus_sha256"]:
        return False, (
            "corpus drift: the index does not match the documents — regenerate with"
            " `vibey-gh corpus-index` (stored"
            f" {str(stored.get('corpus_sha256'))[:12]}…, current"
            f" {current['corpus_sha256'][:12]}…)"
        )
    return True, f"corpus intact: {len(current['chunks'])} chunk(s), one hash walk"
