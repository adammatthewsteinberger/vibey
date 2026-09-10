# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import io
import json
import urllib.error
from pathlib import Path

import pytest

from qwenloop.domain.model import Backend, ChatMessage, ServerInfo
from qwenloop.infrastructure.inference import (
    LlamaCppServer,
    OpenAIServer,
    VllmServer,
    _http_error_detail,
    _parse_text_tool_calls,
    _pid_alive,
)
from qwenloop.infrastructure.profiles import NVIDIA_BF16, PORTABLE


class UrlResponse(io.BytesIO):
    status = 200


@pytest.mark.asyncio
async def test_openai_health_and_chat(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": "done",
                    "tool_calls": [
                        {"function": {"name": "read_file", "arguments": '{"path":"x"}'}}
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 2, "completion_tokens": 1},
    }

    def urlopen(request, timeout):  # type: ignore[no-untyped-def]
        del timeout
        if request.full_url.endswith("/models"):
            return UrlResponse(b"{}")
        body = json.loads(request.data)
        assert body["tool_choice"] == "auto"
        assert {tool["function"]["name"] for tool in body["tools"]} == {
            "read_file",
            "write_file",
            "shell",
        }
        return UrlResponse(json.dumps(payload).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    server = LlamaCppServer(tmp_path)
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://local/v1", True, True, 1, "t")
    assert await server.health(info)
    chunks = [chunk async for chunk in server.chat_stream(info, [ChatMessage("user", "x")])]
    assert chunks[0].tool_call == {"name": "read_file", "arguments": {"path": "x"}}
    assert chunks[1].text == "done"


@pytest.mark.asyncio
async def test_chat_stream_surfaces_context_overflow_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = json.dumps(
        {
            "error": {
                "message": "request (20030 tokens) exceeds the available context size (4096 tokens)",
            }
        }
    ).encode()

    def urlopen(request, timeout):  # type: ignore[no-untyped-def]
        del timeout
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(body))

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    server = LlamaCppServer(tmp_path)
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://local/v1", True, True, 1, "t")
    with pytest.raises(RuntimeError, match="exceeds the available context size"):
        async for _ in server.chat_stream(info, [ChatMessage("user", "x")]):
            pass


def test_http_error_detail_prefers_json_error_message() -> None:
    exc = urllib.error.HTTPError(
        "u", 400, "Bad Request", {}, io.BytesIO(json.dumps({"error": {"message": "boom"}}).encode())
    )
    assert _http_error_detail(exc) == "HTTP 400: boom"


def test_http_error_detail_falls_back_to_raw_body_text() -> None:
    exc = urllib.error.HTTPError("u", 502, "Bad Gateway", {}, io.BytesIO(b"gateway down"))
    assert _http_error_detail(exc) == "HTTP 502: gateway down"


def test_http_error_detail_falls_back_when_json_has_no_message() -> None:
    exc = urllib.error.HTTPError("u", 500, "Server Error", {}, io.BytesIO(b'{"error": {}}'))
    assert _http_error_detail(exc) == 'HTTP 500: {"error": {}}'


def test_http_error_detail_falls_back_when_body_is_not_a_mapping() -> None:
    exc = urllib.error.HTTPError("u", 400, "Bad Request", {}, io.BytesIO(b"[1, 2, 3]"))
    assert _http_error_detail(exc) == "HTTP 400: [1, 2, 3]"


def test_http_error_detail_falls_back_to_reason_on_empty_body() -> None:
    exc = urllib.error.HTTPError("u", 503, "Unavailable", {}, io.BytesIO(b""))
    assert _http_error_detail(exc) == "HTTP 503: Unavailable"


def test_http_error_detail_falls_back_to_reason_when_body_unreadable() -> None:
    class UnreadableFp:
        def read(self) -> bytes:
            raise OSError("closed")

        def close(self) -> None:
            return None

    exc = urllib.error.HTTPError("u", 504, "Gateway Timeout", {}, UnreadableFp())  # type: ignore[arg-type]
    assert _http_error_detail(exc) == "HTTP 504: Gateway Timeout"


def test_server_argv_and_inspect(tmp_path: Path) -> None:
    llama = LlamaCppServer(tmp_path)
    model = tmp_path / "models" / PORTABLE.name / str(PORTABLE.filename)
    model.parent.mkdir(parents=True)
    model.write_bytes(b"x")
    assert "--jinja" in llama._argv(PORTABLE, 1234, "token")
    vllm = VllmServer(tmp_path)
    assert "hermes" in vllm._argv(NVIDIA_BF16, 1234, "token")
    state = tmp_path / "servers" / f"{PORTABLE.name}.json"
    state.parent.mkdir()
    state.write_text("bad")
    assert llama.inspect(PORTABLE) is None
    state.write_text(
        json.dumps(
            {
                "backend": "llama.cpp",
                "profile": PORTABLE.name,
                "endpoint": "x",
                "owned": True,
                "pid": 1,
            }
        )
    )
    assert llama.inspect(PORTABLE) is not None


@pytest.mark.asyncio
async def test_stop_obeys_ownership(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[int, object]] = []
    monkeypatch.setattr("os.killpg", lambda pid, sig: calls.append((pid, sig)))
    monkeypatch.setattr("qwenloop.infrastructure.inference._pid_alive", lambda _pid: False)
    server = LlamaCppServer(tmp_path)
    await server.stop(ServerInfo(Backend.LLAMA_CPP, "p", "x", False, True, 5))
    await server.stop(ServerInfo(Backend.LLAMA_CPP, "p", "x", True, True, 5))
    assert calls


