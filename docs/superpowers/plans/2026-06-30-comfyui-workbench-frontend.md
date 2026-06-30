# ComfyUI Workbench Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the existing single-page FlainBot frontend into a ComfyUI-inspired workbench with top-bar view switching, a searchable node shelf, a larger canvas, node-internal property editing, and a collapsed live Generated Python panel.

**Architecture:** Keep the current static frontend files and backend graph API. `frontend/index.html` defines the top-bar, Planner view, Chat view, node shelf, canvas, and result rail. `frontend/app.js` continues to own graph state, dynamic `/api/nodes` loading, rendering, saving, and chat requests. `frontend/styles.css` provides the workbench layout, node visuals, collapsed result panel, and responsive behavior.

**Tech Stack:** Static HTML, vanilla JavaScript, CSS, Python `unittest`, `node --check`.

---

### Task 1: Static Workbench Structure

**Files:**
- Modify: `tests/test_frontend_static.py`
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

- [x] **Step 1: Write failing static tests for the target shell**

Update `tests/test_frontend_static.py` so `test_planner_page_references_assets_and_nodes` asserts the ComfyUI workbench structure:

```python
self.assertIn("class=\"app-shell\"", html)
self.assertIn("class=\"workbench-topbar\"", html)
self.assertIn("data-route=\"planner\"", html)
self.assertIn("data-route=\"chat\"", html)
self.assertIn("id=\"node-search\"", html)
self.assertIn("id=\"result-panel\"", html)
self.assertIn("id=\"python-panel\"", html)
self.assertIn("details", html)
self.assertIn("Generated Python", html)
self.assertIn("node-properties", js)
```

Keep the existing assertions that standalone chat assets do not exist.

- [x] **Step 2: Verify the new test fails**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
```

Expected: failure because `app-shell`, `workbench-topbar`, `node-search`, and collapsed result panel markup are not present yet.

- [x] **Step 3: Implement the static HTML shell**

Change `frontend/index.html` to this structure while keeping the current element IDs used by JavaScript:

```html
<body>
  <div class="app-shell">
    <header class="workbench-topbar">
      <div class="brand">
        <h1>FlainBot</h1>
        <p id="status-message" class="status-message" role="status" aria-live="polite"></p>
      </div>
      <nav class="topbar-tabs" aria-label="Views">
        <button class="view-tab" data-route="planner" type="button">Planner</button>
        <button class="view-tab" data-route="chat" type="button">Chat</button>
      </nav>
      <div class="topbar-actions">
        <button id="save-graph" type="button">Save</button>
        <button id="reset-graph" type="button">Reset</button>
      </div>
    </header>

    <main>
      <section id="planner-view" class="view planner-workbench" data-view="planner">
        <aside class="node-shelf" aria-labelledby="library-title">
          <div class="shelf-header">
            <h2 id="library-title">Nodes</h2>
            <input id="node-search" type="search" autocomplete="off" placeholder="Search nodes">
          </div>
          <div id="node-library" class="node-list"></div>
        </aside>

        <section class="canvas-panel" aria-labelledby="graph-title">
          <div class="canvas-toolbar">
            <h2 id="graph-title">Planner</h2>
            <span id="graph-count" class="count">0 nodes</span>
          </div>
          <div id="graph-canvas" class="graph-canvas">
            <svg id="edge-layer" class="edge-layer">
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7"></polygon>
                </marker>
              </defs>
            </svg>
            <div id="node-layer" class="node-layer"></div>
          </div>
        </section>

        <aside id="result-panel" class="result-rail" aria-label="Results">
          <details id="python-panel" class="result-section">
            <summary>Generated Python</summary>
            <div class="result-actions">
              <button id="copy-code" type="button">Copy</button>
            </div>
            <pre><code id="python-code"></code></pre>
          </details>
        </aside>
      </section>

      <section id="chat-view" class="view chat-shell" data-view="chat" hidden>
        <!-- keep existing chat ids: messages, chat-form, message-input -->
      </section>
    </main>
  </div>
  <script src="app.js"></script>
</body>
```

The Chat section can reuse the current `chat-header`, `messages`, and `composer` markup inside the same `index.html`.

- [x] **Step 4: Add the minimum CSS for the shell**

Update `frontend/styles.css` with the workbench containers:

```css
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
}

.workbench-topbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto auto;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--panel-border);
  background: #ffffff;
}

.planner-workbench {
  display: grid;
  grid-template-columns: 280px minmax(520px, 1fr) 320px;
  gap: 12px;
  min-height: calc(100vh - 72px);
  padding: 12px;
}

.node-shelf,
.canvas-panel,
.result-rail {
  min-width: 0;
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  background: var(--panel);
}

.result-section > summary {
  cursor: pointer;
  padding: 12px;
}
```

- [x] **Step 5: Verify the static shell test passes**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
```

