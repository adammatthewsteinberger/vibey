# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from vibey.domain.scope_guard import MutationScope, ScopeViolation


def test_scope_guard_blocks_path_traversal() -> None:
    root = "/workspace/project"
    scope = MutationScope(
        worktree_root=root,
        allowed_paths=["src/", "tests/"],
    )

    traversals = [
        "../../etc/passwd",
        "../sibling.py",
        "/etc/shadow",
        "/workspace/project/../../secret.txt",
        "",
        "/workspace/other/file.py",
    ]
    for p in traversals:
        assert scope.is_path_allowed(p) is False
        with pytest.raises(ScopeViolation):
            scope.validate_path(p)


def test_scope_guard_blocks_sensitive_files() -> None:
    root = "/workspace/project"
    scope = MutationScope(
        worktree_root=root,
        allowed_paths=["."],
    )

    sensitive = [
        ".git/config",
        ".git/HEAD",
        ".env",
        ".env.local",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "secrets.json",
        "nested/../.env",
        "/workspace/project/.env",
    ]
    for s in sensitive:
        assert scope.is_path_allowed(s) is False
        with pytest.raises(ScopeViolation):
            scope.validate_path(s)


def test_scope_guard_enforces_declared_paths() -> None:
    root = "/workspace/project"
    scope = MutationScope(
        worktree_root=root,
        allowed_paths=["src/vibey/domain/", "tests/domain/"],
    )

    # Allowed paths
    assert scope.is_path_allowed("src/vibey/domain/item.py") is True
    assert scope.is_path_allowed("tests/domain/test_item.py") is True
    assert scope.is_path_allowed("/workspace/project/src/vibey/domain/item.py") is True
    rel = scope.validate_path("src/vibey/domain/item.py")
    assert rel == "src/vibey/domain/item.py"

    # Disallowed paths (outside declared scope)
    disallowed = [
        "src/vibey/infrastructure/db.py",
        "docs/roadmap.md",
        "package.json",
    ]
    for d in disallowed:
        assert scope.is_path_allowed(d) is False
        with pytest.raises(ScopeViolation):
            scope.validate_path(d)


def test_scope_guard_batch_validation_and_open_scope() -> None:
    root = "/workspace/project"
    scope = MutationScope(
        worktree_root=root,
        allowed_paths=["src/"],
    )

    valid_batch = ["src/a.py", "src/b/c.py"]
    validated = scope.validate_batch(valid_batch)
    assert len(validated) == 2
    assert validated[0] == "src/a.py"

    invalid_batch = ["src/a.py", "docs/b.md"]
    with pytest.raises(ScopeViolation):
        scope.validate_batch(invalid_batch)

    # Open scope (no allowed_paths filter)
    open_scope = MutationScope(worktree_root=root)
    assert open_scope.is_path_allowed("any/valid/path.py") is True
    assert open_scope.validate_path("any/valid/path.py") == "any/valid/path.py"
