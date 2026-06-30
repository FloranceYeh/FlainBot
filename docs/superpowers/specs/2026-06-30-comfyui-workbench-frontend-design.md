# ComfyUI Workbench Frontend Design

## Goal

Refactor the current single-page FlainBot frontend into a ComfyUI-inspired workbench while preserving the existing graph JSON format and backend runtime.

## Scope

The frontend remains a single HTML application backed by `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`. The app can show multiple internal pages, but it must not reintroduce separate chat HTML, CSS, or JS files.

This refactor covers the Planner and Chat user experience only. It does not introduce formal node packages, nested node groups, minimaps, queue history, multi-select, or advanced graph commands.

## Layout

The top bar becomes the global workbench header. It contains the FlainBot identity, Planner and Chat view switching, save/reset actions, and a compact status message. Page switching happens in this top bar and controls internal views inside the same `index.html`.

The Planner view uses a three-zone workbench:

- Left node shelf: loads nodes from `/api/nodes`, supports search, and visually groups the currently flat node catalog into practical sections such as Input, Prompt, Provider, and Output. This grouping is frontend-only until the future node package/group model exists.
- Center canvas: uses a large grid workspace with graph nodes and curved edges. Nodes remain draggable and connectable. The first refactor should add basic pan and zoom so the canvas behaves more like a workbench.
- Right result rail: contains generated output and supporting runtime information. `Generated Python` is shown here, updates live when graph structure or node props change, and is collapsed by default. It can be expanded for viewing and copying.

The Chat view is a separate internal page selected from the top bar. It stays inside the single HTML app and focuses on testing the currently saved graph. It should not be embedded into the Planner result rail.

## Node Editing

Node property editing stays inside each graph node. A selected node should still be visually obvious, but the right rail must not become a primary property inspector.

Each node displays its title, class/type metadata, input and output ports, and editable properties. The existing form behavior for password fields and autocomplete stays intact.

## Data Flow

The frontend continues to load node metadata through `GET /api/nodes`. Adding a node copies the selected node spec into the graph state. Saving still sends the existing graph shape to `POST /api/graph`:

```json
{
  "nodes": [
    {"id": "node_1", "type": "prompt_builder", "props": {}, "x": 0, "y": 0}
  ],
  "edges": []
}
```

Chat still posts to `POST /api/chat`. The backend graph builder and runtime are unchanged.

Generated Python is derived from the in-memory graph and refreshes on graph changes. It does not require saving first.

## Error Handling

If `/api/nodes`, `/api/graph`, or `/api/chat` cannot be reached, the top bar status shows the same clear startup hint used today: start the server with `python start.py`.

If Chat is opened before a useful graph has been saved, the Chat page should show a concise status message rather than failing silently.

## Testing

Static frontend tests should verify the single-page structure, top-bar page switching, dynamic node catalog loading, collapsed Generated Python panel, node-internal property editing, and absence of standalone chat assets.

Backend tests should remain focused on graph persistence, `/api/nodes`, and chat execution. No backend graph schema change is expected for this refactor.