Expected: all tests in `tests.test_frontend_static` pass.

- [x] **Step 6: Commit**

Run:

```powershell
git add frontend/index.html frontend/styles.css tests/test_frontend_static.py
git commit -m "feat: add workbench frontend shell"
```

### Task 2: Node Shelf Search And Visual Grouping

**Files:**
- Modify: `tests/test_frontend_static.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [x] **Step 1: Write failing static tests for node shelf behavior**

Add assertions to `test_planner_page_references_assets_and_nodes`:

```python
self.assertIn("nodeSearchEl", js)
self.assertIn("filterNodeCatalog", js)
self.assertIn("node-group", js)
self.assertIn("categoryForNode", js)
self.assertIn("node-search", js)
```

- [x] **Step 2: Verify the new test fails**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
```

Expected: failure because search and grouping helpers do not exist yet.

- [x] **Step 3: Implement node shelf search and frontend-only groups**

In `frontend/app.js`, add:

```js
const nodeSearchEl = document.getElementById("node-search");

function categoryForNode(node) {
  if (node.type.includes("input")) return "Input";
  if (node.type.includes("prompt")) return "Prompt";
  if (node.type.includes("output")) return "Output";
  if (node.type === "openai" || node.type === "anthropic") return "Provider";
  return "Other";
}

function filterNodeCatalog() {
  const query = nodeSearchEl.value.trim().toLowerCase();
  return nodeCatalog.filter((node) => {
    const haystack = `${node.type} ${node.className} ${node.title} ${node.description}`.toLowerCase();
    return haystack.includes(query);
  });
}
```

Change `renderLibrary()` to group filtered nodes:

```js
function renderLibrary() {
  libraryEl.innerHTML = "";
  const grouped = new Map();
  filterNodeCatalog().forEach((node) => {
    const category = categoryForNode(node);
    if (!grouped.has(category)) grouped.set(category, []);
    grouped.get(category).push(node);
  });

  grouped.forEach((nodes, category) => {
    const group = document.createElement("section");
    group.className = "node-group";
    group.innerHTML = `<h3>${category}</h3>`;
    nodes.forEach((node) => group.appendChild(renderNodeCard(node)));
    libraryEl.appendChild(group);
  });
}

function renderNodeCard(node) {
  const card = document.createElement("article");
  card.className = "node-card";
  card.innerHTML = `
    <span class="node-type">${node.className}</span>
    <h4>${node.title}</h4>
    <p>${node.description}</p>
    <button type="button">Add node</button>
  `;
  card.querySelector("button").addEventListener("click", () => addNode(node.type));
  return card;
}
```

Add the listener:

```js
nodeSearchEl.addEventListener("input", renderLibrary);
```

- [x] **Step 4: Add shelf CSS**

Add CSS:

```css
.shelf-header {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-bottom: 1px solid var(--panel-border);
}

.shelf-header input {
  width: 100%;
  min-height: 34px;
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  padding: 6px 8px;
}

.node-group {
  display: grid;
  gap: 8px;
  padding: 12px;
}

.node-group h3 {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
}
```

- [x] **Step 5: Verify search and grouping checks pass**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
node --check frontend/app.js
```

Expected: frontend static tests pass and `node --check` exits 0.

- [x] **Step 6: Commit**

Run:

```powershell
git add frontend/app.js frontend/styles.css tests/test_frontend_static.py
git commit -m "feat: add searchable node shelf"
```

### Task 3: Result Rail With Collapsed Live Generated Python

**Files:**
- Modify: `tests/test_frontend_static.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [x] **Step 1: Write failing static tests for collapsed live output**

Add assertions:

```python
self.assertIn("id=\"python-panel\"", html)
self.assertIn("<summary>Generated Python</summary>", html)
self.assertNotIn("open", html.split("id=\"python-panel\"")[1].split(">")[0])
self.assertIn("renderCode()", js)
self.assertIn("updateProperty", js)
```

- [x] **Step 2: Verify the test fails if the panel is not collapsed**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
```

Expected: failure until the `details` panel exists without an `open` attribute.

- [x] **Step 3: Ensure graph changes refresh Generated Python**

Keep `renderCode()` inside `render()`. Ensure these paths call either `render()` or `renderCode()`:

```js
function addNode(type) {
  // after graph.nodes.push(...)
  render();
}

function removeNode(id) {
  // after graph mutation
  render();
}

function updateProperty(id, key, value) {
  // after node.props update
  renderCode();
}

function addEdge(fromNode, fromPort, toNode, toPort) {
  // after graph.edges.push(...)
  render();
}
```

This preserves live generated output without requiring a backend save.

- [x] **Step 4: Style the result rail as secondary**

Add:

```css
.result-rail {
  align-self: stretch;
  overflow: auto;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0 12px 12px;
}

