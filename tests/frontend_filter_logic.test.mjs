import {
  connectionArrow,
  connectionPath,
  filterNodeCatalog,
  filterOptions,
  flattenNodeCatalog,
  generatePython,
} from "../src/frontend/graph.js";

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

const flat = flattenNodeCatalog(catalog);

if (filterOptions(flat, "package").join(",") !== "core,media") {
  throw new Error("package filter options should include node packages");
}

let filtered = filterNodeCatalog(catalog, "", {
  selectedPackage: ["media"],
  selectedInputType: [],
  selectedOutputType: [],
});
if (filtered.length !== 1 || filtered[0].id !== "media") {
  throw new Error("package filter should keep only matching package nodes");
}

filtered = filterNodeCatalog(catalog, "", {
  selectedPackage: [],
  selectedInputType: ["json"],
  selectedOutputType: [],
});
if (filtered.length !== 1 || filtered[0].id !== "core") {
  throw new Error("input type filter should keep nodes with matching input port type");
}

filtered = filterNodeCatalog(catalog, "", {
  selectedPackage: [],
  selectedInputType: [],
  selectedOutputType: ["json", "image"],
});
if (filtered.length !== 2) {
  throw new Error("output type filter should support multiple selected output types");
}

const python = generatePython(
  {
    nodes: [
      {
        id: "persona_1",
        type: "persona",
        className: "PersonaNode",
        props: {persona_id: "cat"},
      },
    ],
    edges: [],
  },
  [],
  [{persona_id: "cat", system_prompt: "Meow"}],
);

if (!python.includes("build_graph_from_config") || !python.includes("GraphExecutor")) {
  throw new Error("generated python should build graphs from registry-backed config");
}

const externalPython = generatePython(
  {
    nodes: [
      {
        id: "meow_1",
        type: "meow_before_punctuation",
        className: "MeowBeforePunctuationNode",
        props: {},
      },
    ],
    edges: [],
  },
  [],
  [],
);

if (!externalPython.includes("meow_before_punctuation") || externalPython.includes("ChatOutputNode()")) {
  throw new Error("generated python should preserve external node types");
}

const pathWithMidpoint = connectionPath({x: 10, y: 20}, {x: 210, y: 120});
if (!pathWithMidpoint.startsWith("M 10 20 C ") || (pathWithMidpoint.match(/ C /g) || []).length !== 1) {
  throw new Error("connection path should be one smooth cubic curve");
}

const arrow = connectionArrow({x: 10, y: 20}, {x: 210, y: 120});
if (arrow.x !== 110 || arrow.y !== 70 || !Number.isFinite(arrow.angle)) {
  throw new Error("connection arrow should be positioned at the smooth curve midpoint");
}
