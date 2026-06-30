# Prompt Builder Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a prompt assembly node that outputs a JSON-compatible payload from system/user prompts, tools, and context.

**Architecture:** `PromptBuilderNode` is a pure built-in node. It merges default properties with connected inputs, parses JSON fields for tools/context, and outputs a Python dict on a `json` port. The frontend exposes it as a planner node; provider nodes remain optional and separate.

**Tech Stack:** Python standard library, static JavaScript frontend, `unittest`.

---

### Task 1: Runtime Node

**Files:**
- Modify: `src/flainbot/builtins.py`
- Modify: `src/flainbot/__init__.py`
- Modify: `src/flainbot/config.py`
- Modify: `tests/test_graph_config.py`

- [ ] Add failing tests for `PromptBuilderNode` default payload, input override behavior, JSON parsing, and config execution.
- [ ] Implement `PromptBuilderNode`.
- [ ] Wire `prompt_builder` into config builder and package exports.

### Task 2: Frontend Planner Node

**Files:**
- Modify: `frontend/app.js`
- Modify: `tests/test_frontend_static.py`

- [ ] Add static assertions for `PromptBuilderNode`, `prompt_builder`, prompt fields, and `json` port.
- [ ] Add the node to the frontend catalog.
- [ ] Add generated Python output for `PromptBuilderNode`.

### Task 3: Verification And Commit

- [ ] Run `python -m unittest -v`.
- [ ] Run `python -m py_compile src/flainbot/builtins.py src/flainbot/config.py`.
- [ ] Run `node --check frontend/app.js`.
- [ ] Commit the scoped feature.