.result-section pre {
  margin: 0 12px 12px;
  max-height: calc(100vh - 180px);
}
```

- [x] **Step 5: Verify**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
node --check frontend/app.js
```

Expected: tests pass and JS parses.

- [x] **Step 6: Commit**

Run:

```powershell
git add frontend/app.js frontend/styles.css tests/test_frontend_static.py
git commit -m "feat: add live generated output rail"
```

### Task 4: Canvas Pan And Zoom

**Files:**
- Modify: `tests/test_frontend_static.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [x] **Step 1: Write failing static tests for pan and zoom hooks**

Add assertions:

```python
self.assertIn("viewportState", js)
self.assertIn("applyViewportTransform", js)
self.assertIn("wheel", js)
self.assertIn("startCanvasPan", js)
self.assertIn("data-canvas-space", js)
```

- [x] **Step 2: Verify the test fails**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
```

Expected: failure because pan and zoom state does not exist.

- [x] **Step 3: Add a transform layer inside the canvas**

In `frontend/index.html`, wrap the edge and node layers:

```html
<div id="canvas-space" class="canvas-space" data-canvas-space>
  <svg id="edge-layer" class="edge-layer">...</svg>
  <div id="node-layer" class="node-layer"></div>
</div>
```

Update JS element lookup:

```js
const canvasSpaceEl = document.getElementById("canvas-space");
```

- [x] **Step 4: Implement minimal viewport state**

Add:

```js
let viewportState = {x: 0, y: 0, scale: 1};
let canvasPanState = null;

function applyViewportTransform() {
  canvasSpaceEl.style.transform = `translate(${viewportState.x}px, ${viewportState.y}px) scale(${viewportState.scale})`;
}

function zoomCanvas(event) {
  event.preventDefault();
  const delta = event.deltaY > 0 ? -0.08 : 0.08;
  viewportState.scale = Math.min(1.8, Math.max(0.45, viewportState.scale + delta));
  applyViewportTransform();
  renderEdges();
}

function startCanvasPan(event) {
  if (event.target.closest(".graph-node") || event.button !== 1) return;
  event.preventDefault();
  canvasPanState = {
    startX: event.clientX,
    startY: event.clientY,
    originX: viewportState.x,
    originY: viewportState.y,
  };
}

function moveCanvasPan(event) {
  if (!canvasPanState) return;
  viewportState.x = canvasPanState.originX + event.clientX - canvasPanState.startX;
  viewportState.y = canvasPanState.originY + event.clientY - canvasPanState.startY;
  applyViewportTransform();
}

function endCanvasPan() {
  canvasPanState = null;
}
```

Wire events:

```js
canvasEl.addEventListener("wheel", zoomCanvas, {passive: false});
canvasEl.addEventListener("pointerdown", startCanvasPan);
canvasEl.addEventListener("pointermove", moveCanvasPan);
canvasEl.addEventListener("pointerup", endCanvasPan);
canvasEl.addEventListener("pointercancel", endCanvasPan);
```

Keep existing node drag events intact.

- [x] **Step 5: Add transform CSS**

```css
.canvas-space {
  position: absolute;
  inset: 0;
  transform-origin: 0 0;
}
```

- [x] **Step 6: Verify**

Run:

```powershell
python -m unittest tests.test_frontend_static -v
node --check frontend/app.js
```

Expected: tests pass and JS parses.

- [x] **Step 7: Commit**

Run:

```powershell
git add frontend/index.html frontend/app.js frontend/styles.css tests/test_frontend_static.py
git commit -m "feat: add canvas pan and zoom"
```

### Task 5: Full Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-06-30-comfyui-workbench-frontend.md`

- [x] **Step 1: Run full test suite**

Run:

```powershell
python -m unittest -v
```

Expected: all tests pass.

- [x] **Step 2: Run syntax checks**

Run:

```powershell
node --check frontend/app.js
python -m py_compile scripts\web_chat.py src\flainbot\node_catalog.py
```

Expected: all commands exit 0.

- [x] **Step 3: Start the app for manual browser check**

Run:

```powershell
python start.py
```

Expected startup URL:

```text
FlainBot web chat: http://127.0.0.1:8765/
```

Manual checks:

- Planner and Chat switch from the top bar.
- Node shelf loads from `/api/nodes`.
- Searching `prompt` shows Prompt Builder.
- Node properties are editable inside the node.
- Generated Python is collapsed by default and updates after adding nodes or editing props.
- Save then Chat still routes through the existing graph backend.

- [x] **Step 4: Mark plan complete and commit**

Update this plan's checkboxes to `[x]` for completed tasks, then run:

```powershell
git add docs/superpowers/plans/2026-06-30-comfyui-workbench-frontend.md
git commit -m "docs: complete comfyui workbench plan"
```
