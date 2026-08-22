# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""A git-invoking subprocess executor that strips GIT_* environment
variables, shared by every module in infrastructure/git/ and infrastructure/
provision/ that shells out to `git`.

A caller running inside a git hook (pre-commit, itself invoked from `git
commit`) has GIT_DIR/GIT_INDEX_FILE/GIT_WORK_TREE etc. set in its own
environment, pointing at *that* repository's plumbing. Subprocesses inherit
the parent environment by default, so an unfiltered `git -C <other repo>
...` call silently operates against the wrong repository instead of the one
`-C` names -- GIT_DIR overrides discovery outright. This bit
GitWorktreeManager during development (caught by running its tests through
the actual pre-commit hook); every other git-shelling module uses this same
executor from the start rather than rediscovering the bug.
"""

import asyncio
import os

from vibey.infrastructure.engines.claudeloop_process import CommandResult


class CleanGitEnvSubprocessExecutor:
    async def execute(self, argv: tuple[str, ...]) -> CommandResult:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await process.communicate()
        except asyncio.CancelledError:
            process.terminate()
            await process.wait()
            raise
        return CommandResult(process.returncode or 0, stdout.decode(), stderr.decode())
