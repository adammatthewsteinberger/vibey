# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""HITL / ask_question is denied with guidance, never auto-answered."""

from __future__ import annotations

import inspect

from google.antigravity.connections.local.event_processor import LocalHarnessEventProcessor
from google.antigravity.hooks.hook_runner import HookRunner
from google.antigravity.hooks.hooks import HookContext, OnInteractionHook
from google.antigravity.proto import localharness_pb2
from google.antigravity.types import BuiltinTools, ToolCall
from google.antigravity.utils.interactive import AskQuestionHook, ToolConfirmationHook

from agyloop.infrastructure.agent.autonomy import (
    ASK_QUESTION_DENY_MESSAGE,
    DenyAskQuestionHook,
    DenyAskQuestionInteractionHook,
    autonomy_hooks,
)
from agyloop.infrastructure.agent.options import build_local_config


def test_strict_autonomy_keeps_deny_with_guidance() -> None:
    cfg = build_local_config(cwd=".", strict_autonomy=True)
    assert BuiltinTools.ASK_QUESTION in (cfg.capabilities.disabled_tools or [])
    assert any(isinstance(hook, DenyAskQuestionHook) for hook in cfg.hooks)
    assert any(isinstance(hook, DenyAskQuestionInteractionHook) for hook in cfg.hooks)


async def test_ask_question_denied_with_guidance() -> None:
    hook = DenyAskQuestionHook()
    result = await hook.run(HookContext(), ToolCall(name=BuiltinTools.ASK_QUESTION, args={}))
    assert result.allow is False
    assert result.message == ASK_QUESTION_DENY_MESSAGE
    assert "no human is available" in result.message
    assert "Do not call `ask_question` again" in result.message


async def test_ask_question_deny_does_not_block_other_tools() -> None:
    hook = DenyAskQuestionHook()
    result = await hook.run(
        HookContext(), ToolCall(name=BuiltinTools.VIEW_FILE, args={"path": "a.py"})
    )
    assert result.allow is True


def test_ask_question_handler_is_synchronous() -> None:
    """Hook bodies must not await a human; SDK run() is async but we don't wait."""
    for hook in autonomy_hooks():
        source = inspect.getsource(type(hook).run)
        assert "input(" not in source
        assert "async_input" not in source
        assert "sleep(" not in source


async def test_questions_request_carries_deny_guidance() -> None:
    """Live HITL path: questions_request → OnInteractionHook, not unanswered."""
    cfg = build_local_config(cwd=".")
    for hook in cfg.hooks:
        assert not isinstance(hook, (ToolConfirmationHook, AskQuestionHook))
    assert any(isinstance(hook, OnInteractionHook) for hook in cfg.hooks)

    runner = HookRunner()
    for hook in cfg.hooks:
        runner.register_hook(hook)

    sent: list[localharness_pb2.InputEvent] = []

    async def capture(event: localharness_pb2.InputEvent) -> None:
        sent.append(event)

    processor = LocalHarnessEventProcessor(
        send_input_event_fn=capture,
        hook_runner=runner,
    )
    step_update = localharness_pb2.StepUpdate(
        step_index=1,
        trajectory_id="traj",
        state=localharness_pb2.StepUpdate.STATE_WAITING_FOR_USER,
        questions_request=localharness_pb2.UserQuestionsRequest(
            questions=[
                localharness_pb2.UserQuestion(
                    multiple_choice=localharness_pb2.MultipleChoice(
                        question="Which option?",
                        choices=["A", "B"],
                    )
                )
            ]
        ),
    )
    await processor.handle_question_request(step_update)

    assert sent, "questions_request must produce a question_response"
    answers = sent[0].question_response.response.answers
    assert len(answers) == 1
    answer = answers[0]
    assert not answer.unanswered
    assert answer.multiple_choice_answer.freeform_response == ASK_QUESTION_DENY_MESSAGE
    assert list(answer.multiple_choice_answer.selected_choice_indices) == []


def test_tool_name_and_command_line_helpers() -> None:
    from unittest.mock import MagicMock

    from agyloop.infrastructure.agent.autonomy import (
        _command_line_from_args,
        _is_destructive_command,
        _tool_name,
        build_autonomy_policies,
    )

    # Plain string name
    data = MagicMock()
    data.name = "custom_tool"
    assert _tool_name(data) == "custom_tool"

    # Command line variations
    assert _command_line_from_args({"CommandLine": "rm -rf /"}) == "rm -rf /"
    assert _command_line_from_args({"command": "git clean -fdx"}) == "git clean -fdx"
    assert _command_line_from_args({"other": 123}) == ""

    # Destructive commands detection
    assert _is_destructive_command({"CommandLine": "rm -rf /"}) is True
    assert _is_destructive_command({"CommandLine": "git status"}) is False

    # build_autonomy_policies yolo mode
    yolo_policies = build_autonomy_policies(cwd=".", permission_mode="yolo")
    assert len(yolo_policies) == 1
