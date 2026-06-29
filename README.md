# FlainBot

FlainBot is a developer-facing chatbot framework built around composable event
chains. The first version focuses on a minimal linear pipeline while keeping the
node interface open for later adapters and extensions.

## Minimal Example

```python
from flainbot import MessageContext, Pipeline


class CaptureInput:
    name = "capture_input"

    def handle(self, context):
        context.data["captured"] = context.input_text


class BuildReply:
    name = "build_reply"

    def handle(self, context):
        context.output_text = f"echo: {context.data['captured']}"


pipeline = Pipeline([CaptureInput(), BuildReply()])
context = pipeline.run(MessageContext(input_text="hello"))

print(context.output_text)
print(context.trace)
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

