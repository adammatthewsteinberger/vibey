# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/api/binder.py — Click command tree builder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import click
from click.testing import CliRunner

from claudeloop.infrastructure.api.binder import (
    _ensure_group,
    _make_click_command,
    build_api_click_group,
)


class TestEnsureGroup:
    def test_creates_new_group(self) -> None:
        parent = click.Group("root")
        child = _ensure_group(parent, "child")
        assert isinstance(child, click.Group)
        assert parent.commands["child"] is child

    def test_reuses_existing_group(self) -> None:
        parent = click.Group("root")
        first = _ensure_group(parent, "child")
        second = _ensure_group(parent, "child")
        assert first is second

    def test_replaces_non_group_command(self) -> None:
        parent = click.Group("root")
        parent.add_command(click.Command("child", callback=lambda: None), "child")
        group = _ensure_group(parent, "child")
        assert isinstance(group, click.Group)


class TestMakeClickCommand:
    def test_creates_command_with_params(self) -> None:
        method = MagicMock()
        method.path = "messages.create"
        method.method_name = "create"
        method.chain = ["messages"]

        gateway = MagicMock()

        # _make_click_command imports resolve_callable locally from introspect
        # (avoids a module-level import cycle), so the patch target is where
        # it's defined, not where binder.py happens to call it.
        with patch("claudeloop.infrastructure.api.introspect.resolve_callable") as mock_resolve:

            def dummy_fn(*, model: str = "claude-sonnet") -> None:
                pass

            mock_resolve.return_value = dummy_fn
            cmd = _make_click_command(method, gateway)

        assert isinstance(cmd, click.Command)
        assert cmd.name == "create"
        param_names = [p.name for p in cmd.params]
        assert "json" in param_names
        assert "json_file" in param_names
        assert "raw" in param_names
        assert "stream" in param_names
        assert "max_items" in param_names


class TestBuildApiClickGroup:
    def test_builds_group_with_commands(self) -> None:
        gateway = MagicMock()
        group = build_api_click_group(gateway=gateway)
        assert isinstance(group, click.Group)

    def test_help_output(self) -> None:
        gateway = MagicMock()
        group = build_api_click_group(gateway=gateway)
        runner = CliRunner()
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert "api" in result.output.lower() or "SDK" in result.output

    def test_unknown_provider_raises(self) -> None:
        gateway = MagicMock()
        group = build_api_click_group(gateway=gateway)
        runner = CliRunner()
        result = runner.invoke(group, ["--provider", "nonexistent", "messages"])
        assert result.exit_code != 0
        assert "unknown provider" in result.output


class TestCallbackDirect:
    """Exercise the callback's root-walk when there is no parent context."""

    @staticmethod
    def _build_command(gateway: MagicMock) -> click.Command:
        method = MagicMock()
        method.path = "messages.create"
        method.method_name = "create"
        method.chain = ["messages"]
        with patch("claudeloop.infrastructure.api.introspect.resolve_callable") as mock_resolve:

            def dummy_fn() -> None:
                pass

            mock_resolve.return_value = dummy_fn
            return _make_click_command(method, gateway)

    def test_missing_root_obj_defaults_to_first_party(self) -> None:
        gateway = MagicMock()
        gateway.invoke_and_print.return_value = "direct-ok"
        cmd = self._build_command(gateway)

        runner = CliRunner()
        result = runner.invoke(cmd, [])

        assert result.exit_code == 0
        assert "direct-ok" in result.output
        kwargs = gateway.invoke_and_print.call_args.kwargs
        assert kwargs["provider"] == "first-party"


class TestCallbackViaFullGroup:
    """Exercise the callback through the real generated command tree."""

    @staticmethod
    def _build_group() -> tuple[click.Group, MagicMock]:
        gateway = MagicMock()
        group = build_api_click_group(gateway=gateway)
        return group, gateway

    def test_success_prints_result_with_default_provider(self) -> None:
        group, gateway = self._build_group()
        gateway.invoke_and_print.return_value = "hello output"
        runner = CliRunner()

        result = runner.invoke(group, ["messages", "create", "--json", "{}"])

        assert result.exit_code == 0
        assert "hello output" in result.output
        kwargs = gateway.invoke_and_print.call_args.kwargs
        assert kwargs["provider"] == "first-party"
        assert kwargs["json_body"] == "{}"
        assert kwargs["raw"] is False
        assert kwargs["stream"] is False
        assert kwargs["max_items"] is None

    def test_provider_propagates_through_nested_groups(self) -> None:
        group, gateway = self._build_group()
        gateway.invoke_and_print.return_value = "ok"
        runner = CliRunner()

        # beta.agents.create is nested two levels deep, exercising the
        # multi-hop ctx.parent walk up to the root context.
        result = runner.invoke(group, ["--provider", "aws", "beta", "agents", "create"])

        assert result.exit_code == 0
        kwargs = gateway.invoke_and_print.call_args.kwargs
        assert kwargs["provider"] == "aws"

    def test_value_error_becomes_click_exception(self) -> None:
        group, gateway = self._build_group()
        gateway.invoke_and_print.side_effect = ValueError("bad value")
        runner = CliRunner()

        result = runner.invoke(group, ["messages", "create"])

        assert result.exit_code != 0
        assert "bad value" in result.output

    def test_type_error_becomes_click_exception(self) -> None:
        group, gateway = self._build_group()
        gateway.invoke_and_print.side_effect = TypeError("bad type")
        runner = CliRunner()

        result = runner.invoke(group, ["messages", "create"])

        assert result.exit_code != 0
        assert "bad type" in result.output

    def test_os_error_becomes_click_exception(self) -> None:
        group, gateway = self._build_group()
        gateway.invoke_and_print.side_effect = OSError("disk full")
        runner = CliRunner()

        result = runner.invoke(group, ["messages", "create"])

        assert result.exit_code != 0
        assert "disk full" in result.output
