from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from vibey.domain.effort import Effort

# The *loop runners' shared "graceful wind-down" exit code: the engine ran
# out of window capacity mid-item and stopped cleanly after writing its
# state, so the item hands off to another engine instead of failing
# (handoff-protocol.md §3). A domain constant because the meaning belongs
# to the protocol, not to any one subprocess adapter.
EXIT_CODE_WIND_DOWN = 75


class EngineId(StrEnum):
    CLAUDELOOP = "claudeloop"
    CODEXLOOP = "codexloop"
    CURSORLOOP = "cursorloop"
    AGYLOOP = "agyloop"


class Capability(StrEnum):
    SAVEPOINTS = "savepoints"
    UNWIND = "unwind"
    STRUCTURED_VERDICT = "structured_verdict"
    MID_RUN_PROMPT = "mid_run_prompt"
    MID_RUN_MODEL = "mid_run_model"
    MID_RUN_EFFORT = "mid_run_effort"
    ATTACHMENTS = "attachments"
    SLASH_COMMANDS = "slash_commands"
    WEB_SEARCH = "web_search"
    SNAPSHOT = "snapshot"
    SANDBOX = "sandbox"


class IsolationLevel(StrEnum):
    WORKTREE = "worktree"
    CONTAINER = "container"
    VM = "vm"


@dataclass(frozen=True, slots=True)
class EngineInvocation:
    argv: tuple[str, ...]
    achieved: Effort
    notes: str = ""


@dataclass(frozen=True, slots=True)
class EngineDescriptor:
    engine_id: EngineId
    binary: str
    min_version: str
    state_dir: str
    done_marker: str
    auth_env: tuple[str, ...]
    capabilities: frozenset[Capability]
    effort_projection: Mapping[Effort, EngineInvocation]
    session_verb: str
    isolation_flags: Mapping[IsolationLevel, tuple[str, ...]]
    cost_per_mtok_in: float
    cost_per_mtok_out: float
    context_window: int
    base_weight: int = 1
    # Whether the engine's own `run`/`resume` CLI accepts a `--cwd` flag.
    # False for an engine that doesn't have it yet (verified against the
    # real installed binary, not assumed) -- build_argv() must not append a
    # flag the binary would reject at argument parsing, before it ever gets
    # a chance to run.
    supports_cwd_flag: bool = True
    # How the engine's `run` verb takes the plan file. None means a bare
    # positional path (claudeloop, codexloop, agyloop); a string is the flag
    # the binary requires instead (cursorloop: `--plan`). Verified against
    # each installed binary's own --help, never assumed -- passing a
    # positional to a binary that wants a flag fails at argument parsing,
    # before the session ever starts.
    plan_flag: str | None = None

    def invoke(self, effort: Effort) -> EngineInvocation:
        try:
            return self.effort_projection[effort]
        except KeyError:
            # Fall back to the highest projection at or below the requested
            # effort -- the descriptor's own saturation point.
            candidates = sorted((e for e in self.effort_projection if e <= effort), reverse=True)
            if not candidates:
                raise
            return self.effort_projection[candidates[0]]

    def saturates_at(self, effort: Effort) -> bool:
        return self.invoke(effort).achieved < effort


@dataclass(frozen=True, slots=True)
class JobRequirement:
    effort: Effort
    capabilities: frozenset[Capability] = frozenset()
    excluded: frozenset[EngineId] = frozenset()  # the "must differ" constraint
