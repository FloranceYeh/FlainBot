# FlainBot

FlainBot is a developer-facing chatbot framework built around composable
directed graphs. Nodes expose typed input and output ports, and edges connect
those ports into a runtime graph.

## Minimal Example

```python
import os

from flainbot import Graph, GraphExecutor, InputNode, OpenAIChatNode, OutputNode


graph = Graph()
graph.add_node("input", InputNode("hello"))
graph.add_node(
    "model",
    OpenAIChatNode(
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
        model="gpt-4.1-mini",
    ),
)
graph.add_node("output", OutputNode())
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

Open `frontend/index.html` in a browser to view available nodes and plan a graph.
The page runs locally without a dev server.

## Web Chat

OpenAI:

```powershell
$env:OPENAI_API_KEY="sk-..."
python scripts/web_chat.py openai --model gpt-4.1-mini
```

Anthropic:

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
python scripts/web_chat.py anthropic --model claude-sonnet-4-5
```

Then open the printed local URL in a browser.

## Real Graph Smoke Test

```powershell
python scripts/smoke_chat.py openai --model gpt-4.1-mini
```

Compatible gateways can override the base URL:

```powershell
python scripts/smoke_chat.py openai --base-url https://example.com/v1 --model your-model
```

