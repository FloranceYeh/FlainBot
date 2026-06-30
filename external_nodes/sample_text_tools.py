from __future__ import annotations

import unicodedata
from typing import Any

from flainbot.node_registry import NodeBuildContext, NodeBuilder

MEOW = "\u55b5"


class MeowBeforePunctuationNode:
    name = "meow_before_punctuation"

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        text = str(inputs.get("text", ""))
        return {"text": "".join(meow_before_punctuation(text))}


def meow_before_punctuation(text: str):
    for character in text:
        if unicodedata.category(character).startswith("P"):
            yield MEOW
        yield character


def port(name: str, type_: str) -> dict[str, str]:
    return {"name": name, "type": type_}


def get_node_package() -> dict[str, Any]:
    return {
        "kind": "package",
        "id": "sample_text_tools",
        "title": "Sample Text Tools",
        "description": "Example external node package.",
        "items": [
            {
                "kind": "group",
                "id": "text",
                "title": "Text",
                "items": [
                    {
                        "kind": "node",
                        "package": "sample_text_tools",
                        "type": "meow_before_punctuation",
                        "className": "MeowBeforePunctuationNode",
                        "title": "Meow Before Punctuation",
                        "description": f"Adds the character '{MEOW}' before every punctuation mark.",
                        "inputs": [port("text", "text")],
                        "outputs": [port("text", "text")],
                        "defaults": {},
                    }
                ],
            }
        ],
    }


def get_node_builders() -> dict[str, NodeBuilder]:
    return {
        "meow_before_punctuation": build_meow_before_punctuation,
    }


def build_meow_before_punctuation(
    node_config: dict[str, Any],
    context: NodeBuildContext,
) -> MeowBeforePunctuationNode:
    return MeowBeforePunctuationNode()
