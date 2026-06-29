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


class OpenAIChatNode:
    name = "openai_chat"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._transport = transport or json_post

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
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


class AnthropicMessagesNode:
    name = "anthropic_messages"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        transport: Transport | None = None,
        max_tokens: int = 1024,
        anthropic_version: str = "2023-06-01",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.anthropic_version = anthropic_version
        self._transport = transport or json_post

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        request_body: JsonObject = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": inputs["text"]}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
        }
        response = self._transport(f"{self.base_url}/messages", headers, request_body)
        return {
            "request": request_body,
            "response": response,
            "text": response["content"][0]["text"],
        }
