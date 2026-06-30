# Single HTML Dynamic Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the planner and chat UI run from one dynamic `frontend/index.html` shell instead of separate HTML pages.

**Architecture:** Keep the existing static HTML/CSS/JS stack. `index.html` owns both planner and chat sections, `app.js` switches views using the hash route, and the Python web server serves `index.html` as the default route like a small SPA.

**Tech Stack:** Static browser JavaScript, CSS, Python standard-library HTTP server, `unittest`.

---

### Task 1: Tests Define Single-HTML Behavior

**Files:**
- Modify: `tests/test_frontend_static.py`
- Modify: `tests/test_web_chat.py`

- [ ] Assert `frontend/index.html` contains both planner and chat UI markers.
- [ ] Assert `frontend/app.js` owns both `/api/graph` and `/api/chat` calls plus hash view switching.
- [ ] Assert standalone chat assets are absent.
- [ ] Assert `GET /` serves `index.html` content rather than `chat.html`.

### Task 2: Merge Chat Into Static Shell

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Delete: `frontend/chat.html`
- Delete: `frontend/chat.js`
- Delete: `frontend/chat.css`

- [ ] Add Planner and Chat navigation buttons.
- [ ] Move chat markup into `index.html`.
- [ ] Merge chat submit behavior into `app.js`.
- [ ] Merge chat CSS into `styles.css`.
- [ ] Switch views with `#planner` and `#chat`.

### Task 3: Server And Docs

**Files:**
- Modify: `scripts/web_chat.py`
- Modify: `README.md`

- [ ] Serve `index.html` for `/`.
- [ ] Preserve static asset serving and `/api/graph`, `/api/chat`.
- [ ] Update README so users open the single shell and use `#chat` for chat.

### Task 4: Verification

- [ ] Run `python -m unittest -v`.
- [ ] Run a JavaScript syntax check for `frontend/app.js`.
