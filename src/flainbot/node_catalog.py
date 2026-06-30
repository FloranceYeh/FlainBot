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
            "type": "openai",
            "className": "OpenAIChatNode",
            "title": "OpenAI Chat",
            "description": "Consumes text and calls an OpenAI-compatible chat endpoint.",
            "inputs": ["text"],
            "outputs": ["text", "request", "response"],
            "defaults": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "",
                "model": "gpt-4.1-mini",
            },
        },
        {
            "type": "anthropic",
            "className": "AnthropicMessagesNode",
            "title": "Anthropic Messages",
            "description": "Consumes text and calls the Anthropic Messages API.",
            "inputs": ["text"],
            "outputs": ["text", "request", "response"],
            "defaults": {
                "base_url": "https://api.anthropic.com/v1",
                "api_key": "",
                "model": "claude-sonnet-4-5",
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
