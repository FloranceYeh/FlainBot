# Minimal Chain Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first developer-facing FlainBot core that can run a simple chat pipeline while preserving extension interfaces.

**Architecture:** The core is a small Python package under `src/flainbot`. `MessageContext` carries message state, `Node` defines the extension contract, and `Pipeline` executes nodes in order with trace records and clear error wrapping.

**Tech Stack:** Python 3.11+ standard library, `unittest`, src-layout package.

---

### Task 1: Project Skeleton And Public API

**Files:**
- Create: `pyproject.toml`
- Create: `src/flainbot/__init__.py`
- Create: `src/flainbot/context.py`
- Create: `src/flainbot/node.py`
- Create: `src/flainbot/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing import and context test**

```python
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import MessageContext


class MessageContextTests(unittest.TestCase):
    def test_context_starts_with_input_and_empty_trace(self):
        context = MessageContext(input_text="hello")

        self.assertEqual(context.input_text, "hello")
        self.assertIsNone(context.output_text)
        self.assertEqual(context.data, {})
        self.assertEqual(context.trace, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_pipeline -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'flainbot'`.

- [ ] **Step 3: Add minimal package skeleton**

```python
# src/flainbot/context.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MessageContext:
    input_text: str
    output_text: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    trace: list[Any] = field(default_factory=list)
```

```python
# src/flainbot/__init__.py
from .context import MessageContext

__all__ = ["MessageContext"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_pipeline -v`

Expected: PASS.

### Task 2: Linear Pipeline Execution

**Files:**
- Modify: `src/flainbot/node.py`
- Modify: `src/flainbot/pipeline.py`
- Modify: `src/flainbot/__init__.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing linear execution test**

```python
class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_nodes_in_order(self):
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

        self.assertEqual(context.output_text, "echo: hello")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_pipeline.PipelineTests.test_pipeline_runs_nodes_in_order -v`

Expected: FAIL with `NameError: name 'Pipeline' is not defined` or import failure.

- [ ] **Step 3: Implement minimal pipeline and node protocol**

```python
# src/flainbot/node.py
from __future__ import annotations

from typing import Protocol

from .context import MessageContext


class Node(Protocol):
    name: str

    def handle(self, context: MessageContext) -> None:
        ...
```

```python
# src/flainbot/pipeline.py
from __future__ import annotations

from collections.abc import Iterable

from .context import MessageContext
from .node import Node


class Pipeline:
    def __init__(self, nodes: Iterable[Node] = ()) -> None:
        self._nodes = list(nodes)

    @property
    def nodes(self) -> tuple[Node, ...]:
        return tuple(self._nodes)

    def run(self, context: MessageContext) -> MessageContext:
        for node in self._nodes:
            node.handle(context)
        return context
```

- [ ] **Step 4: Export public API and run tests**

Run: `python -m unittest tests.test_pipeline -v`

Expected: PASS.

### Task 3: Extension Insertion And Trace Records

**Files:**
- Modify: `src/flainbot/context.py`
- Modify: `src/flainbot/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests for insertion and trace**

```python
    def test_pipeline_can_insert_extension_between_nodes(self):
        class Start:
            name = "start"

            def handle(self, context):
                context.output_text = "hello"

        class Segment:
            name = "segment"

            def handle(self, context):
                context.output_text = "|".join(context.output_text)

        pipeline = Pipeline([Start()])
        pipeline.insert_after("start", Segment())

        context = pipeline.run(MessageContext(input_text="ignored"))

        self.assertEqual(context.output_text, "h|e|l|l|o")
        self.assertEqual([node.name for node in pipeline.nodes], ["start", "segment"])

    def test_pipeline_records_node_trace(self):
        class Noop:
            name = "noop"

            def handle(self, context):
                context.data["handled"] = True

        context = Pipeline([Noop()]).run(MessageContext(input_text="hello"))

        self.assertEqual(len(context.trace), 1)
        self.assertEqual(context.trace[0].node_name, "noop")
        self.assertEqual(context.trace[0].status, "ok")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_pipeline.PipelineTests -v`

Expected: FAIL because `insert_after` and trace records are missing.

- [ ] **Step 3: Add trace record and insertion API**

```python
# src/flainbot/context.py
@dataclass(frozen=True)
class NodeTrace:
    node_name: str
    status: str
    error: str | None = None
```

```python
# src/flainbot/pipeline.py
    def insert_after(self, existing_node_name: str, node: Node) -> None:
        for index, existing in enumerate(self._nodes):
            if existing.name == existing_node_name:
                self._nodes.insert(index + 1, node)
                return
        raise ValueError(f"node not found: {existing_node_name}")

    def run(self, context: MessageContext) -> MessageContext:
        for node in self._nodes:
            node.handle(context)
            context.trace.append(NodeTrace(node_name=node.name, status="ok"))
        return context
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_pipeline -v`

Expected: PASS.

### Task 4: Node Error Wrapping

**Files:**
- Modify: `src/flainbot/pipeline.py`
- Modify: `src/flainbot/__init__.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing error test**

```python
    def test_pipeline_wraps_node_errors_with_node_name(self):
        class Broken:
            name = "broken"

            def handle(self, context):
                raise RuntimeError("boom")

        context = MessageContext(input_text="hello")

        with self.assertRaises(PipelineError) as raised:
            Pipeline([Broken()]).run(context)

        self.assertEqual(raised.exception.node_name, "broken")
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertEqual(context.trace[0].node_name, "broken")
        self.assertEqual(context.trace[0].status, "error")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_pipeline.PipelineTests.test_pipeline_wraps_node_errors_with_node_name -v`

Expected: FAIL because `PipelineError` is missing.

- [ ] **Step 3: Implement error wrapping**

```python
class PipelineError(RuntimeError):
    def __init__(self, node_name: str, message: str) -> None:
        super().__init__(f"{node_name}: {message}")
        self.node_name = node_name
```

Wrap exceptions in `Pipeline.run`, append an error trace, and re-raise `PipelineError` from the original exception.

- [ ] **Step 4: Run all tests**

Run: `python -m unittest -v`

Expected: PASS.

