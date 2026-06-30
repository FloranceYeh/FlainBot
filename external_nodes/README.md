# External Node Packages

FlainBot loads project-local external nodes from this `external_nodes` package
when the backend starts or when `/api/nodes` is requested.

Each module in this directory is one node package module and must expose:

- `get_node_package() -> dict`: returns the package/group/node metadata shown in
  the frontend node list.
- `get_node_builders() -> dict[str, NodeBuilder]`: maps each node `type` to a
  builder function.

Builder functions receive `(node_config, context)` and return an object with:

- `name: str`
- `run(inputs: dict) -> dict`

Node metadata should keep `package`, `type`, `inputs`, `outputs`, and
`defaults` accurate. The `type` value must be globally unique across built-in
and external packages.

`sample_text_tools.py` is a complete example. It defines a
`meow_before_punctuation` node that accepts `text` and outputs `text` with the
`U+55B5` character inserted before every punctuation mark.
