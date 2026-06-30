const fs = require("fs");
const vm = require("vm");

const appJs = fs.readFileSync("frontend/app.js", "utf8");

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id,
      value: "",
      innerHTML: "",
      textContent: "",
      checked: false,
      type: "",
      className: "",
      classList: {toggle() {}, remove() {}, add() {}},
      dataset: {},
      style: {},
      eventListeners: {},
      appendChild() {},
      addEventListener(eventName, callback) {
        this.eventListeners[eventName] = callback;
      },
      setAttribute() {},
      querySelector() { return element(`${id}-child`); },
      querySelectorAll(selector) {
        if (selector !== "input:checked") {
          return [];
        }
        return Array.from(elements.values()).filter((item) => (
          item.id.startsWith(`${id}-`) && item.checked
        ));
      },
    });
  }
  return elements.get(id);
}

const documentStub = {
  getElementById: element,
  querySelectorAll() { return []; },
  createElement() { return element(`created-${elements.size}`); },
  createElementNS() { return element(`created-ns-${elements.size}`); },
};

const context = {
  document: documentStub,
  window: {
    location: {protocol: "http:", port: "8765", hash: ""},
    addEventListener() {},
  },
  navigator: {clipboard: {writeText() {}}},
  requestAnimationFrame(callback) { callback(); },
  fetch() { return Promise.resolve({ok: true, json: () => Promise.resolve([])}); },
  FormData: class FormData {},
  console,
};

vm.createContext(context);
vm.runInContext(
  `${appJs}\nthis.__testApi = {collectCatalogNodes, flattenNodeCatalog, filterNodeCatalog, renderNodeFilters, renderNodeCard};`,
  context,
);

const catalog = [
  {
    kind: "package",
    id: "core",
    title: "Core",
    description: "Built-in nodes",
    items: [
      {
        kind: "node",
        package: "core",
        type: "prompt_builder",
        className: "PromptBuilderNode",
        title: "Prompt Builder",
        description: "Builds prompts",
        inputs: [{name: "tools", type: "json"}],
        outputs: [{name: "json", type: "json"}],
        defaults: {},
      },
    ],
  },
  {
    kind: "package",
    id: "media",
    title: "Media",
    description: "Media nodes",
    items: [
      {
        kind: "node",
        package: "media",
        type: "image_loader",
        className: "ImageLoaderNode",
        title: "Image Loader",
        description: "Loads images",
        inputs: [],
        outputs: [{name: "image", type: "image"}],
        defaults: {},
      },
    ],
  },
];

vm.runInContext(
  `nodeCatalog = ${JSON.stringify(catalog)}; flatNodeCatalog = flattenNodeCatalog(nodeCatalog);`,
  context,
);
context.__testApi.renderNodeFilters();

element("package-filter-options-media").value = "media";
element("package-filter-options-media").checked = true;
let filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 1 || filtered[0].id !== "media") {
  throw new Error("package filter should keep only matching package nodes");
}

element("package-filter-options-media").checked = false;
element("input-type-filter-options-json").value = "json";
element("input-type-filter-options-json").checked = true;
filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 1 || filtered[0].id !== "core") {
  throw new Error("input type filter should keep nodes with matching input port type");
}

element("input-type-filter-options-json").checked = false;
element("output-type-filter-options-json").value = "json";
element("output-type-filter-options-json").checked = true;
element("output-type-filter-options-image").value = "image";
element("output-type-filter-options-image").checked = true;
filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 2) {
  throw new Error("output type filter should support multiple selected output types");
}

const card = context.__testApi.renderNodeCard(catalog[0].items[0]);
card.eventListeners.mouseenter({clientX: 100, clientY: 120});
const preview = element("node-preview-popover");
if (
  preview.hidden
  || !preview.innerHTML.includes("Prompt Builder")
  || !preview.innerHTML.includes("graph-node preview-node")
) {
  throw new Error("node hover should show a floating preview card");
}

card.eventListeners.mousemove({clientX: 140, clientY: 160});
if (preview.style.left !== "152px" || preview.style.top !== "172px") {
  throw new Error("node preview should follow the mouse cursor");
}

card.eventListeners.mouseleave();
if (!preview.hidden) {
  throw new Error("node preview should hide when the cursor leaves the node card");
}
