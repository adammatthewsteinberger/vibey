# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""HTTP adapter for the generated Gemini REST CLI."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlencode

from agyloop.infrastructure.api.discover import (
    ApiLane,
    DiscoveredMethod,
    discover_surface,
    parse_api_lane,
)

DEVELOPER_ROOT = "https://generativelanguage.googleapis.com/"
VERTEX_ROOT = "https://aiplatform.googleapis.com/"
_PATH_PARAM = re.compile(r"\{([^}]+)\}")


class HttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, str]: ...


class UrllibTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, str]:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:  # nosec B310 — https only
                return int(response.status), response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            return int(exc.code), payload or str(exc)


def interpolate_path(template: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    leftover = dict(params)

    def replacer(match: re.Match[str]) -> str:
        inner = match.group(1)
        key = inner.lstrip("+").split("=", 1)[0]
        if key not in leftover:
            raise ValueError(f"missing path parameter {key!r} for {template}")
        value = leftover.pop(key)
        return str(value).lstrip("/")

    return _PATH_PARAM.sub(replacer, template), leftover


def _load_json_payload(*, json_body: str | None, json_file: Path | None) -> dict[str, Any]:
    if json_body and json_file:
        raise ValueError("pass only one of --json or --json-file")
    raw: str | None = json_body
    if json_file is not None:
        raw = Path(json_file).read_text(encoding="utf-8")
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("--json must be a JSON object")
    return data


class GeminiRestGateway:
    """Concrete ``ApiGateway`` for the generated Gemini REST surface."""

    def __init__(self, *, transport: HttpTransport | None = None) -> None:
        self._transport = transport or UrllibTransport()

    def invoke(
        self,
        method_path: str,
        *,
        lane: str = "developer",
        json_body: str | None = None,
        json_file: Path | None = None,
        scalar_values: dict[str, Any] | None = None,
        method: DiscoveredMethod | None = None,
    ) -> Any:
        parsed_lane = parse_api_lane(lane)
        resolved = method or _method_for(method_path, parsed_lane)
        if resolved.lane != parsed_lane:
            raise ValueError(
                f"{method_path} belongs to lane {resolved.lane!r}, not {parsed_lane!r}"
            )
        payload = _load_json_payload(json_body=json_body, json_file=json_file)
        for key, value in (scalar_values or {}).items():
            if value is not None:
                payload[key] = value
        path, leftover = interpolate_path(resolved.http_path, payload)
        url = _url_for(parsed_lane, path)
        headers = {"Accept": "application/json", "User-Agent": "agyloop"}
        body: bytes | None = None
        method_verb = resolved.http_method.upper()
        if method_verb in {"POST", "PATCH", "PUT"}:
            headers["Content-Type"] = "application/json"
            body = json.dumps(leftover).encode("utf-8")
        elif leftover:
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}{urlencode({k: str(v) for k, v in leftover.items()})}"
        url, headers = _authenticate(parsed_lane, url, headers)
        status, text = self._transport.request(method_verb, url, headers=headers, body=body)
        try:
            parsed: Any = json.loads(text) if text else {}
        except json.JSONDecodeError:
            parsed = {"raw": text}
        if status >= 400:
            raise ValueError(f"Gemini REST {method_path} failed ({status}): {text}")
        return parsed

    def invoke_and_print(self, method_path: str, **options: Any) -> str:
        result = self.invoke(method_path, **options)
        return json.dumps(result, indent=2, default=str)


def _method_for(method_path: str, lane: ApiLane) -> DiscoveredMethod:
    for item in discover_surface(lane=lane):
        if item.path == method_path:
            return item
    raise ValueError(f"unknown method {method_path!r} for lane {lane}")


def _url_for(lane: ApiLane, path: str) -> str:
    root = DEVELOPER_ROOT if lane == "developer" else VERTEX_ROOT
    return root.rstrip("/") + "/" + path.lstrip("/")


def _authenticate(lane: ApiLane, url: str, headers: dict[str, str]) -> tuple[str, dict[str, str]]:
    if lane == "vertex":
        token = _vertex_access_token()
        out = dict(headers)
        out["Authorization"] = f"Bearer {token}"
        return url, out
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) is required for --lane developer")
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}{urlencode({'key': key})}", headers


def _vertex_access_token() -> str:
    for name in ("GOOGLE_ACCESS_TOKEN", "CLOUDSDK_AUTH_ACCESS_TOKEN"):
        token = os.environ.get(name)
        if token and token.strip():
            return token.strip()
    raise ValueError(
        "Vertex lane needs GOOGLE_ACCESS_TOKEN (or CLOUDSDK_AUTH_ACCESS_TOKEN). "
        "ADC is not read here; export a short-lived token from `gcloud auth print-access-token`."
    )


def default_gateway() -> GeminiRestGateway:
    return GeminiRestGateway()
