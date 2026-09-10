# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Managed llama.cpp/vLLM OpenAI-compatible server adapters."""

import asyncio
import fcntl
import json
import os
import re
import signal
import socket
import urllib.error
import urllib.request
from collections.abc import AsyncIterator, Sequence
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from typing import IO

from platformdirs import user_cache_path

from qwenloop.domain.model import Backend, ChatChunk, ChatMessage, ModelProfile, ServerInfo


class OpenAIServer:
    binary: str
    backend: Backend

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or user_cache_path("qwenloop")

    def inspect(self, profile: ModelProfile) -> ServerInfo | None:
        state = self.cache_dir / "servers" / f"{profile.name}.json"
        if not state.is_file():
            return None
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            return ServerInfo(
                backend=Backend(data["backend"]),
                profile=str(data["profile"]),
                endpoint=str(data["endpoint"]),
                owned=bool(data["owned"]),
                healthy=False,
                pid=int(data["pid"]),
                token=str(data.get("token", "")),
            )
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return None

    async def install(self, profile: ModelProfile) -> Path:
        raise RuntimeError(
            "model installation is explicit but network transfer is delegated to the runtime; "
            f"install {profile.repository}@{profile.revision} ({profile.filename or 'safetensors'})"
        )

    async def start(self, profile: ModelProfile) -> ServerInfo:
        lock = await asyncio.to_thread(_acquire_profile_lock, self.cache_dir, profile.name)
        try:
            existing = self.inspect(profile)
            if existing is not None and existing.pid is not None and _pid_alive(existing.pid):
                return existing
            port = _free_port()
            token = os.urandom(24).hex()
            argv = self._argv(profile, port, token)
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
            info = ServerInfo(
                backend=self.backend,
                profile=profile.name,
                endpoint=f"http://127.0.0.1:{port}/v1",
                owned=True,
                healthy=False,
                pid=process.pid,
                token=token,
            )
            state = self.cache_dir / "servers" / f"{profile.name}.json"
            state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            state.write_text(
                json.dumps({**asdict(info), "backend": info.backend.value}),
                encoding="utf-8",
            )
            return info
        finally:
            await asyncio.to_thread(_release_profile_lock, lock)

    async def health(self, info: ServerInfo) -> bool:
        request = urllib.request.Request(
            f"{info.endpoint}/models", headers={"Authorization": f"Bearer {info.token}"}
        )
        try:
            response = await asyncio.to_thread(urllib.request.urlopen, request, timeout=2)
            return bool(response.status == 200)
        except (OSError, urllib.error.URLError):
            return False

    async def chat_stream(
        self, info: ServerInfo, messages: Sequence[ChatMessage]
    ) -> AsyncIterator[ChatChunk]:
        payload = json.dumps(
            {
                "model": info.profile,
                "messages": [{"role": item.role, "content": item.content} for item in messages],
                "tools": _CODING_TOOLS,
                "tool_choice": "auto",
                "stream": False,
            }
        ).encode()
        request = urllib.request.Request(
            f"{info.endpoint}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {info.token}",
            },
        )
        try:
            response = await asyncio.to_thread(urllib.request.urlopen, request, timeout=300)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(_http_error_detail(exc)) from exc
        data = json.loads(response.read())
        message = data["choices"][0]["message"]
        calls = message.get("tool_calls", [])
        content = message.get("content") or ""
        if not calls:
            parsed, content = _parse_text_tool_calls(content)
            calls = [
                {"function": {"name": call["name"], "arguments": call["arguments"]}}
                for call in parsed
            ]
        for call in calls:
            function = call.get("function", {})
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            yield ChatChunk(tool_call={"name": function.get("name", ""), "arguments": arguments})
        usage = data.get("usage", {})
        yield ChatChunk(
            text=content,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
        )

    async def stop(self, info: ServerInfo) -> None:
        if not info.owned or info.pid is None:
            return
        try:
            os.killpg(info.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        else:
            for _ in range(100):
                if not _pid_alive(info.pid):
                    break
                await asyncio.sleep(0.1)
            else:
                with suppress(ProcessLookupError):
                    os.killpg(info.pid, signal.SIGKILL)
        state = self.cache_dir / "servers" / f"{info.profile}.json"
        current = self.inspect(
            ModelProfile(info.profile, info.backend, "", "", None, None, None, "")
        )
        if current is not None and current.pid == info.pid:
            state.unlink(missing_ok=True)

    def _argv(self, profile: ModelProfile, port: int, token: str) -> tuple[str, ...]:
        raise NotImplementedError


class LlamaCppServer(OpenAIServer):
    binary = "llama-server"
    backend = Backend.LLAMA_CPP

    def _argv(self, profile: ModelProfile, port: int, token: str) -> tuple[str, ...]:
        model = self.cache_dir / "models" / profile.name / str(profile.filename)
        if not model.is_file():
            raise FileNotFoundError(f"model is not installed: {model}")
        return (
            self.binary,
            "--model",
            str(model),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--ctx-size",
            str(profile.context_window),
            "--api-key",
            token,
            "--jinja",
        )


class VllmServer(OpenAIServer):
    binary = "vllm"
    backend = Backend.VLLM

    def _argv(self, profile: ModelProfile, port: int, token: str) -> tuple[str, ...]:
        return (
            self.binary,
            "serve",
            profile.repository,
            "--revision",
            profile.revision,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--api-key",
            token,
            "--enable-auto-tool-choice",
            "--tool-call-parser",
            "hermes",
            "--max-model-len",
            str(profile.context_window),
        )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _acquire_profile_lock(cache_dir: Path, profile: str) -> IO[str]:
    directory = cache_dir / "servers"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    stream = (directory / f"{profile}.lock").open("a+", encoding="utf-8")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    return stream


def _release_profile_lock(stream: IO[str]) -> None:
    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    stream.close()


def _http_error_detail(exc: urllib.error.HTTPError) -> str:
    """Surface the server's own error body instead of urllib's generic reason phrase."""
    try:
        body = exc.read()
    except OSError:
        return f"HTTP {exc.code}: {exc.reason}"
    message: str | None = None
    try:
        parsed = json.loads(body)
        message = parsed.get("error", {}).get("message")
    except (json.JSONDecodeError, AttributeError, TypeError):
        message = None
    if message:
        return f"HTTP {exc.code}: {message}"
    text = body.decode("utf-8", errors="replace").strip()
    return f"HTTP {exc.code}: {text or exc.reason}"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


_CODING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file inside the assigned worktree.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write UTF-8 text to a file inside the assigned worktree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shell",
            "description": "Run a bounded command in the assigned worktree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "argv": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["argv"],
                "additionalProperties": False,
            },
        },
    },
]


def _parse_text_tool_calls(text: str) -> tuple[list[dict[str, object]], str]:
    calls: list[dict[str, object]] = []
    pattern = re.compile(r"<(?:tools|tool_call)>\s*(\{.*?\})\s*</(?:tools|tool_call)>", re.DOTALL)
    for match in pattern.finditer(text):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict) or not isinstance(value.get("name"), str):
            continue
        arguments = value.get("arguments", {})
        calls.append(
            {
                "name": value["name"],
                "arguments": arguments if isinstance(arguments, dict) else {},
            }
        )
    return calls, pattern.sub("", text).strip() if calls else text
