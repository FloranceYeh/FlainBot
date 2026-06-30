let nodeCatalog = [];
let graph = {nodes: [], edges: []};
let selectedId = null;
let connectionDrag = null;
let dragState = null;
let viewportState = {x: 0, y: 0, scale: 1};
let canvasPanState = null;
let resultRailCollapsed = true;

const libraryEl = document.getElementById("node-library");
const nodeSearchEl = document.getElementById("node-search");
const canvasEl = document.getElementById("graph-canvas");
const canvasSpaceEl = document.getElementById("canvas-space");
const nodeLayerEl = document.getElementById("node-layer");
const edgeLayerEl = document.getElementById("edge-layer");
const graphCountEl = document.getElementById("graph-count");
const pythonCodeEl = document.getElementById("python-code");
const resultPanelEl = document.getElementById("result-panel");
const resultPanelToggleEl = document.getElementById("toggle-result-panel");
const plannerViewEl = document.getElementById("planner-view");
const statusMessageEl = document.getElementById("status-message");
const viewEls = document.querySelectorAll("[data-view]");
const viewTabEls = document.querySelectorAll("[data-route]");
const chatFormEl = document.getElementById("chat-form");
const messageInputEl = document.getElementById("message-input");
const messagesEl = document.getElementById("messages");

function defaultApiBaseUrl() {
  if (window.location.protocol === "file:" || window.location.port === "5500") {
    return "http://127.0.0.1:8765";
  }
  return "";
}

const apiBaseUrl = window.FLAINBOT_API_BASE_URL || defaultApiBaseUrl();

function apiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

function nextId(type) {
  const count = graph.nodes.filter((node) => node.type === type).length + 1;
  return `${type}_${count}`;
}

function cloneDefaults(defaults) {
  return JSON.parse(JSON.stringify(defaults));
}

async function loadNodeCatalog() {
  let response;
  try {
    response = await fetch(apiUrl("/api/nodes"));
  } catch (error) {
    throw new Error("Could not load node catalog. Start server with: python start.py");
  }
  if (!response.ok) {
    throw new Error(`Could not load node catalog: ${response.status}`);
  }
  nodeCatalog = await response.json();
}

function addNode(type) {
  const spec = nodeCatalog.find((node) => node.type === type);
  if (!spec) {
    setStatus(`Unknown node type: ${type}`, "error");
    return;
  }
  const offset = graph.nodes.length * 28;
  const item = {
    id: nextId(spec.type),
    type: spec.type,
    className: spec.className,
    title: spec.title,
    description: spec.description,
    inputs: spec.inputs,
    outputs: spec.outputs,
    props: cloneDefaults(spec.defaults),
    x: 48 + offset,
    y: 48 + offset,
  };
  graph.nodes.push(item);
  selectedId = item.id;
  render();
}

function removeNode(id) {
  graph.nodes = graph.nodes.filter((node) => node.id !== id);
  graph.edges = graph.edges.filter((edge) => edge.from_node !== id && edge.to_node !== id);
  if (selectedId === id) {
    selectedId = graph.nodes[0]?.id ?? null;
  }
  render();
}

function updateProperty(id, key, value) {
  const node = graph.nodes.find((item) => item.id === id);
  if (!node) {
    return;
  }
  node.props[key] = value;
  renderCode();
}

function addEdge(fromNode, fromPort, toNode, toPort) {
  if (!fromNode || !fromPort || !toNode || !toPort || fromNode === toNode) {
    return;
  }
  graph.edges.push({from_node: fromNode, from_port: fromPort, to_node: toNode, to_port: toPort});
  render();
}

function categoryForNode(node) {
  if (node.type.includes("input")) {
    return "Input";
  }
  if (node.type.includes("prompt")) {
    return "Prompt";
  }
  if (node.type.includes("output")) {
    return "Output";
  }
  if (node.type === "openai" || node.type === "anthropic") {
    return "Provider";
  }
  return "Other";
}

