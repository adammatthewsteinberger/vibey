# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.provision import (
    BEGIN_MARKER,
    END_MARKER,
    ProvisionSpec,
    RouterFile,
    content_digest,
    merge_router,
    needs_write,
    render_block,
)


def spec() -> ProvisionSpec:
    return ProvisionSpec(
        non_negotiables=("no secrets in the repo", "tests before code"),
        plugins=("software-architecture", "quality-engineering"),
    )


def test_router_file_names_match_adr_0011() -> None:
    assert {member.value for member in RouterFile} == {
        "CLAUDE.md",
        "AGENTS.md",
        "CURSOR.md",
        "GEMINI.md",
        "QWEN.md",
    }


def test_render_block_contains_markers_and_content() -> None:
    block = render_block(spec())
    assert block.startswith(BEGIN_MARKER)
    assert block.rstrip().endswith(END_MARKER)
    assert "no secrets in the repo" in block
    assert "software-architecture" in block


def test_render_block_handles_empty_non_negotiables_and_plugins() -> None:
    block = render_block(ProvisionSpec((), ()))
    assert "- None" in block
    assert "none" in block


def test_merge_router_with_no_existing_content_returns_the_block_verbatim() -> None:
    block = render_block(spec())
    assert merge_router(None, block) == block
    assert merge_router("", block) == block


def test_merge_router_appends_block_to_unmarked_hand_written_content() -> None:
    block = render_block(spec())
    existing = "# My project\n\nSome hand-written notes.\n"
    merged = merge_router(existing, block)
    assert merged.startswith(existing)
    assert block in merged


def test_merge_router_replaces_only_the_vibey_span_and_preserves_the_rest() -> None:
    old_block = render_block(ProvisionSpec(("old rule",), ()))
    existing = f"# Hand-written header\n\n{old_block}\n# Hand-written footer\n"
    new_block = render_block(spec())

    merged = merge_router(existing, new_block)

    assert "# Hand-written header" in merged
    assert "# Hand-written footer" in merged
    assert "old rule" not in merged
    assert "no secrets in the repo" in merged


def test_content_digest_is_deterministic_and_sensitive_to_content() -> None:
    assert content_digest("a") == content_digest("a")
    assert content_digest("a") != content_digest("b")


def test_needs_write_true_when_no_existing_file() -> None:
    assert needs_write(None, render_block(spec())) is True


def test_needs_write_false_when_content_is_already_correct() -> None:
    rendered = render_block(spec())
    assert needs_write(rendered, rendered) is False


def test_needs_write_true_when_content_differs() -> None:
    rendered = render_block(spec())
    other = render_block(ProvisionSpec(("different",), ()))
    assert needs_write(other, rendered) is True


def test_merge_router_round_trips_to_an_identical_string() -> None:
    """The property re-provisioning idempotence depends on: merging a
    block into content that's already exactly that block must reproduce
    the same string byte for byte, or needs_write() will never see a
    match and re-provisioning an unchanged worktree will never be a
    no-op."""
    block = render_block(spec())
    assert merge_router(block, block) == block
    assert needs_write(block, merge_router(block, block)) is False


def test_merge_router_handles_tail_without_leading_newline() -> None:
    """When the tail after END_MARKER doesn't start with a newline,
    the tail is preserved as-is without stripping."""
    existing = f"prefix\n{BEGIN_MARKER}\nold\n{END_MARKER}Tail without newline"

    new_block = render_block(spec())
    merged = merge_router(existing, new_block)

    assert "Tail without newline" in merged
    assert "no secrets in the repo" in merged
