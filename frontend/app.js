const nodeCatalog = [
  {
    type: "input",
    className: "InputNode",
    title: "Web Chat Input",
    description: "Reads the user's message from the web chat input.",
    inputs: [],
    outputs: ["text"],
    defaults: {
      text: "hello",
    },
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
      api_key_env: "OPENAI_API_KEY",
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
      api_key_env: "ANTHROPIC_API_KEY",
      model: "claude-sonnet-4-5",
    },
  },
  {
    type: "output",
    className: "OutputNode",
    title: "Web Chat Output",
    description: "Sends model text to the web chat message list.",
    inputs: ["text"],
    outputs: ["reply"],
    defaults: {},
  },
];

let graph = {nodes: [], edges: []};
let selectedId = null;

const libraryEl = document.getElementById("node-library");
const graphEl = document.getElementById("graph-list");
const graphCountEl = document.getElementById("graph-count");
const propertyEditorEl = document.getElementById("property-editor");
const pythonCodeEl = document.getElementById("python-code");

function nextId(type) {
  const count = graph.nodes.filter((node) => node.type === type).length + 1;
  return `${type}_${count}`;
}

function cloneDefaults(defaults) {
  return JSON.parse(JSON.stringify(defaults));
}

function addNode(type) {
  const spec = nodeCatalog.find((node) => node.type === type);
  const item = {
    id: nextId(spec.type),
    type: spec.type,
    className: spec.className,
    title: spec.title,
    description: spec.description,
    inputs: spec.inputs,
    outputs: spec.outputs,
    props: cloneDefaults(spec.defaults),
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
  renderGraph();
  renderCode();
}

function addEdge(fromNode, fromPort, toNode, toPort) {
  if (!fromNode || !fromPort || !toNode || !toPort || fromNode === toNode) {
    return;
  }
  graph.edges.push({from_node: fromNode, from_port: fromPort, to_node: toNode, to_port: toPort});
  render();
}

function removeEdge(index) {
  graph.edges.splice(index, 1);
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

function renderGraph() {
  graphEl.innerHTML = "";
  graphCountEl.textContent = `${graph.nodes.length} nodes / ${graph.edges.length} edges`;

  if (graph.nodes.length === 0) {
    graphEl.innerHTML = '<div class="empty-state">Add nodes from the library to plan a graph.</div>';
    return;
  }

  graph.nodes.forEach((node) => {
    const item = document.createElement("article");
    item.className = `graph-node${node.id === selectedId ? " selected" : ""}`;
    item.innerHTML = `
      <div>
        <span class="node-type">${node.id} / ${node.className}</span>
        <h3>${node.title}</h3>
        <p>${node.description}</p>
        <p>Inputs: ${node.inputs.join(", ") || "none"} / Outputs: ${node.outputs.join(", ") || "none"}</p>
      </div>
      <div class="graph-actions">
        <button type="button" data-action="select">Select</button>
        <button type="button" data-action="remove" class="danger">Remove</button>
      </div>
    `;
    item.querySelector('[data-action="select"]').addEventListener("click", () => {
      selectedId = node.id;
      render();
    });
    item.querySelector('[data-action="remove"]').addEventListener("click", () => removeNode(node.id));
    graphEl.appendChild(item);
  });

  renderEdgeBuilder();
  renderEdges();
}

function optionList(nodes, direction) {
  return nodes
    .filter((node) => direction === "from" ? node.outputs.length > 0 : node.inputs.length > 0)
    .map((node) => `<option value="${node.id}">${node.id}</option>`)
    .join("");
}

function renderEdgeBuilder() {
  const builder = document.createElement("article");
  builder.className = "node-card";
  builder.innerHTML = `
    <h3>Connect Ports</h3>
    <div class="field">
      <label>From node</label>
      <select id="from-node">${optionList(graph.nodes, "from")}</select>
    </div>
    <div class="field">
      <label>From port</label>
      <select id="from-port"></select>
    </div>
    <div class="field">
      <label>To node</label>
      <select id="to-node">${optionList(graph.nodes, "to")}</select>
    </div>
    <div class="field">
      <label>To port</label>
      <select id="to-port"></select>
    </div>
    <button type="button">Connect</button>
  `;

  const fromNode = builder.querySelector("#from-node");
  const fromPort = builder.querySelector("#from-port");
  const toNode = builder.querySelector("#to-node");
  const toPort = builder.querySelector("#to-port");

  function syncPorts() {
    const source = graph.nodes.find((node) => node.id === fromNode.value);
    const target = graph.nodes.find((node) => node.id === toNode.value);
    fromPort.innerHTML = (source?.outputs ?? []).map((port) => `<option value="${port}">${port}</option>`).join("");
    toPort.innerHTML = (target?.inputs ?? []).map((port) => `<option value="${port}">${port}</option>`).join("");
  }

  fromNode.addEventListener("change", syncPorts);
  toNode.addEventListener("change", syncPorts);
  builder.querySelector("button").addEventListener("click", () => {
    addEdge(fromNode.value, fromPort.value, toNode.value, toPort.value);
  });
  syncPorts();
  graphEl.appendChild(builder);
}

function renderEdges() {
  const list = document.createElement("div");
  list.className = "node-list";
  graph.edges.forEach((edge, index) => {
    const item = document.createElement("article");
    item.className = "graph-node";
    item.innerHTML = `
      <div>
        <span class="node-type">Edge ${index + 1}</span>
        <h3>${edge.from_node}.${edge.from_port} -> ${edge.to_node}.${edge.to_port}</h3>
      </div>
      <div class="graph-actions">
        <button type="button" class="danger">Remove</button>
      </div>
    `;
    item.querySelector("button").addEventListener("click", () => removeEdge(index));
    list.appendChild(item);
  });
  graphEl.appendChild(list);
}

function renderProperties() {
  propertyEditorEl.innerHTML = "";
  const selected = graph.nodes.find((node) => node.id === selectedId);
  if (!selected) {
    propertyEditorEl.innerHTML = '<div class="empty-state">Select a node to edit its properties.</div>';
    return;
  }

  const title = document.createElement("div");
  title.innerHTML = `<strong>${selected.className}</strong>`;
  propertyEditorEl.appendChild(title);

  const entries = Object.entries(selected.props);
  if (entries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "This node has no editable properties.";
    propertyEditorEl.appendChild(empty);
    return;
  }

  entries.forEach(([key, value]) => {
    const field = document.createElement("div");
    field.className = "field";
    field.innerHTML = `
      <label for="${selected.id}-${key}">${key}</label>
      <input id="${selected.id}-${key}" value="${value}">
    `;
    field.querySelector("input").addEventListener("input", (event) => {
      updateProperty(selected.id, key, event.target.value);
    });
    propertyEditorEl.appendChild(field);
  });
}

function quote(value) {
  return JSON.stringify(value);
}

function nodeToPython(node) {
  if (node.type === "input") {
    return `graph.add_node(${quote(node.id)}, InputNode(${quote(node.props.text)}))`;
  }

  if (node.type === "openai" || node.type === "anthropic") {
    return `graph.add_node(${quote(node.id)}, ${node.className}(\n` +
      `    base_url=${quote(node.props.base_url)},\n` +
      `    api_key=os.environ[${quote(node.props.api_key_env)}],\n` +
      `    model=${quote(node.props.model)},\n` +
      "))";
  }

  return `graph.add_node(${quote(node.id)}, OutputNode())`;
}

function generatePython() {
  const imports = new Set(["Graph", "GraphExecutor"]);
  graph.nodes.forEach((node) => imports.add(node.className));
  const needsOs = graph.nodes.some((node) => node.props.api_key_env);
  const importLine = `from flainbot import ${Array.from(imports).sort().join(", ")}`;
  const nodeLines = graph.nodes.length > 0 ? graph.nodes.map(nodeToPython).join("\n") : "# Add nodes in the planner";
  const edgeLines = graph.edges.map((edge) => (
    `graph.connect(${quote(edge.from_node)}, ${quote(edge.from_port)}, ${quote(edge.to_node)}, ${quote(edge.to_port)})`
  )).join("\n");

  return `${needsOs ? "import os\n\n" : ""}${importLine}\n\n\ngraph = Graph()\n${nodeLines}\n${edgeLines ? `${edgeLines}\n` : ""}outputs = GraphExecutor(graph).run()\nprint(outputs)\n`;
}

function renderCode() {
  pythonCodeEl.textContent = generatePython();
}

function render() {
  renderGraph();
  renderProperties();
  renderCode();
}

document.getElementById("reset-graph").addEventListener("click", () => {
  graph = {nodes: [], edges: []};
  selectedId = null;
  render();
});

document.getElementById("copy-code").addEventListener("click", async () => {
  await navigator.clipboard.writeText(pythonCodeEl.textContent);
});

renderLibrary();
render();
