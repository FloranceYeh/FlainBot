from __future__ import annotations


def port(name: str, type_: str) -> dict[str, str]:
    return {"name": name, "type": type_}


def builtin_node_catalog() -> list[dict]:
    return [
        {
            "kind": "package",
            "id": "core",
            "title": "Core",
            "description": "Built-in nodes for web chat graphs.",
            "items": [
                {
                    "kind": "group",
                    "id": "io",
                    "title": "Input / Output",
                    "items": [
                        {
                            "kind": "group",
                            "id": "web-chat",
                            "title": "Web Chat",
                            "items": [
                                {
                                    "kind": "node",
                                    "package": "core",
                                    "type": "chat_input",
                                    "className": "ChatInputNode",
                                    "title": "Web Chat Input",
                                    "description": "Reads the user's message from the web chat input.",
                                    "inputs": [],
                                    "outputs": [port("text", "text")],
                                    "defaults": {},
                                },
                                {
                                    "kind": "node",
                                    "package": "core",
                                    "type": "chat_output",
                                    "className": "ChatOutputNode",
                                    "title": "Web Chat Output",
                                    "description": "Sends model text to the web chat message list.",
                                    "inputs": [port("text", "text")],
                                    "outputs": [port("reply", "text")],
                                    "defaults": {},
                                },
                            ],
                        }
                    ],
                },
                {
                    "kind": "group",
                    "id": "processing",
                    "title": "Processing",
                    "items": [
                        {
                            "kind": "group",
                            "id": "prompting",
                            "title": "Prompting",
                            "items": [
                                {
                                    "kind": "node",
                                    "package": "core",
                                    "type": "prompt_builder",
                                    "className": "PromptBuilderNode",
                                    "title": "Prompt Builder",
                                    "description": "Assembles system, user, tools, and context into a JSON prompt payload.",
                                    "inputs": [
                                        port("system", "text"),
                                        port("user", "text"),
                                        port("tools", "json"),
                                        port("contexts", "json"),
                                    ],
                                    "outputs": [port("json", "json")],
                                    "defaults": {
                                        "system_prompt": "",
                                        "user_prompt": "",
                                        "tools_json": "[]",
                                        "contexts_json": "[]",
                                    },
                                }
                            ],
                        },
                        {
                            "kind": "group",
                            "id": "providers",
                            "title": "Providers",
                            "items": [
                                {
                                    "kind": "node",
                                    "package": "core",
                                    "type": "provider_call",
                                    "className": "ProviderCallNode",
                                    "title": "Call Provider",
                                    "description": "Consumes text or prompt JSON and calls a configured provider.",
                                    "inputs": [port("text", "text"), port("json", "json")],
                                    "outputs": [
                                        port("text", "text"),
                                        port("request", "json"),
                                        port("response", "json"),
                                    ],
                                    "defaults": {
                                        "provider_id": "",
                                    },
                                }
                            ],
                        },
                    ],
                },
            ],
        },
    ]
