# vibey worker/server image.
#
# Two stages so the runtime layer carries no build toolchain and no uv:
# a compromised engine session running inside a worker should not find a
# compiler or a package manager waiting for it. The base image's own pip
# is removed below for the same reason. CI asserts every part of this,
# because a property stated only in a comment is one careless refactor
# away from silently lapsing -- pip was in fact present until the check
# was written.
#
# Both stages use /app as WORKDIR deliberately. `uv sync` installs the
# project in editable mode, so the venv holds an absolute path back to
# the source tree; building under /src and copying to /app would leave
# that pointer dangling. Same path in both stages, no rewriting needed.
#
# Migrations ship in the image because the worker applies them at startup
# (bootstrap resolves them relative to its own file: /app/src/vibey/…
# -> /app/migrations), so a chart install never depends on someone
# running SQL by hand first.

FROM ghcr.io/astral-sh/uv:0.9-python3.12-bookworm-slim AS build

# The context-engine release is temporarily locked to an immutable Git commit
# until it has a newly versioned wheel. Git remains confined to this disposable
# build stage; only the resolved virtual environment is copied into runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependency layer first: the lockfile changes far less often than source,
# so this caches across almost every rebuild.
COPY pyproject.toml uv.lock README.md ./
# vibey-skills is a workspace member now, not a PyPI download, so uv has to be able to
# BUILD it in this layer -- without it the sync fails outright with "Distribution not
# found at: .../src/vibey_tools/skills". Only this one member is needed: the runners and
# the other tools are not dependencies of `vibey[operator,skills]`, so uv never looks for
# them. Copying the subtree whole rather than cherry-picking its manifest is deliberate;
# its wheel force-includes plugins/ and .claude-plugin/, and a narrower copy silently rots
# the moment that list grows.
COPY src/vibey_tools/skills/ ./src/vibey_tools/skills/
# --extra operator: the same image serves the worker and the operator
# Deployment, so kopf has to be present. --extra skills makes the optional
# context compiler available when a VibeyProject enables it; its process is
# never started for projects that leave the feature off.
RUN uv sync --frozen --no-install-project --no-dev --extra operator --extra skills

# src/vibey only. This was `COPY src/ ./src/`, which already shipped five runner subtrees
# into a runtime image that cannot execute them; with three tools absorbed as well it
# became roughly 160 MB of tests, docs and marketplace Markdown in the layer.
COPY src/vibey/ ./src/vibey/
COPY migrations/ ./migrations/
RUN uv sync --frozen --no-dev --extra operator --extra skills


FROM python:3.12-slim-bookworm AS runtime

# tini is here for one reason, and it is not tidiness. Linux discards a signal sent to
# PID 1 while its disposition is still SIG_DFL, so whatever runs as PID 1 must have its
# handlers installed before the orchestrator can possibly signal it. A Python process
# cannot meet that bar: interpreter start and imports take hundreds of milliseconds on a
# cold container, and measured on minikube a pod was deleted ~600ms after its container
# started -- inside that window. The signal was not delivered late, it was discarded, and
# the worker then sat out its full 7200s grace period claiming jobs nobody wanted.
#
# tini is ready in microseconds and forwards to the child, which turns an unwinnable race
# into an ordinary one: SIGTERM during boot terminates a worker that has claimed nothing,
# which is both correct and prompt; SIGTERM after boot is drained gracefully.
#
# Git is independently a genuine runtime dependency: BUILD phase work happens
# in real git worktrees the worker creates itself.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

# python:slim ships a system pip that this image never uses -- everything
# runs from /app/.venv, which uv built without one. Left in place it is
# the single package manager a compromised session could actually reach:
# uid 10001 owns a writable $HOME, so `pip install --user` would succeed.
# apt-get stays, since it installs git above, and is inert by comparison
# -- it needs root, and the chart runs the pod non-root with
# allowPrivilegeEscalation false.
RUN rm -rf /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.* \
           /usr/local/lib/python3.12/site-packages/pip \
           /usr/local/lib/python3.12/site-packages/pip-*.dist-info

# Non-root by default. The worktree volume is chowned to this uid in the
# chart; nothing in the image itself needs write access to /app.
RUN useradd --create-home --uid 10001 vibey

WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/migrations /app/migrations
COPY --from=build /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER vibey

# No default subcommand: the chart's worker and server Deployments supply
# their own args, and an image that silently starts a worker is a footgun
# when someone runs it just to inspect the filesystem.
# `-g` forwards to the whole process group, so an engine subprocess the worker started is
# signalled too rather than being orphaned onto init.
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "vibey"]
CMD ["--help"]
