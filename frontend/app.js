const nodeCatalog = [
  {
    type: "openai",
    className: "OpenAIChatNode",
    title: "OpenAI Chat",
    description: "Calls an OpenAI-compatible chat completions endpoint.",
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
    description: "Calls the Anthropic Messages API endpoint.",
    defaults: {
      base_url: "https://api.anthropic.com/v1",
      api_key_env: "ANTHROPIC_API_KEY",
      model: "claude-sonnet-4-5",
    },
  },
  {
    type: "request",
    className: "RequestNode",
    title: "Generic Request",
    description: "Builds a request object and calls an injected client.",
    defaults: {
      client_name: "client",
    },
  },
  {
    type: "response",
    className: "ResponseNode",
    title: "Generic Response",
    description: "Reads a generic response and writes context.output_text.",
    defaults: {},
  },
];

let chain = [];
let selectedId = null;

const libraryEl = document.getElementById("node-library");
const chainEl = document.getElementById("chain-list");
const chainCountEl = document.getElementById("chain-count");
const propertyEditorEl = document.getElementById("property-editor");
const pythonCodeEl = document.getElementById("python-code");

function nextId() {
  return `node-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function cloneDefaults(defaults) {
  return JSON.parse(JSON.stringify(defaults));
}

function addNode(type) {
  const spec = nodeCatalog.find((node) => node.type === type);
  const item = {
    id: nextId(),
    type: spec.type,
    className: spec.className,
    title: spec.title,
    description: spec.description,
    props: cloneDefaults(spec.defaults),
  };
  chain.push(item);
  selectedId = item.id;
  render();
}

function moveNode(id, direction) {
  const index = chain.findIndex((node) => node.id === id);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= chain.length) {
    return;
  }
  const [node] = chain.splice(index, 1);
  chain.splice(target, 0, node);
  render();
}

function removeNode(id) {
  chain = chain.filter((node) => node.id !== id);
  if (selectedId === id) {
    selectedId = chain[0]?.id ?? null;
  }
  render();
}

function updateProperty(id, key, value) {
  const node = chain.find((item) => item.id === id);
  if (!node) {
    return;
  }
  node.props[key] = value;
  renderChain();
  renderCode();
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

function renderChain() {
  chainEl.innerHTML = "";
  chainCountEl.textContent = `${chain.length} ${chain.length === 1 ? "node" : "nodes"}`;

  if (chain.length === 0) {
    chainEl.innerHTML = '<div class="empty-state">Add nodes from the library to plan a chain.</div>';
    return;
  }

  chain.forEach((node, index) => {
    const item = document.createElement("article");
    item.className = `chain-node${node.id === selectedId ? " selected" : ""}`;
    item.innerHTML = `
      <div>
        <span class="node-type">Step ${index + 1} · ${node.className}</span>
        <h3>${node.title}</h3>
        <p>${node.description}</p>
      </div>
      <div class="chain-actions">
        <button type="button" data-action="select">Select</button>
        <button type="button" data-action="up">Up</button>
        <button type="button" data-action="down">Down</button>
        <button type="button" data-action="remove" class="danger">Remove</button>
      </div>
    `;
    item.querySelector('[data-action="select"]').addEventListener("click", () => {
      selectedId = node.id;
      render();
    });
    item.querySelector('[data-action="up"]').addEventListener("click", () => moveNode(node.id, -1));
    item.querySelector('[data-action="down"]').addEventListener("click", () => moveNode(node.id, 1));
    item.querySelector('[data-action="remove"]').addEventListener("click", () => removeNode(node.id));
    chainEl.appendChild(item);
  });
}

function renderProperties() {
  propertyEditorEl.innerHTML = "";
  const selected = chain.find((node) => node.id === selectedId);
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
  if (node.type === "openai" || node.type === "anthropic") {
    return `    ${node.className}(\n` +
      `        base_url=${quote(node.props.base_url)},\n` +
      `        api_key=os.environ[${quote(node.props.api_key_env)}],\n` +
      `        model=${quote(node.props.model)},\n` +
      "    )";
  }

  if (node.type === "request") {
    return `    RequestNode(client=${node.props.client_name})`;
  }

  return "    ResponseNode()";
}

function generatePython() {
  const imports = new Set(["MessageContext", "Pipeline"]);
  chain.forEach((node) => imports.add(node.className));
  const needsOs = chain.some((node) => node.props.api_key_env);
  const importLine = `from flainbot import ${Array.from(imports).sort().join(", ")}`;
  const nodeLines = chain.length > 0 ? chain.map(nodeToPython).join(",\n") : "    # Add nodes in the planner";

  return `${needsOs ? "import os\n\n" : ""}${importLine}\n\n\npipeline = Pipeline([\n${nodeLines}\n])\ncontext = pipeline.run(MessageContext(input_text=\"hello\"))\nprint(context.output_text)\n`;
}

function renderCode() {
  pythonCodeEl.textContent = generatePython();
}

function render() {
  renderChain();
  renderProperties();
  renderCode();
}

document.getElementById("reset-chain").addEventListener("click", () => {
  chain = [];
  selectedId = null;
  render();
});

document.getElementById("copy-code").addEventListener("click", async () => {
  await navigator.clipboard.writeText(pythonCodeEl.textContent);
});

renderLibrary();
render();

