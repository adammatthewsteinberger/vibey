# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Auth-lane resolution for ``agyloop doctor``. Never guesses Developer vs Enterprise."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - fixed-argument `agy --version` only
from collections.abc import Mapping
from pathlib import Path

from agyloop.application.interfaces import AuthResolution, HarnessStatus
from agyloop.infrastructure.agent.autonomy import autonomy_hooks
from agyloop.infrastructure.agent.harness_retarget import (
    cache_dir,
    smoke_check_harness,
    stock_harness_path,
)
from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.policies import config_has_nonblocking_policies

_INTERACTIVE_HOOK_NAMES = frozenset({"ToolConfirmationHook", "AskQuestionHook"})
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def developer_api_key(environ: Mapping[str, str]) -> tuple[str | None, str | None]:
    """Return ``(key, source)`` for the Developer API lane.

    ``GOOGLE_API_KEY`` wins when both are set (same lane, not a conflict).
    The Antigravity SDK validates ``LocalAgentConfig.api_key`` or
    ``GEMINI_API_KEY``; doctor and REST already used ``GOOGLE_API_KEY``.
    """
    google = (environ.get("GOOGLE_API_KEY") or "").strip()
    if google:
        return google, "GOOGLE_API_KEY"
    gemini = (environ.get("GEMINI_API_KEY") or "").strip()
    if gemini:
        return gemini, "GEMINI_API_KEY"
    return None, None


class RealDoctorEnvironment:
    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
    ) -> None:
        self._environ = environ if environ is not None else os.environ
        self._home = home if home is not None else Path.home()

    def resolve_auth(self) -> AuthResolution:
        api_key, key_source = developer_api_key(self._environ)
        vertex_flag: str | None = None
        if _truthy(self._environ.get("GOOGLE_GENAI_USE_VERTEXAI")):
            vertex_flag = "GOOGLE_GENAI_USE_VERTEXAI"
        elif _truthy(self._environ.get("GOOGLE_GENAI_USE_ENTERPRISE")):
            vertex_flag = "GOOGLE_GENAI_USE_ENTERPRISE"
        adc_source = self._adc_source()

        if api_key and vertex_flag:
            return AuthResolution(
                lane="unresolved",
                source="conflict",
                authenticated=False,
                detail=(
                    "GOOGLE_API_KEY/GEMINI_API_KEY and Vertex/Enterprise env "
                    "are both set; doctor will not guess the effective lane"
                ),
            )
        if vertex_flag is not None:
            source = vertex_flag if adc_source is None else f"{vertex_flag}+{adc_source}"
            authenticated = adc_source is not None
            detail = (
                f"Enterprise/Vertex lane via {source}"
                if authenticated
                else f"{vertex_flag} is set but ADC was not found"
            )
            return AuthResolution(
                lane="enterprise",
                source=source,
                authenticated=authenticated,
                detail=detail,
            )
        if api_key:
            source = key_source or "GOOGLE_API_KEY"
            return AuthResolution(
                lane="developer_api",
                source=source,
                authenticated=True,
                detail=f"Developer API via {source}",
            )
        if adc_source is not None:
            return AuthResolution(
                lane="unresolved",
                source=adc_source,
                authenticated=True,
                detail=(
                    "ADC present; set GOOGLE_API_KEY for Developer API or "
                    "GOOGLE_GENAI_USE_VERTEXAI for Enterprise — doctor will not guess"
                ),
            )
        return AuthResolution(
            lane="unresolved",
            source="none",
            authenticated=False,
            detail="no GOOGLE_API_KEY/GEMINI_API_KEY and no ADC",
        )

    def _adc_source(self) -> str | None:
        cred_path = self._environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and Path(cred_path).is_file():
            return "GOOGLE_APPLICATION_CREDENTIALS"
        well_known = self._well_known_adc_path()
        if well_known.is_file():
            return "ADC_WELL_KNOWN"
        return None

    def _well_known_adc_path(self) -> Path:
        cloudsdk = self._environ.get("CLOUDSDK_CONFIG")
        if cloudsdk:
            return Path(cloudsdk) / "application_default_credentials.json"
        return self._home / ".config" / "gcloud" / "application_default_credentials.json"

    def interactive_hooks_registered(self) -> bool:
        for hook in autonomy_hooks():
            if type(hook).__name__ in _INTERACTIVE_HOOK_NAMES:
                return True
            if "utils.interactive" in type(hook).__module__:
                return True
        config = build_local_config(cwd=".")
        return not config_has_nonblocking_policies(config)

    def find_agy_cli(self) -> str | None:
        return shutil.which("agy")

    def agy_cli_version(self, path: str) -> str | None:
        try:
            result = subprocess.run(  # nosec B603
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def configured_mcp_servers(self) -> list[str]:
        return []

    def check_sdk_harness(self) -> HarnessStatus:
        """Check SDK harness viability for --gateway sdk."""
        stock_path = stock_harness_path()
        if stock_path is None:
            return HarnessStatus(
                available=False,
                detail="google-antigravity not installed (SDK gateway not available)",
            )
        patched_path = cache_dir() / "localharness"
        if patched_path.exists():
            smoke_result = smoke_check_harness(patched_path, timeout=2.0)
            if smoke_result is None:
                return HarnessStatus(
                    available=True,
                    detail=f"patched harness at {patched_path} verified",
                )
            return HarnessStatus(
                available=False,
                detail=(
                    f"SDK harness issue: {smoke_result}. "
                    f"Use --gateway cli, or run `agyloop doctor repair-harness`. "
                    f"Patched binary at {patched_path}"
                ),
            )
        return HarnessStatus(
            available=True,
            detail=f"stock harness at {stock_path} (no patch needed yet)",
        )
