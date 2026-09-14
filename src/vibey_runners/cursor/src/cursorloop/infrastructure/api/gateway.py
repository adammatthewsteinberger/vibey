# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""HTTP gateway for Cloud Agents REST calls (Bearer + redaction)."""

from __future__ import annotations

from typing import Any

import httpx

from cursorloop.infrastructure.redact import redact


class CloudAgentsGateway:
    """Thin httpx wrapper. Full OpenAPI generation is deferred (ADR-0006)."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.cursor.com",
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.Client(base_url=self._base_url, timeout=30.0)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> CloudAgentsGateway:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def invoke(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Authorization"] = f"Bearer {self._api_key}"
        response = self._client.request(method.upper(), path, headers=headers, **kwargs)
        response.raise_for_status()
        if not response.content:
            return {}
        raw: Any = response.json()
        if isinstance(raw, dict):
            redacted = redact(raw)
            if isinstance(redacted, dict):
                return redacted
            return {"data": redacted}
        return {"data": raw}
