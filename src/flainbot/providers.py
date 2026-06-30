from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError

JsonObject = dict[str, Any]
Transport = Callable[[str, dict[str, str], JsonObject], JsonObject]


def json_post(url: str, headers: dict[str, str], body: JsonObject) -> JsonObject:
    data = json.dumps(body).encode("utf-8")
    req = urllib_request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        error_payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_payload}") from exc
    return json.loads(payload)


class ProviderCallNode:
    name = "provider_call"

    def __init__(self, provider: JsonObject, transport: Transport | None = None) -> None:
        self.provider = provider
        self.base_url = provider["base_url"].rstrip("/")
        self.api_key = provider["api_key"]
        self.model = provider["model"]
        self.format = provider["format"]
        self._transport = transport or json_post

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        if self.format == "openai_chat":
            return self._run_openai_chat(inputs)
        if self.format == "anthropic_messages":
            return self._run_anthropic_messages(inputs)
        raise ValueError(f"unsupported provider format: {self.format}")

    def _run_openai_chat(self, inputs: dict[str, Any]) -> dict[str, Any]:
        request_body: JsonObject = {
            "model": self.model,
            "messages": [{"role": "user", "content": inputs["text"]}],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = self._transport(
            f"{self.base_url}/chat/completions", headers, request_body
        )
        return {
            "request": request_body,
            "response": response,
            "text": response["choices"][0]["message"]["content"],
        }

    def _run_anthropic_messages(self, inputs: dict[str, Any]) -> dict[str, Any]:
        request_body: JsonObject = {
            "model": self.model,
            "max_tokens": self.provider.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": inputs["text"]}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.provider.get("anthropic_version", "2023-06-01"),
            "Content-Type": "application/json",
        }
        response = self._transport(f"{self.base_url}/messages", headers, request_body)
        return {
            "request": request_body,
            "response": response,
            "text": response["content"][0]["text"],
        }
