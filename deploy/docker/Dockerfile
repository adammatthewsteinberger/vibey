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

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependency layer first: the lockfile changes far less often than source,
# so this caches across almost every rebuild.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY migrations/ ./migrations/
RUN uv sync --frozen --no-dev


FROM python:3.12-slim-bookworm AS runtime

# git is a genuine runtime dependency, not a build-time one: BUILD phase
# work happens in real git worktrees the worker creates itself.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
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
ENTRYPOINT ["vibey"]
CMD ["--help"]
