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
      className: "",
      classList: {toggle() {}, remove() {}, add() {}},
      dataset: {},
      style: {},
      appendChild() {},
      addEventListener() {},
      setAttribute() {},
      querySelector() { return element(`${id}-child`); },
      querySelectorAll() { return []; },
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
vm.runInContext(`${appJs}\nthis.__testApi = {collectCatalogNodes, flattenNodeCatalog, filterNodeCatalog, renderNodeFilters};`, context);

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

element("package-filter").value = "media";
let filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 1 || filtered[0].id !== "media") {
  throw new Error("package filter should keep only matching package nodes");
}

element("package-filter").value = "";
element("input-type-filter").value = "json";
filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 1 || filtered[0].id !== "core") {
  throw new Error("input type filter should keep nodes with matching input port type");
}

element("input-type-filter").value = "";
element("output-type-filter").value = "image";
filtered = context.__testApi.filterNodeCatalog();
if (filtered.length !== 1 || filtered[0].id !== "media") {
  throw new Error("output type filter should keep nodes with matching output port type");
}
