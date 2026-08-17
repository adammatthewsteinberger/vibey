"""descriptor + effort + isolation -> command line. The only place a
RunSpec's abstract intent becomes a concrete argv for a specific vendor
binary."""

from vibey.application.dto import RunSpec
from vibey.domain.engine import EngineDescriptor


def build_argv(descriptor: EngineDescriptor, spec: RunSpec) -> tuple[str, ...]:
    verb = "resume" if spec.session_id is not None else "run"

    argv: list[str] = [descriptor.binary, verb]
    if spec.session_id is not None:
        argv.append(spec.session_id)
    else:
        plan_path = spec.worktree_path / ".vibey" / "plans" / f"{spec.run_id}.md"
        argv.append(str(plan_path))
        argv.extend(["--run-id", str(spec.run_id)])

    argv.extend(descriptor.invoke(spec.effort).argv)
    argv.extend(descriptor.isolation_flags.get(spec.isolation, ()))
    argv.extend(["--cwd", str(spec.worktree_path)])

    return tuple(argv)
