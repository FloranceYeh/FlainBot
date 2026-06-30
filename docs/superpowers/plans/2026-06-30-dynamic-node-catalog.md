# Dynamic Node Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load planner node metadata dynamically from the backend instead of hard-coding the catalog in `frontend/app.js`.

**Architecture:** Move built-in node metadata into `src/flainbot/node_catalog.py`. Expose it through `GET /api/nodes`. The frontend starts with an empty catalog, fetches `/api/nodes`, then renders the library. Node package/group normalization remains out of scope for this step.

**Tech Stack:** Python standard library HTTP server, static browser JavaScript, `unittest`.

---

### Task 1: Backend Catalog API

**Files:**
- Create: `src/flainbot/node_catalog.py`
- Modify: `scripts/web_chat.py`
- Modify: `tests/test_web_chat.py`

- [x] Add tests for `GET /api/nodes` returning current built-in node specs.
- [x] Add a catalog module with `builtin_node_catalog()`.
- [x] Serve catalog JSON from `/api/nodes`.

### Task 2: Frontend Dynamic Loading

**Files:**
- Modify: `frontend/app.js`
- Modify: `tests/test_frontend_static.py`

- [x] Change `nodeCatalog` to an empty array.
- [x] Add `loadNodeCatalog()` using `apiUrl("/api/nodes")`.
- [x] Render the library only after catalog load.
- [x] Show a status error when catalog loading fails.

### Task 3: Verification And Commit

- [x] Run `python -m unittest -v`.
- [x] Run `python -m py_compile src/flainbot/node_catalog.py scripts/web_chat.py`.
- [x] Run `node --check frontend/app.js`.
- [x] Commit the scoped change.