function filterNodeCatalog() {
  const query = nodeSearchEl.value.trim().toLowerCase();
  return nodeCatalog.filter((node) => {
    const haystack = `${node.type} ${node.className} ${node.title} ${node.description}`.toLowerCase();
    return haystack.includes(query);
  });
}

function renderLibrary() {
  libraryEl.innerHTML = "";
  const grouped = new Map();
  filterNodeCatalog().forEach((node) => {
    const category = categoryForNode(node);
    if (!grouped.has(category)) {
      grouped.set(category, []);
    }
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

function renderCanvas() {
  nodeLayerEl.innerHTML = "";
  graphCountEl.textContent = `${graph.nodes.length} nodes / ${graph.edges.length} edges`;

  graph.nodes.forEach((node) => {
    const item = document.createElement("article");
    item.className = `graph-node${node.id === selectedId ? " selected" : ""}`;
    item.style.left = `${node.x}px`;
    item.style.top = `${node.y}px`;
    item.dataset.nodeId = node.id;
    item.innerHTML = `
      <div class="node-header" data-drag-handle="true">
        <span class="node-type">${node.id} / ${node.className}</span>
        <h3>${node.title}</h3>
      </div>
      <div class="node-body">
        <div class="ports">
          <div class="port-column">
            <span class="port-title">Inputs</span>
            ${renderPorts(node, "input")}
          </div>
          <div class="port-column">
            <span class="port-title">Outputs</span>
            ${renderPorts(node, "output")}
          </div>
        </div>
        ${renderProperties(node)}
        <div class="node-actions">
          <button type="button" class="danger" data-action="remove">Remove</button>
        </div>
      </div>
    `;
    item.querySelector(".node-header").addEventListener("pointerdown", (event) => startDrag(event, node.id));
    item.querySelector('[data-action="remove"]').addEventListener("click", () => removeNode(node.id));
    item.querySelectorAll(".port").forEach((port) => {
      port.addEventListener("pointerdown", startConnectionDrag);
    });
    item.querySelectorAll("[data-prop-key]").forEach((input) => {
      input.addEventListener("input", (event) => updateProperty(node.id, event.target.dataset.propKey, event.target.value));
    });
    item.querySelectorAll(".node-properties").forEach((form) => {
      form.addEventListener("submit", (event) => event.preventDefault());
    });
    item.addEventListener("pointerdown", () => {
      selectedId = node.id;
      renderSelection();
    });
    nodeLayerEl.appendChild(item);
  });

  renderEdges();
}

function renderPorts(node, direction) {
  const ports = direction === "input" ? node.inputs : node.outputs;
  if (ports.length === 0) {
    return '<span class="node-type">none</span>';
  }
  return ports.map((port) => {
    return `
      <button
        type="button"
        class="port ${direction}"
        data-node-id="${node.id}"
        data-port="${port}"
        data-direction="${direction}"
        data-compatible="false"
      >${port}</button>
    `;
  }).join("");
}

function renderProperties(node) {
  const entries = Object.entries(node.props);
  if (entries.length === 0) {
    return "";
  }

  return `
    <form class="node-properties" autocomplete="off">
      ${entries.map(([key, value]) => `
        <div class="field">
          <label>${key}</label>
          <input data-prop-key="${key}" value="${value}" ${key === "api_key" ? 'type="password"' : ""}>
        </div>
      `).join("")}
    </form>
  `;
}

function renderSelection() {
  document.querySelectorAll(".graph-node").forEach((node) => {
    node.classList.toggle("selected", node.dataset.nodeId === selectedId);
  });
}

function startDrag(event, nodeId) {
  event.preventDefault();
  const node = graph.nodes.find((item) => item.id === nodeId);
  selectedId = nodeId;
  dragState = {
    nodeId,
    startX: event.clientX,
    startY: event.clientY,
    originX: node.x,
    originY: node.y,
  };
  event.currentTarget.setPointerCapture(event.pointerId);
}

function dragMove(event) {
  if (!dragState) {
    return;
  }
  const node = graph.nodes.find((item) => item.id === dragState.nodeId);
  node.x = Math.max(0, dragState.originX + event.clientX - dragState.startX);
  node.y = Math.max(0, dragState.originY + event.clientY - dragState.startY);
  const element = nodeLayerEl.querySelector(`[data-node-id="${node.id}"]`);
  element.style.left = `${node.x}px`;
  element.style.top = `${node.y}px`;
  renderEdges();
}

function dragEnd() {
  dragState = null;
}

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
  if (event.target.closest(".graph-node") || event.button !== 1) {
    return;
  }
  event.preventDefault();
  canvasPanState = {
    startX: event.clientX,
    startY: event.clientY,
    originX: viewportState.x,
    originY: viewportState.y,
  };
}

function moveCanvasPan(event) {
  if (!canvasPanState) {
    return;
  }
  viewportState.x = canvasPanState.originX + event.clientX - canvasPanState.startX;
  viewportState.y = canvasPanState.originY + event.clientY - canvasPanState.startY;
  applyViewportTransform();
}

function endCanvasPan() {
  canvasPanState = null;
}

function canvasPointFromEvent(event) {
  const canvasRect = canvasEl.getBoundingClientRect();
  return {
    x: (event.clientX - canvasRect.left - viewportState.x) / viewportState.scale,
    y: (event.clientY - canvasRect.top - viewportState.y) / viewportState.scale,
  };
}

function portCenter(nodeId, portName, direction) {
  const selector = `.port[data-node-id="${nodeId}"][data-port="${portName}"][data-direction="${direction}"]`;
  const port = nodeLayerEl.querySelector(selector);
  const canvasRect = canvasEl.getBoundingClientRect();
  const portRect = port.getBoundingClientRect();
  return {
    x: (portRect.left - canvasRect.left + portRect.width / 2 - viewportState.x) / viewportState.scale,
    y: (portRect.top - canvasRect.top + portRect.height / 2 - viewportState.y) / viewportState.scale,
  };
}

function connectionPath(from, to) {
  const curve = Math.max(60, Math.abs(to.x - from.x) / 2);
  return `M ${from.x} ${from.y} C ${from.x + curve} ${from.y}, ${to.x - curve} ${to.y}, ${to.x} ${to.y}`;
}

function clearConnectionPreview() {
  edgeLayerEl.querySelectorAll(".preview-connection").forEach((path) => path.remove());
  nodeLayerEl.querySelectorAll(".port").forEach((port) => {
    port.classList.remove("compatible");
    port.dataset.compatible = "false";
  });
}

function isCompatiblePort(port) {
  if (!connectionDrag || !port) {
    return false;
  }
  return port.dataset.nodeId !== connectionDrag.nodeId && port.dataset.direction !== connectionDrag.direction;
}

function startConnectionDrag(event) {
  const port = event.currentTarget;
  event.preventDefault();
  event.stopPropagation();
  connectionDrag = {
    nodeId: port.dataset.nodeId,
    port: port.dataset.port,
    direction: port.dataset.direction,
    start: portCenter(port.dataset.nodeId, port.dataset.port, port.dataset.direction),
    current: canvasPointFromEvent(event),
  };
  port.setPointerCapture(event.pointerId);
  nodeLayerEl.querySelectorAll(".port").forEach((candidate) => {
    const compatible = isCompatiblePort(candidate);
    candidate.classList.toggle("compatible", compatible);
    candidate.dataset.compatible = compatible ? "true" : "false";
  });
  renderConnectionPreview();
}

function renderConnectionPreview() {
  if (!connectionDrag) {
    return;
  }
  edgeLayerEl.querySelectorAll(".preview-connection").forEach((path) => path.remove());
  const from = connectionDrag.direction === "output" ? connectionDrag.start : connectionDrag.current;
  const to = connectionDrag.direction === "output" ? connectionDrag.current : connectionDrag.start;
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.classList.add("preview-connection");
  path.setAttribute("d", connectionPath(from, to));
  edgeLayerEl.appendChild(path);
}

function moveConnectionDrag(event) {
  if (!connectionDrag) {
    return;
  }
  connectionDrag.current = canvasPointFromEvent(event);
  renderConnectionPreview();
}

function finishConnectionDrag(event) {
  if (!connectionDrag) {
    return;
  }
  const target = document.elementFromPoint(event.clientX, event.clientY)?.closest(".port");
  if (isCompatiblePort(target)) {
    const from = connectionDrag.direction === "output" ? connectionDrag : target.dataset;
    const to = connectionDrag.direction === "output" ? target.dataset : connectionDrag;
    addEdge(from.nodeId, from.port, to.nodeId, to.port);
  }
  connectionDrag = null;
  clearConnectionPreview();
}

function renderEdges() {
  edgeLayerEl.querySelectorAll("path").forEach((path) => path.remove());
  graph.edges.forEach((edge) => {
    const from = portCenter(edge.from_node, edge.from_port, "output");
    const to = portCenter(edge.to_node, edge.to_port, "input");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", connectionPath(from, to));
    path.setAttribute("marker-end", "url(#arrowhead)");
    edgeLayerEl.appendChild(path);
  });
  renderConnectionPreview();
}

function quote(value) {
  return JSON.stringify(value);
}

function nodeToPython(node) {
  if (node.type === "chat_input") {
    return `graph.add_node(${quote(node.id)}, ChatInputNode("message from web chat"))`;
  }

  if (node.type === "openai" || node.type === "anthropic") {
    return `graph.add_node(${quote(node.id)}, ${node.className}(\n` +
      `    base_url=${quote(node.props.base_url)},\n` +
      `    api_key=${quote(node.props.api_key)},\n` +
      `    model=${quote(node.props.model)},\n` +
      "))";
  }

  if (node.type === "prompt_builder") {
    return `graph.add_node(${quote(node.id)}, PromptBuilderNode(\n` +
      `    system_prompt=${quote(node.props.system_prompt)},\n` +
      `    user_prompt=${quote(node.props.user_prompt)},\n` +
      `    tools_json=${quote(node.props.tools_json)},\n` +
      `    context_json=${quote(node.props.context_json)},\n` +
      "))";
  }

  return `graph.add_node(${quote(node.id)}, ChatOutputNode())`;
}

function generatePython() {
  const imports = new Set(["Graph", "GraphExecutor"]);
  graph.nodes.forEach((node) => imports.add(node.className));
  const importLine = `from flainbot import ${Array.from(imports).sort().join(", ")}`;
  const nodeLines = graph.nodes.length > 0 ? graph.nodes.map(nodeToPython).join("\n") : "# Add nodes in the planner";
  const edgeLines = graph.edges.map((edge) => (
    `graph.connect(${quote(edge.from_node)}, ${quote(edge.from_port)}, ${quote(edge.to_node)}, ${quote(edge.to_port)})`
  )).join("\n");

  return `${importLine}\n\n\ngraph = Graph()\n${nodeLines}\n${edgeLines ? `${edgeLines}\n` : ""}outputs = GraphExecutor(graph).run()\nprint(outputs)\n`;
}

function renderCode() {
  pythonCodeEl.textContent = generatePython();
}

function setStatus(message, type = "") {
  statusMessageEl.textContent = message;
  statusMessageEl.className = `status-message${type ? ` ${type}` : ""}`;
}

function renderPlannerLayout() {
  resultPanelEl.className = resultRailCollapsed ? "result-rail collapsed" : "result-rail";
  plannerViewEl.classList.toggle("result-collapsed", resultRailCollapsed);
  resultPanelToggleEl.setAttribute("aria-expanded", resultRailCollapsed ? "false" : "true");
}

function toggleResultPanel() {
  resultRailCollapsed = !resultRailCollapsed;
  renderPlannerLayout();
  requestAnimationFrame(renderEdges);
}

function serializeGraph() {
  return {
    nodes: graph.nodes.map((node) => ({
      id: node.id,
      type: node.type,
      props: node.props,
      x: node.x,
      y: node.y,
    })),
    edges: graph.edges,
  };
}

async function saveGraph() {
  let response;
  try {
    response = await fetch(apiUrl("/api/graph"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(serializeGraph()),
    });
  } catch (error) {
    throw new Error("Could not reach FlainBot server. Start it with: python start.py");
  }
  if (!response.ok) {
    throw new Error(`save failed: ${response.status}`);
  }
}

function activeViewFromHash() {
  return window.location.hash === "#chat" ? "chat" : "planner";
}

function setActiveView(view) {
  viewEls.forEach((element) => {
    element.hidden = element.dataset.view !== view;
  });
  viewTabEls.forEach((button) => {
    const active = button.dataset.route === view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });

  if (view === "planner") {
    requestAnimationFrame(renderEdges);
  }
}

function navigateToView(view) {
  const hash = view === "chat" ? "#chat" : "#planner";
  if (window.location.hash === hash) {
    setActiveView(view);
    return;
  }
  window.location.hash = hash;
}

function appendMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;
  messagesEl.appendChild(item);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendChatMessage(message) {
  const response = await fetch(apiUrl("/api/chat"), {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({message}),
  });
  if (!response.ok) {
    throw new Error(`chat failed: ${response.status}`);
  }
  return response.json();
}

function render() {
  renderCanvas();
  renderCode();
}

async function init() {
  try {
    await loadNodeCatalog();
    renderLibrary();
  } catch (error) {
    setStatus(error.message, "error");
  }

  render();
  renderPlannerLayout();
  setActiveView(activeViewFromHash());
}

document.getElementById("reset-graph").addEventListener("click", () => {
  graph = {nodes: [], edges: []};
  selectedId = null;
  connectionDrag = null;
  render();
});

nodeSearchEl.addEventListener("input", renderLibrary);
resultPanelToggleEl.addEventListener("click", toggleResultPanel);

document.getElementById("copy-code").addEventListener("click", async () => {
  await navigator.clipboard.writeText(pythonCodeEl.textContent);
});

document.getElementById("save-graph").addEventListener("click", async () => {
  setStatus("Saving graph...");
  try {
    await saveGraph();
    setStatus("Graph saved for Web Chat.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

viewTabEls.forEach((button) => {
  button.addEventListener("click", () => navigateToView(button.dataset.route));
});

window.addEventListener("hashchange", () => setActiveView(activeViewFromHash()));

chatFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInputEl.value.trim();
  if (!message) {
    return;
  }

  messageInputEl.value = "";
  appendMessage("user", message);

  try {
    const payload = await sendChatMessage(message);
    appendMessage("assistant", payload.reply);
  } catch (error) {
    appendMessage("assistant", `Request failed: ${error.message}`);
  }
});

canvasEl.addEventListener("pointermove", dragMove);
canvasEl.addEventListener("pointerup", dragEnd);
canvasEl.addEventListener("pointercancel", dragEnd);
canvasEl.addEventListener("pointermove", moveConnectionDrag);
canvasEl.addEventListener("pointerup", finishConnectionDrag);
canvasEl.addEventListener("pointercancel", finishConnectionDrag);
canvasEl.addEventListener("wheel", zoomCanvas, {passive: false});
canvasEl.addEventListener("pointerdown", startCanvasPan);
canvasEl.addEventListener("pointermove", moveCanvasPan);
canvasEl.addEventListener("pointerup", endCanvasPan);
canvasEl.addEventListener("pointercancel", endCanvasPan);

init();