@pytest.mark.asyncio
async def test_base_install_and_argv_are_not_implicit(tmp_path: Path) -> None:
    server = OpenAIServer(tmp_path)
    with pytest.raises(RuntimeError):
        await server.install(PORTABLE)
    with pytest.raises(NotImplementedError):
        server._argv(PORTABLE, 1, "t")
    with pytest.raises(FileNotFoundError):
        LlamaCppServer(tmp_path)._argv(PORTABLE, 1, "t")


@pytest.mark.asyncio
async def test_start_persists_owned_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    model = tmp_path / "models" / PORTABLE.name / str(PORTABLE.filename)
    model.parent.mkdir(parents=True)
    model.write_bytes(b"x")

    class Process:
        pid = 42

    async def create(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return Process()

    monkeypatch.setattr("qwenloop.infrastructure.inference._free_port", lambda: 1234)
    monkeypatch.setattr("asyncio.create_subprocess_exec", create)
    server = LlamaCppServer(tmp_path)
    info = await server.start(PORTABLE)
    assert info.pid == 42
    assert server.inspect(PORTABLE) is not None

    monkeypatch.setattr("qwenloop.infrastructure.inference._pid_alive", lambda _pid: True)
    reused = await server.start(PORTABLE)
    assert reused.pid == 42


@pytest.mark.asyncio
async def test_health_failure_and_malformed_tool_args(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def failed(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise OSError("offline")

    monkeypatch.setattr("urllib.request.urlopen", failed)
    server = LlamaCppServer(tmp_path)
    info = ServerInfo(Backend.LLAMA_CPP, "p", "http://bad/v1", True, False, 1)
    assert not await server.health(info)

    payload = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [{"function": {"name": "x", "arguments": "bad"}}],
                }
            }
        ]
    }
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: UrlResponse(json.dumps(payload).encode()),
    )
    chunks = [chunk async for chunk in server.chat_stream(info, [])]
    assert chunks[0].tool_call == {"name": "x", "arguments": {}}

    payload["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = {"x": 1}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: UrlResponse(json.dumps(payload).encode()),
    )
    chunks = [chunk async for chunk in server.chat_stream(info, [])]
    assert chunks[0].tool_call == {"name": "x", "arguments": {"x": 1}}

    payload["choices"][0]["message"] = {
        "content": '<tools>{"name":"read_file","arguments":{"path":"x"}}</tools>'
    }
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: UrlResponse(json.dumps(payload).encode()),
    )
    chunks = [chunk async for chunk in server.chat_stream(info, [])]
    assert chunks[0].tool_call == {"name": "read_file", "arguments": {"path": "x"}}
    assert chunks[1].text == ""


@pytest.mark.asyncio
async def test_stop_ignores_missing_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def missing(_pid, _signal):  # type: ignore[no-untyped-def]
        raise ProcessLookupError

    monkeypatch.setattr("os.killpg", missing)
    server = LlamaCppServer(tmp_path)
    await server.stop(ServerInfo(Backend.LLAMA_CPP, "p", "x", True, True, 99))


@pytest.mark.asyncio
async def test_stop_cleans_matching_state_and_forces_after_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    server = LlamaCppServer(tmp_path)
    state = tmp_path / "servers" / f"{PORTABLE.name}.json"
    state.parent.mkdir()
    state.write_text(
        json.dumps(
            {
                "backend": "llama.cpp",
                "profile": PORTABLE.name,
                "endpoint": "x",
                "owned": True,
                "pid": 7,
            }
        )
    )
    signals: list[object] = []
    monkeypatch.setattr("os.killpg", lambda _pid, sig: signals.append(sig))
    monkeypatch.setattr("qwenloop.infrastructure.inference._pid_alive", lambda _pid: True)

    async def no_sleep(_delay):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr("asyncio.sleep", no_sleep)
    await server.stop(ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", True, True, 7))
    assert len(signals) == 2
    assert not state.exists()


def test_pid_alive_outcomes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("os.kill", lambda *_args: None)
    assert _pid_alive(1)

    def denied(*_args):  # type: ignore[no-untyped-def]
        raise PermissionError

    monkeypatch.setattr("os.kill", denied)
    assert _pid_alive(1)

    def missing(*_args):  # type: ignore[no-untyped-def]
        raise ProcessLookupError

    monkeypatch.setattr("os.kill", missing)
    assert not _pid_alive(1)


def test_free_port_uses_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    from qwenloop.infrastructure import inference

    class Socket:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *_args):  # type: ignore[no-untyped-def]
            return None

        def bind(self, address):  # type: ignore[no-untyped-def]
            assert address == ("127.0.0.1", 0)

        def getsockname(self):  # type: ignore[no-untyped-def]
            return ("127.0.0.1", 4321)

    monkeypatch.setattr("socket.socket", Socket)
    assert inference._free_port() == 4321


def test_qwen_text_tool_calls_are_normalized() -> None:
    calls, remaining = _parse_text_tool_calls(
        'before <tools>{"name":"read_file","arguments":{"path":"README.md"}}</tools> after'
    )
    assert calls == [{"name": "read_file", "arguments": {"path": "README.md"}}]
    assert remaining == "before  after"

    malformed, unchanged = _parse_text_tool_calls("<tool_call>{bad}</tool_call>")
    assert malformed == []
    assert unchanged == "<tool_call>{bad}</tool_call>"

    invalid, _ = _parse_text_tool_calls('<tool_call>{"name": 1, "arguments": []}</tool_call>')
    assert invalid == []

    normalized, _ = _parse_text_tool_calls('<tool_call>{"name":"shell","arguments":[]}</tool_call>')
    assert normalized == [{"name": "shell", "arguments": {}}]
