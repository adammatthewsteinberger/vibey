"""Engine descriptors: data, not code paths (rotation-and-engines.md §2). A
fifth engine is a new descriptor plus an adapter, with no change to
domain/rotation.py.

The effort projections for claudeloop, codexloop, and cursorloop are
transcribed verbatim from rotation-and-engines.md §3, which states they are
built from reading the runners' sources. agyloop's doc entry ("same shape as
claudeloop with gemini aliases") conflicts with its own capability-matrix row
in §1, which lists no top-level `effort` command for agyloop -- only
`preset`. Since there is no `--effort` flag to combine with `--preset`, this
descriptor treats agyloop as preset-only and saturating at HIGH, the same
pattern verified for codexloop, rather than inventing two more preset tiers
the source table doesn't name. Flag this against the real binary in
conformance once agyloop is installed anywhere this runs.
"""

from vibey.domain.effort import Effort
from vibey.domain.engine import (
    Capability,
    EngineDescriptor,
    EngineId,
    EngineInvocation,
    IsolationLevel,
)

CLAUDELOOP = EngineDescriptor(
    engine_id=EngineId.CLAUDELOOP,
    binary="claudeloop",
    min_version="0.1.0",
    state_dir=".claudeloop",
    done_marker="CLAUDELOOP_TASK_FULLY_COMPLETE",
    auth_env=("ANTHROPIC_API_KEY",),
    capabilities=frozenset(
        {
            Capability.SAVEPOINTS,
            Capability.UNWIND,
            Capability.STRUCTURED_VERDICT,
            Capability.MID_RUN_PROMPT,
            Capability.MID_RUN_MODEL,
            Capability.MID_RUN_EFFORT,
            Capability.SLASH_COMMANDS,
            Capability.SNAPSHOT,
            Capability.SANDBOX,
        }
    ),
    effort_projection={
        Effort.TRIVIAL: EngineInvocation(
            ("--preset", "low", "--effort", "low"), achieved=Effort.TRIVIAL
        ),
        Effort.LOW: EngineInvocation(
            ("--preset", "low", "--effort", "medium"), achieved=Effort.LOW
        ),
        Effort.STANDARD: EngineInvocation(
            ("--preset", "medium", "--effort", "high"), achieved=Effort.STANDARD
        ),
        Effort.HIGH: EngineInvocation(
            ("--preset", "high", "--effort", "high"), achieved=Effort.HIGH
        ),
        Effort.MAX: EngineInvocation(("--preset", "high", "--effort", "max"), achieved=Effort.MAX),
    },
    session_verb="sessions",
    isolation_flags={
        IsolationLevel.WORKTREE: (),
        IsolationLevel.CONTAINER: ("--permission-mode", "container"),
        IsolationLevel.VM: ("--permission-mode", "vm"),
    },
    cost_per_mtok_in=3.0,
    cost_per_mtok_out=15.0,
    context_window=200_000,
    base_weight=3,
)

CODEXLOOP = EngineDescriptor(
    engine_id=EngineId.CODEXLOOP,
    binary="codexloop",
    min_version="0.1.0",
    state_dir=".codexloop",
    done_marker="CODEXLOOP_TASK_FULLY_COMPLETE",
    auth_env=("OPENAI_API_KEY",),
    capabilities=frozenset(
        {
            Capability.SAVEPOINTS,
            Capability.UNWIND,
            Capability.STRUCTURED_VERDICT,
            Capability.SNAPSHOT,
            Capability.SANDBOX,
        }
    ),
    effort_projection={
        Effort.TRIVIAL: EngineInvocation(("--effort", "low"), achieved=Effort.TRIVIAL),
        Effort.LOW: EngineInvocation(("--effort", "low"), achieved=Effort.LOW),
        Effort.STANDARD: EngineInvocation(("--effort", "medium"), achieved=Effort.STANDARD),
        Effort.HIGH: EngineInvocation(("--effort", "high"), achieved=Effort.HIGH),
        Effort.MAX: EngineInvocation(
            ("--effort", "high"), achieved=Effort.HIGH, notes="saturates: no tier above high"
        ),
    },
    session_verb="threads",
    isolation_flags={
        IsolationLevel.WORKTREE: (),
        IsolationLevel.CONTAINER: ("--sandbox", "container", "--approval", "never"),
        IsolationLevel.VM: ("--sandbox", "vm", "--approval", "never"),
    },
    cost_per_mtok_in=2.0,
    cost_per_mtok_out=8.0,
    context_window=200_000,
    base_weight=2,
)

