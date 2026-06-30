const nodeCatalog = [
  {
    type: "chat_input",
    className: "ChatInputNode",
    title: "Web Chat Input",
    description: "Reads the user's message from the web chat input.",
    inputs: [],
    outputs: ["text"],
    defaults: {},
  },
  {
    type: "openai",
    className: "OpenAIChatNode",
    title: "OpenAI Chat",
    description: "Consumes text and calls an OpenAI-compatible chat endpoint.",
    inputs: ["text"],
    outputs: ["text", "request", "response"],
    defaults: {
      base_url: "https://api.openai.com/v1",
      api_key: "",
      model: "gpt-4.1-mini",
    },
  },
  {
    type: "anthropic",
    className: "AnthropicMessagesNode",
    title: "Anthropic Messages",
    description: "Consumes text and calls the Anthropic Messages API.",
    inputs: ["text"],
    outputs: ["text", "request", "response"],
    defaults: {
      base_url: "https://api.anthropic.com/v1",
      api_key: "",
      model: "claude-sonnet-4-5",
    },
  },
  {
    type: "chat_output",
    className: "ChatOutputNode",
    title: "Web Chat Output",
    description: "Sends model text to the web chat message list.",
    inputs: ["text"],
    outputs: ["reply"],
    defaults: {},
  },
];

let graph = {nodes: [], edges: []};
let selectedId = null;
let pendingOutput = null;
let dragState = null;

const libraryEl = document.getElementById("node-library");
const canvasEl = document.getElementById("graph-canvas");
const nodeLayerEl = document.getElementById("node-layer");
const edgeLayerEl = document.getElementById("edge-layer");
const graphCountEl = document.getElementById("graph-count");
const pythonCodeEl = document.getElementById("python-code");
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

function addNode(type) {
  const spec = nodeCatalog.find((node) => node.type === type);
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
  pendingOutput = null;
  render();
}

function renderLibrary() {
  libraryEl.innerHTML = "";
  nodeCatalog.forEach((node) => {
    const card = document.createElement("article");
    card.className = "node-card";
    card.innerHTML = `
      <span class="node-type">${node.className}</span>
      <h3>${node.title}</h3>
      <p>${node.description}</p>
      <button type="button">Add node</button>
    `;
    card.querySelector("button").addEventListener("click", () => addNode(node.type));
    libraryEl.appendChild(card);
  });
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
      port.addEventListener("click", () => handlePortClick(port));
    });
    item.querySelectorAll("[data-prop-key]").forEach((input) => {
      input.addEventListener("input", (event) => updateProperty(node.id, event.target.dataset.propKey, event.target.value));
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
    const pending = pendingOutput && pendingOutput.nodeId === node.id && pendingOutput.port === port;
    return `
      <button
        type="button"
        class="port ${direction}${pending ? " pending" : ""}"
        data-node-id="${node.id}"
        data-port="${port}"
        data-direction="${direction}"
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
    <div class="node-properties">
      ${entries.map(([key, value]) => `
        <div class="field">
          <label>${key}</label>
          <input data-prop-key="${key}" value="${value}" ${key === "api_key" ? 'type="password"' : ""}>
        </div>
      `).join("")}
    </div>
  `;
}

function renderSelection() {
  document.querySelectorAll(".graph-node").forEach((node) => {
    node.classList.toggle("selected", node.dataset.nodeId === selectedId);
  });
}

function handlePortClick(port) {
  const nodeId = port.dataset.nodeId;
  const portName = port.dataset.port;
  const direction = port.dataset.direction;

  if (direction === "output") {
    pendingOutput = {nodeId, port: portName};
    renderCanvas();
    renderCode();
    return;
  }

  if (direction === "input" && pendingOutput) {
    addEdge(pendingOutput.nodeId, pendingOutput.port, nodeId, portName);
  }
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

function portCenter(nodeId, portName, direction) {
  const selector = `.port[data-node-id="${nodeId}"][data-port="${portName}"][data-direction="${direction}"]`;
  const port = nodeLayerEl.querySelector(selector);
  const canvasRect = canvasEl.getBoundingClientRect();
  const portRect = port.getBoundingClientRect();
  return {
    x: portRect.left - canvasRect.left + portRect.width / 2,
    y: portRect.top - canvasRect.top + portRect.height / 2,
  };
}

function renderEdges() {
  edgeLayerEl.querySelectorAll("path").forEach((path) => path.remove());
  graph.edges.forEach((edge) => {
    const from = portCenter(edge.from_node, edge.from_port, "output");
    const to = portCenter(edge.to_node, edge.to_port, "input");
    const curve = Math.max(60, Math.abs(to.x - from.x) / 2);
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${from.x} ${from.y} C ${from.x + curve} ${from.y}, ${to.x - curve} ${to.y}, ${to.x} ${to.y}`);
    path.setAttribute("marker-end", "url(#arrowhead)");
    edgeLayerEl.appendChild(path);
  });
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
  const response = await fetch(apiUrl("/api/graph"), {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(serializeGraph()),
  });
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

document.getElementById("reset-graph").addEventListener("click", () => {
  graph = {nodes: [], edges: []};
  selectedId = null;
  pendingOutput = null;
  render();
});

document.getElementById("copy-code").addEventListener("click", async () => {
  await navigator.clipboard.writeText(pythonCodeEl.textContent);
});

document.getElementById("save-graph").addEventListener("click", async () => {
  await saveGraph();
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

renderLibrary();
render();
setActiveView(activeViewFromHash());
