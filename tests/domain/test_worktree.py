# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import pytest

from vibey.domain.worktree import branch_name, validate_item_id, worktree_subpath


def test_validate_item_id_accepts_lowercase_alphanumeric_and_hyphens() -> None:
    validate_item_id("item-014")
    validate_item_id("a")
    validate_item_id("skeleton")


@pytest.mark.parametrize("bad", ["", "Item-1", "item_1", "-item", "it/em", "a" * 65])
def test_validate_item_id_rejects_invalid_ids(bad: str) -> None:
    with pytest.raises(ValueError, match="invalid work item id"):
        validate_item_id(bad)


def test_worktree_subpath_is_deterministic_and_scoped_by_cycle() -> None:
    assert worktree_subpath(1, "item-1") == ".vibey/worktrees/1/item-1"
    assert worktree_subpath(2, "item-1") != worktree_subpath(1, "item-1")


def test_worktree_subpath_rejects_invalid_item_id() -> None:
    with pytest.raises(ValueError):
        worktree_subpath(1, "Bad Id")


def test_branch_name_is_deterministic_and_scoped_by_cycle() -> None:
    assert branch_name(1, "item-1") == "vibey/1/item-1"
    assert branch_name(2, "item-1") != branch_name(1, "item-1")


def test_branch_name_rejects_invalid_item_id() -> None:
    with pytest.raises(ValueError):
        branch_name(1, "Bad Id")