CURSORLOOP = EngineDescriptor(
    engine_id=EngineId.CURSORLOOP,
    binary="cursorloop",
    min_version="0.1.0",
    state_dir=".cursorloop",
    done_marker="CURSORLOOP_TASK_FULLY_COMPLETE",
    auth_env=("CURSOR_API_KEY",),
    capabilities=frozenset(
        {
            Capability.SAVEPOINTS,
            Capability.UNWIND,
            Capability.SNAPSHOT,
            Capability.SANDBOX,
        }
    ),
    effort_projection={
        Effort.TRIVIAL: EngineInvocation(("--model", "composer-fast"), achieved=Effort.TRIVIAL),
        Effort.LOW: EngineInvocation(("--model", "composer"), achieved=Effort.LOW),
        Effort.STANDARD: EngineInvocation(("--model", "grok-4.5"), achieved=Effort.STANDARD),
        Effort.HIGH: EngineInvocation(("--model", "grok"), achieved=Effort.HIGH),
        Effort.MAX: EngineInvocation(("--model", "grok-xhigh"), achieved=Effort.MAX),
    },
    session_verb="agents",
    isolation_flags={
        IsolationLevel.WORKTREE: (),
        IsolationLevel.CONTAINER: ("--hooks-policy", "container"),
        IsolationLevel.VM: ("--hooks-policy", "vm"),
    },
    cost_per_mtok_in=2.5,
    cost_per_mtok_out=10.0,
    context_window=128_000,
    base_weight=2,
)

AGYLOOP = EngineDescriptor(
    engine_id=EngineId.AGYLOOP,
    binary="agyloop",
    min_version="0.1.0",
    state_dir=".agyloop",
    done_marker="AGYLOOP_TASK_FULLY_COMPLETE",
    auth_env=("GOOGLE_API_KEY",),
    capabilities=frozenset(
        {
            Capability.UNWIND,
            Capability.STRUCTURED_VERDICT,
            Capability.WEB_SEARCH,
            Capability.SNAPSHOT,
        }
    ),
    effort_projection={
        Effort.TRIVIAL: EngineInvocation(("--preset", "low"), achieved=Effort.TRIVIAL),
        Effort.LOW: EngineInvocation(("--preset", "low"), achieved=Effort.LOW),
        Effort.STANDARD: EngineInvocation(("--preset", "medium"), achieved=Effort.STANDARD),
        Effort.HIGH: EngineInvocation(("--preset", "high"), achieved=Effort.HIGH),
        Effort.MAX: EngineInvocation(
            ("--preset", "high"), achieved=Effort.HIGH, notes="saturates: no tier above high"
        ),
    },
    session_verb="sessions",
    isolation_flags={
        IsolationLevel.WORKTREE: (),
        IsolationLevel.CONTAINER: ("--safe",),
        IsolationLevel.VM: ("--safe",),
    },
    cost_per_mtok_in=0.5,
    cost_per_mtok_out=2.0,
    context_window=1_000_000,
    base_weight=1,
)

ALL_DESCRIPTORS: tuple[EngineDescriptor, ...] = (CLAUDELOOP, CODEXLOOP, CURSORLOOP, AGYLOOP)

BY_ENGINE_ID: dict[EngineId, EngineDescriptor] = {d.engine_id: d for d in ALL_DESCRIPTORS}
