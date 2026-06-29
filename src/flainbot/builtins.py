from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import MessageContext

Request = dict[str, Any]
Response = dict[str, Any]
RequestBuilder = Callable[[MessageContext], Request]
Client = Callable[[Request], Response]


def default_request_builder(context: MessageContext) -> Request:
    return {"messages": [{"role": "user", "content": context.input_text}]}


class RequestNode:
    name = "request"

    def __init__(
        self,
        client: Client,
        build_request: RequestBuilder = default_request_builder,
    ) -> None:
        self._client = client
        self._build_request = build_request

    def handle(self, context: MessageContext) -> None:
        request = self._build_request(context)
        context.data["request"] = request
        context.data["response"] = self._client(request)


class ResponseNode:
    name = "response"

    def handle(self, context: MessageContext) -> None:
        response = context.data["response"]
        context.output_text = response["text"]

