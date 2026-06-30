from __future__ import annotations


def builtin_node_catalog() -> list[dict]:
    return [
        {
            "type": "chat_input",
            "className": "ChatInputNode",
            "title": "Web Chat Input",
            "description": "Reads the user's message from the web chat input.",
            "inputs": [],
            "outputs": ["text"],
            "defaults": {},
        },
        {
            "type": "provider_call",
            "className": "ProviderCallNode",
            "title": "Call Provider",
            "description": "Consumes text and calls a configured provider.",
            "inputs": ["text"],
            "outputs": ["text", "request", "response"],
            "defaults": {
                "provider_id": "",
            },
        },
        {
            "type": "prompt_builder",
            "className": "PromptBuilderNode",
            "title": "Prompt Builder",
            "description": "Assembles system, user, tools, and context into a JSON prompt payload.",
            "inputs": ["system", "user", "tools", "context"],
            "outputs": ["json"],
            "defaults": {
                "system_prompt": "",
                "user_prompt": "",
                "tools_json": "[]",
                "context_json": "{}",
            },
        },
        {
            "type": "chat_output",
            "className": "ChatOutputNode",
            "title": "Web Chat Output",
            "description": "Sends model text to the web chat message list.",
            "inputs": ["text"],
            "outputs": ["reply"],
            "defaults": {},
        },
    ]
