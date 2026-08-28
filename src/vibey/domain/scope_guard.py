# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Scope-bound mutation guard for Phase 2 implementation isolation (Milestone 9 task 9.3)."""

import posixpath
import re
from collections.abc import Sequence


class ScopeViolation(Exception):
    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Scope violation on '{path}': {reason}")
        self.path = path
        self.reason = reason


_FORBIDDEN_FILE_RE = re.compile(
    r"(^|/|\\)(\.git(/|\\|$)|secrets\.json|id_rsa|id_ed25519|id_ecdsa|\.env(\.[a-z0-9_-]+)?($|/|\\))",
    re.IGNORECASE,
)


class MutationScope:
    """Enforces that mutations are confined within declared scope boundaries."""

    def __init__(
        self,
        *,
        worktree_root: str,
        allowed_paths: Sequence[str] | None = None,
        allow_new_files: bool = True,
    ) -> None:
        self.worktree_root = worktree_root.replace("\\", "/").rstrip("/")
        self.allow_new_files = allow_new_files

        norm_allowed: list[str] = []
        for p in allowed_paths or []:
            p_str = p.strip().replace("\\", "/")
            p_str = p_str.removeprefix("./")
            if p_str and p_str != ".":
                norm_allowed.append(p_str)
        self.allowed_paths: tuple[str, ...] = tuple(norm_allowed)

    def _resolve_relative(self, path: str) -> str | None:
        p_str = path.strip().replace("\\", "/")
        if not p_str:
            return None

        # Handle absolute paths against worktree_root

        if p_str.startswith("/"):
            if not p_str.startswith(self.worktree_root):
                return None
            rel = p_str[len(self.worktree_root) :].lstrip("/")
        else:
            rel = p_str

        normalized = posixpath.normpath(rel)

        # Check for forbidden after norm
        if _FORBIDDEN_FILE_RE.search(normalized):
            return None

        # Path traversal check
        if normalized == ".." or normalized.startswith("../"):
            return None

        return normalized

    def is_path_allowed(self, path: str) -> bool:
        rel = self._resolve_relative(path)
        if rel is None:
            return False

        if not self.allowed_paths:
            return True

        for allowed in self.allowed_paths:
            clean_allowed = allowed.rstrip("/")
            if rel == clean_allowed or rel.startswith(f"{clean_allowed}/"):
                return True
        return False

    def validate_path(self, path: str) -> str:
        rel = self._resolve_relative(path)
        if rel is None:
            raise ScopeViolation(path, "Path escapes worktree root or targets sensitive files")

        if self.allowed_paths:
            matched = False
            for allowed in self.allowed_paths:
                clean_allowed = allowed.rstrip("/")
                if rel == clean_allowed or rel.startswith(f"{clean_allowed}/"):
                    matched = True
                    break
            if not matched:
                raise ScopeViolation(
                    path,
                    f"Path '{rel}' is outside declared scope {self.allowed_paths}",
                )

        return rel

    def validate_batch(self, paths: Sequence[str]) -> list[str]:
        return [self.validate_path(p) for p in paths]
