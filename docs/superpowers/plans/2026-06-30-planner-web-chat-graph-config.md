# Planner Web Chat Graph Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the planner save a graph configuration that web chat can execute directly.

**Architecture:** `ChatInputNode` and `ChatOutputNode` become explicit runtime boundary nodes in the graph. Planner JSON stores node ids, node types, props, coordinates, and edges. The web chat server keeps the active graph config in memory and uses a builder to instantiate `Graph` objects per incoming chat message.

**Tech Stack:** Python standard library, static browser JavaScript, `unittest`.

---

### Task 1: Runtime Nodes And Config Builder

**Files:**
- Modify: `src/flainbot/builtins.py`
- Modify: `src/flainbot/providers.py`
- Modify: `src/flainbot/__init__.py`
- Create: `src/flainbot/config.py`
- Modify: `tests/test_provider_nodes.py`
- Create: `tests/test_graph_config.py`

- [ ] Write failing tests for `ChatInputNode`, `ChatOutputNode`, direct provider `api_key`, and config-to-graph execution.
- [ ] Implement nodes and config builder.
- [ ] Run targeted tests.

### Task 2: Web Chat Graph API

**Files:**
- Modify: `scripts/web_chat.py`
- Modify: `tests/test_web_chat.py`

- [ ] Write failing tests for `GET /api/graph`, `POST /api/graph`, and `/api/chat` using the active graph config.
- [ ] Implement in-memory active graph config.
- [ ] Run web chat tests.

### Task 3: Planner Save Button

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Modify: `tests/test_frontend_static.py`
- Modify: `README.md`

- [ ] Add static tests for `Save for Web Chat`, `/api/graph`, `ChatInputNode`, `ChatOutputNode`, and `api_key`.
- [ ] Update planner catalog and save behavior.
- [ ] Run all tests and JS syntax check.
- [ ] Commit.

