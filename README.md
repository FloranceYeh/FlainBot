# FlainBot

FlainBot is a developer-facing chatbot framework built around composable
directed graphs. Nodes expose typed input and output ports, and edges connect
those ports into a runtime graph.

## Minimal Example

```python
import os

from flainbot import ChatInputNode, ChatOutputNode, Graph, GraphExecutor, OpenAIChatNode


graph = Graph()
graph.add_node("input", ChatInputNode("hello"))
graph.add_node(
    "model",
    OpenAIChatNode(
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
        model="gpt-4.1-mini",
    ),
)
graph.add_node("output", ChatOutputNode())
graph.connect("input", "text", "model", "text")
graph.connect("model", "text", "output", "text")

outputs = GraphExecutor(graph).run()
print(outputs["output"]["reply"])
```

Anthropic-compatible nodes use the same graph shape with
`AnthropicMessagesNode`.

## Extension Point

Any object with `name: str` and `run(inputs: Mapping[str, Any]) -> dict[str, Any]`
can be used as a node. A node receives values from connected input ports and
returns values for its output ports.

## Tests

```powershell
python -m unittest -v
```

## Node Planner

Open `frontend/index.html` in a browser to view available nodes and plan a graph
on a draggable canvas. Node properties are edited inside each node, and output
ports connect to input ports with arrowed edges. The page runs locally without a
dev server for visual editing. To save the active graph for web chat, run
`scripts/web_chat.py`; the static planner will call its API on
`http://127.0.0.1:8765` when opened from `file://` or a `5500` live server.
The same `index.html` also contains the chat view; switch with the top
navigation or open `frontend/index.html#chat`.

## Web Chat

OpenAI:

```powershell
$env:OPENAI_API_KEY="sk-..."
python start.py --model gpt-4.1-mini
```

Anthropic:

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
python start.py --provider anthropic --model claude-sonnet-4-5
```

Then open the printed local URL in a browser.
Use the Chat tab or `http://127.0.0.1:8765/#chat` to talk to the active graph.
The cross-platform `start.py` wrapper delegates to `scripts/web_chat.py` and
accepts `--host`, `--port`, `--model`, and `--base-url`.

## Real Graph Smoke Test

```powershell
python scripts/smoke_chat.py openai --model gpt-4.1-mini
```

Compatible gateways can override the base URL:

```powershell
python scripts/smoke_chat.py openai --base-url https://example.com/v1 --model your-model
```
