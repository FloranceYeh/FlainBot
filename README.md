# FlainBot

FlainBot is a developer-facing chatbot framework built around composable event
chains. The first version focuses on a minimal linear pipeline while keeping the
node interface open for later adapters and extensions.

## Minimal Example

```python
import os

from flainbot import MessageContext, OpenAIChatNode, Pipeline


node = OpenAIChatNode(
    base_url="https://api.openai.com/v1",
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4.1-mini",
)

pipeline = Pipeline([node])
context = pipeline.run(MessageContext(input_text="hello"))

print(context.output_text)
print(context.trace)
```

Anthropic-compatible nodes use the same shape:

```python
import os

from flainbot import AnthropicMessagesNode, MessageContext, Pipeline


node = AnthropicMessagesNode(
    base_url="https://api.anthropic.com/v1",
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-sonnet-4-5",
)

pipeline = Pipeline([node])
context = pipeline.run(MessageContext(input_text="hello"))

print(context.output_text)
```

## Extension Point

Any object with `name: str` and `handle(context: MessageContext) -> None` can be
used as a node. Extensions can be inserted into an existing chain:

```python
pipeline.insert_after("build_reply", SegmentMessage())
```

## Tests

```powershell
python -m unittest -v
```
