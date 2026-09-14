#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run a reproducible 50-case local quantization smoke evaluation."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(url: str, token: str, payload: dict[str, object] | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read())


def wait_ready(endpoint: str, token: str) -> float:
    started = time.monotonic()
    for _ in range(720):
        try:
            request(f"{endpoint}/models", token)
            return time.monotonic() - started
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise TimeoutError("server did not become ready")


def evaluate(label: str, model: Path) -> dict[str, object]:
    port = free_port()
    token = os.urandom(24).hex()
    process = subprocess.Popen(  # noqa: S603
        [
            "llama-server",  # noqa: S607
            "--model",
            str(model),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--ctx-size",
            "4096",
            "--api-key",
            token,
            "--jinja",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    endpoint = f"http://127.0.0.1:{port}/v1"
    try:
        load_seconds = wait_ready(endpoint, token)
        started = time.monotonic()
        correct = 0
        output_tokens = 0
        for index in range(40):
            left = index * 17 + 3
            right = index * 11 + 5
            expected = str(left + right)
            data = request(
                f"{endpoint}/chat/completions",
                token,
                {
                    "model": label,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Return only the integer result of {left} + {right}.",
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 16,
                },
            )
            message = str(data["choices"][0]["message"].get("content") or "").strip()
            correct += message == expected
            output_tokens += int(data.get("usage", {}).get("completion_tokens", 0))
        valid_tools = 0
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            }
        ]
        for index in range(10):
            expected_path = f"fixture-{index}.txt"
            data = request(
                f"{endpoint}/chat/completions",
                token,
                {
                    "model": label,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Call read_file exactly once with path "
                                f"{expected_path}; do not answer in prose."
                            ),
                        }
                    ],
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0,
                    "max_tokens": 64,
                },
            )
            message = data["choices"][0]["message"]
            encoded = json.dumps(message)
            valid_tools += "read_file" in encoded and expected_path in encoded
            output_tokens += int(data.get("usage", {}).get("completion_tokens", 0))
        elapsed = time.monotonic() - started
        return {
            "label": label,
            "model": str(model),
            "cases": 50,
            "exact_answer_passes": correct,
            "valid_tool_calls": valid_tools,
            "load_seconds": round(load_seconds, 3),
            "evaluation_seconds": round(elapsed, 3),
            "output_tokens": output_tokens,
        }
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=30)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+", metavar="LABEL=PATH")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = []
    for value in args.models:
        label, raw_path = value.split("=", 1)
        results.append(evaluate(label, Path(raw_path)))
    rendered = json.dumps(results, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
