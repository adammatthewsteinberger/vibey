# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Throwaway capacity probe: cheapest ``chat()``, no ``conversation_id`` (F12).

A rejected probe may still consume RPD, so the runner counts it in the budget
ledger. ``--no-probe`` skips this adapter entirely.
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import (
    AntigravityCancelledError,
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
    BuiltinTools,
    CapabilitiesConfig,
    ChatResponse,
)

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.autonomy import autonomy_hooks, build_autonomy_policies
from agyloop.infrastructure.agent.harness_logs import (
    capture_harness_logs,
    raise_if_empty_withdrawn,
)
from agyloop.infrastructure.agent.harness_retarget import (
    input_detection_env,
    input_detection_models,
    prepare_harness,
)
from agyloop.infrastructure.agent.translate import (
    outcome_from_exception,
    partial_text_from_response,
    verdict_from_structured,
)

PROBE_PROMPT = "Reply with the single word OK and nothing else."

_HARNESS_DIAGNOSIS = (
    "the local Antigravity harness failed to start. This is a harness problem, "
    "not a capacity problem.\n"
    "  - Run `agyloop doctor` to check harness viability before retrying.\n"
    "  - Re-run with `--gateway cli` to avoid the SDK harness entirely.\n"
    "  - Or `--no-probe` to skip the preflight probe (not recommended).\n"
    "  - Or `agyloop doctor --repair-harness` to restore the stock binary.\n"
    "  - Override the binary with ANTIGRAVITY_HARNESS_PATH, or clear the patched\n"
    "    copy cache at AGYLOOP_HARNESS_CACHE (default ~/.cache/agyloop/localharness).\n"
    "  See docs/contributing/harness-patch.md."
)


def harness_startup_error(exc: BaseException) -> AgentConfigError:
    """Diagnose a harness startup failure instead of surfacing a bare
    ``RuntimeError: Failed to read length from stdout`` traceback."""
    return AgentConfigError(f"{_HARNESS_DIAGNOSIS}\n  Underlying error: {exc}")


def build_probe_config(
    *,
    cwd: str,
    model: str | None = None,
    api_key: str | None = None,
) -> LocalAgentConfig:
    workspace = str(Path(cwd).resolve())
    extra_models = input_detection_models(chat_model=model, api_key=api_key)
    return LocalAgentConfig(
        system_instructions=PROBE_PROMPT,
        capabilities=CapabilitiesConfig(enabled_tools=BuiltinTools.none()),
        policies=build_autonomy_policies(cwd=workspace, permission_mode="autonomous"),
        hooks=autonomy_hooks(),
        workspaces=[workspace],
        conversation_id=None,
        model=None,
        models=extra_models if model else None,
        env=input_detection_env(),
        api_key=api_key,
        mcp_servers=[],
    )


class AntigravityCapacityProbe:
    """One-shot throwaway Agent used only to re-check capacity."""

    def __init__(
        self,
        *,
        cwd: str,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._cwd = cwd
        self._model = model
        self._api_key = api_key

    def set_model(self, model: str | None) -> None:
        self._model = model

    async def probe(self) -> TurnOutcome:
        prepare_harness()
        agent = Agent(build_probe_config(cwd=self._cwd, model=self._model, api_key=self._api_key))
        response: ChatResponse | None = None
        try:
            # __aenter__ spawns the local harness subprocess and can fail before
            # any session exists. It must be inside the try so the finally below
            # reaps the orphaned Popen -- otherwise a harness that dies without
            # writing its length header leaks a process and escapes undiagnosed.
            session = await agent.__aenter__()
            with capture_harness_logs() as logs:
                response = await session.chat(PROBE_PROMPT)
                output_text = await response.text()
            structured = await response.structured_output()
            raise_if_empty_withdrawn(output_text=output_text, logs=logs)
            return TurnOutcome(
                signals=TurnSignals(),
                verdict=verdict_from_structured(structured),
                output_text=output_text,
                session_id=None,
            )
        except AntigravityValidationError as exc:
            raise AgentConfigError(str(exc)) from exc
        except (
            AntigravityCancelledError,
            AntigravityExecutionError,
            AntigravityConnectionError,
        ) as exc:
            partial = partial_text_from_response(response) if response is not None else ""
            return outcome_from_exception(exc, output_text=partial, session_id=None)
        except (RuntimeError, OSError) as exc:
            # The SDK raises a bare RuntimeError when the harness subprocess exits
            # without writing its 4-byte length header. Fail closed with a
            # diagnosis rather than a raw traceback out of typer.
            raise harness_startup_error(exc) from exc
        finally:
            # A harness that never started cannot be shut down cleanly; the
            # startup error above is the one worth reporting.
            with suppress(RuntimeError, OSError):
                await agent.__aexit__(None, None, None)
