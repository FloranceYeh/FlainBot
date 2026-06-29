# Static Node Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a zero-dependency browser page for viewing available nodes and planning a linear FlainBot pipeline.

**Architecture:** The page lives under `frontend/` and runs directly from `index.html`. `app.js` owns node catalog data, chain state, selection, editing, and Python code generation; `styles.css` owns the utilitarian planner layout.

**Tech Stack:** Plain HTML, CSS, JavaScript, Python `unittest` for static content checks.

---

### Task 1: Static Planner Page

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/app.js`
- Create: `tests/test_frontend_static.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing static test**

Create `tests/test_frontend_static.py` asserting the planner files exist and contain required UI/API markers:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendStaticTests(unittest.TestCase):
    def test_planner_page_references_assets_and_nodes(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

        self.assertIn("FlainBot Node Planner", html)
        self.assertIn("styles.css", html)
        self.assertIn("app.js", html)
        self.assertIn("OpenAIChatNode", js)
        self.assertIn("AnthropicMessagesNode", js)
        self.assertIn("generatePython", js)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_frontend_static -v`

Expected: FAIL because `frontend/index.html` does not exist.

- [ ] **Step 3: Implement static page**

Create the three frontend files. Required behavior:
- Node library with OpenAI, Anthropic, generic request, generic response nodes.
- Add-to-chain buttons.
- Chain list with select, move up, move down, remove.
- Property editor for selected node.
- Generated Python code updates after every state change.

- [ ] **Step 4: Update README**

Add a short section:

```markdown
## Node Planner

Open `frontend/index.html` in a browser to view nodes and plan a linear chain.
```

- [ ] **Step 5: Run verification**

Run: `python -m unittest -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/index.html frontend/styles.css frontend/app.js tests/test_frontend_static.py README.md docs/superpowers/plans/2026-06-29-static-node-planner.md
git commit -m "feat: add static node planner"
```

