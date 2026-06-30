# External Nodes

FlainBot discovers external node packages from the project-local
`external_nodes` Python package. The backend merges these packages with built-in
node packages for `/api/nodes`, and graph execution uses the same registry to
build runtime nodes.

An external node package is a Python module under `external_nodes/`.

Required module functions:

- `get_node_package() -> dict`: returns the package tree used by the frontend.
- `get_node_builders() -> dict[str, NodeBuilder]`: maps node `type` values to
  builder functions.

Required runtime node shape:

- `name: str`
- `run(inputs: dict) -> dict`

Builder signature:

```python
def build_my_node(node_config: dict, context: NodeBuildContext):
    return MyNode()
```

The `context` contains the current chat message, transports, providers, and
personas. Use `node_config["props"]` for per-node settings.

Metadata rules:

- package entries use `kind: "package"`.
- nested groups use `kind: "group"` and `items`.
- node entries use `kind: "node"`.
- `type` must be globally unique.
- `inputs` and `outputs` are lists of `{ "name": "...", "type": "..." }`.
- `defaults` contains editable node property defaults.

See `external_nodes/sample_text_tools.py` for a complete package. It provides a
`meow_before_punctuation` text node.
