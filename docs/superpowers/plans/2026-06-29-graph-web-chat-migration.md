# Graph Web Chat Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the linear pipeline concept with a ComfyUI-style directed graph runtime and a minimal browser chat flow.

**Architecture:** The public API centers on `Graph`, `GraphExecutor`, and port-based nodes. Runtime nodes use `run(inputs: dict) -> dict`; provider nodes consume `text` and produce `text`. A small standard-library web server serves the chat UI and runs `InputNode -> provider -> OutputNode` for `/api/chat`.

**Tech Stack:** Python 3.11+ standard library, `unittest`, static HTML/CSS/JavaScript.

---

### Task 1: Graph Core

**Files:**
- Create: `src/flainbot/graph.py`
- Modify: `src/flainbot/node.py`
- Modify: `src/flainbot/__init__.py`
- Delete: `src/flainbot/pipeline.py`
- Test: `tests/test_graph.py`

- [ ] **Step 1: Write graph execution tests**

Tests must verify:
- A graph connects node output ports to downstream input ports.
- Execution follows dependencies, not insertion order.
- Cycles raise `GraphError`.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_graph -v`

Expected: import failure for `Graph`.

- [ ] **Step 3: Implement graph runtime**

Implement:
- `Node` protocol with `run(inputs: Mapping[str, Any]) -> dict[str, Any]`
- `Graph.add_node(node_id, node)`
- `Graph.connect(from_node, from_port, to_node, to_port)`
- `GraphExecutor.run(inputs=None) -> dict[str, Any]`
- `GraphError`

- [ ] **Step 4: Run graph tests**

Run: `python -m unittest tests.test_graph -v`

Expected: PASS.

### Task 2: Runtime Boundary And Provider Nodes

**Files:**
- Modify: `src/flainbot/builtins.py`
- Modify: `src/flainbot/providers.py`
- Modify: `src/flainbot/__init__.py`
- Delete: `tests/test_pipeline.py`
- Delete: `tests/test_request_response.py`
- Modify: `tests/test_provider_nodes.py`

- [ ] **Step 1: Write node tests**

Tests must verify:
- `InputNode("hello").run({})` returns `{"text": "hello"}`.
- `OutputNode().run({"text": "reply"})` returns `{"reply": "reply"}`.
- `OpenAIChatNode.run({"text": "hello"})` sends a correct request and returns `{"text": ...}`.
- `AnthropicMessagesNode.run({"text": "hello"})` sends a correct request and returns `{"text": ...}`.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_provider_nodes -v`

Expected: failure because provider nodes still expose `handle(context)`.

- [ ] **Step 3: Implement port-style nodes**

Replace `handle(context)` provider behavior with `run(inputs)`.

- [ ] **Step 4: Run tests**

Run: `python -m unittest -v`

Expected: old pipeline tests fail until deleted/updated; graph/provider tests pass.

### Task 3: Smoke Script And Web Chat

**Files:**
- Modify: `scripts/smoke_chat.py`
- Create: `scripts/web_chat.py`
- Create: `frontend/chat.html`
- Create: `frontend/chat.js`
- Create: `frontend/chat.css`
- Modify: `tests/test_smoke_chat_script.py`
- Create: `tests/test_web_chat.py`

- [ ] **Step 1: Write script/server tests**

Tests must verify:
- Smoke script builds a graph containing input, provider, output nodes.
- `/api/chat` handler returns `{"reply": ...}` when provided a fake graph runner.

- [ ] **Step 2: Implement smoke graph**

`scripts/smoke_chat.py` should run `InputNode -> provider -> OutputNode`.

- [ ] **Step 3: Implement web chat server**

Use `http.server` to serve static files and handle `POST /api/chat`.

- [ ] **Step 4: Implement browser chat page**

Static page has a message list, input box, and send button.

### Task 4: Graph Planner Frontend

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Modify: `tests/test_frontend_static.py`
- Modify: `README.md`

- [ ] **Step 1: Update static tests**

Tests must assert planner code uses graph concepts: `nodes`, `edges`, `connect`, `GraphExecutor`.

- [ ] **Step 2: Convert planner state**

Replace `chain = []` with `graph = { nodes: [], edges: [] }`.

- [ ] **Step 3: Add simple port connection UI**

Use select boxes for source node/port and target node/port, then add edge.

- [ ] **Step 4: Generate Graph Python code**

Generated code should instantiate `Graph`, add nodes, connect ports, and run `GraphExecutor`.

### Task 5: Final Verification And Commit

**Files:**
- All changed files.

- [ ] **Step 1: Run all tests**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 2: Check no Pipeline remains**

Run: `rg "Pipeline|pipeline" src tests scripts frontend README.md`

Expected: no references except historical docs under `docs/superpowers/plans`.

- [ ] **Step 3: Commit**

```powershell
git add .
git commit -m "refactor: migrate runtime to graph web chat"
```

