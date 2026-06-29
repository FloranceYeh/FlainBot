# FlainBot

FlainBot is a developer-facing chatbot framework built around composable event
chains. The first version focuses on a minimal linear pipeline while keeping the
node interface open for later adapters and extensions.

## Minimal Example

```python
from flainbot import MessageContext, Pipeline, RequestNode, ResponseNode


def fake_client(request):
    user_message = request["messages"][-1]["content"]
    return {"text": f"echo: {user_message}"}


pipeline = Pipeline([RequestNode(client=fake_client), ResponseNode()])
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
