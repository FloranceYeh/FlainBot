from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError

from .runtime_logging import NodeRuntimeLogger

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

    def __init__(
        self,
        provider: JsonObject,
        transport: Transport | None = None,
        logger: NodeRuntimeLogger | None = None,
    ) -> None:
        self.provider = provider
        self.base_url = provider["base_url"].rstrip("/")
        self.api_key = provider["api_key"]
        self.model = provider["model"]
        self.format = provider["format"]
        self._transport = transport or json_post
        self.logger = logger

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        if self.logger:
            self.logger.info(
                "provider_call.started",
                provider_id=self.provider.get("id"),
                format=self.format,
                model=self.model,
            )
        if self.format == "openai_chat":
            outputs = self._run_openai_chat(inputs)
        elif self.format == "anthropic_messages":
            outputs = self._run_anthropic_messages(inputs)
        else:
            raise ValueError(f"unsupported provider format: {self.format}")
        if self.format == "anthropic_messages":
            response_items = len(outputs.get("response", {}).get("content", []))
        else:
            response_items = len(outputs.get("response", {}).get("choices", []))
        if self.logger:
            self.logger.info(
                "provider_call.completed",
                provider_id=self.provider.get("id"),
                format=self.format,
                model=self.model,
                response_items=response_items,
            )
        return outputs

    def _run_openai_chat(self, inputs: dict[str, Any]) -> dict[str, Any]:
        prompt_payload = prompt_payload_from_inputs(inputs)
        request_body: JsonObject = {
            "model": self.model,
            "messages": openai_messages_from_prompt_payload(prompt_payload),
        }
        if prompt_payload["tools"]:
            request_body["tools"] = prompt_payload["tools"]
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
        prompt_payload = prompt_payload_from_inputs(inputs)
        request_body: JsonObject = {
            "model": self.model,
            "max_tokens": self.provider.get("max_tokens", 1024),
            "messages": anthropic_messages_from_prompt_payload(prompt_payload),
        }
        if prompt_payload["system_prompt"]:
            request_body["system"] = prompt_payload["system_prompt"]
        if prompt_payload["tools"]:
            request_body["tools"] = prompt_payload["tools"]
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


def prompt_payload_from_inputs(inputs: dict[str, Any]) -> JsonObject:
    payload = inputs.get("json")
    if payload is None:
        payload = {"prompt": inputs["text"]}
    if not isinstance(payload, dict):
        raise TypeError("provider json input must be an object")
    return {
        "prompt": payload.get("prompt", ""),
        "system_prompt": payload.get("system_prompt", ""),
        "contexts": payload.get("contexts", []),
        "tools": payload.get("tools", []),
    }


def openai_messages_from_prompt_payload(payload: JsonObject) -> list[JsonObject]:
    messages: list[JsonObject] = []
    if payload["system_prompt"]:
        messages.append({"role": "system", "content": payload["system_prompt"]})
    messages.extend(payload["contexts"])
    if payload["prompt"]:
        messages.append({"role": "user", "content": payload["prompt"]})
    return messages


def anthropic_messages_from_prompt_payload(payload: JsonObject) -> list[JsonObject]:
    return [
        message
        for message in openai_messages_from_prompt_payload(
            {**payload, "system_prompt": ""}
        )
        if message.get("role") != "system"
    ]
