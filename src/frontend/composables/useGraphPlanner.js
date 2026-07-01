import {computed, nextTick, reactive, ref} from "vue";
import {
  cloneDefaults,
  filterNodeCatalog,
  filterOptions,
  flattenNodeCatalog,
  generatePython,
  graphNodeCenter,
} from "../graph.js";

export function useGraphPlanner({
  setStatus,
  providers,
  personas,
  viewportState,
  refreshEdgeLayout,
}) {
  const nodeCatalog = ref([]);
  const flatNodeCatalog = ref([]);
  const graph = reactive({nodes: [], edges: []});
  const selectedId = ref(null);
  const nodeSearch = ref("");
  const selectedPackage = ref([]);
  const selectedInputType = ref([]);
  const selectedOutputType = ref([]);
  const latestNodeOutputs = ref({});

  const filters = computed(() => ({
    selectedPackage: selectedPackage.value,
    selectedInputType: selectedInputType.value,
    selectedOutputType: selectedOutputType.value,
  }));

  const filterOptionValues = computed(() => ({
    package: filterOptions(flatNodeCatalog.value, "package"),
    input: filterOptions(flatNodeCatalog.value, "input"),
    output: filterOptions(flatNodeCatalog.value, "output"),
  }));

  const nodeFilterSummary = computed(() => {
    const selectedCount = selectedPackage.value.length + selectedInputType.value.length + selectedOutputType.value.length;
    return selectedCount === 0 ? "Filters" : `Filters (${selectedCount})`;
  });

  const filteredCatalog = computed(() => filterNodeCatalog(nodeCatalog.value, nodeSearch.value.trim().toLowerCase(), filters.value));
  const generatedPython = computed(() => generatePython(graph, providers.value, personas.value));

  function setNodeCatalog(catalog) {
    nodeCatalog.value = catalog;
    flatNodeCatalog.value = flattenNodeCatalog(catalog);
  }

  function nextId(type) {
    const count = graph.nodes.filter((node) => node.type === type).length + 1;
    return `${type}_${count}`;
  }

  function findNode(id) {
    return graph.nodes.find((item) => item.id === id);
  }

  function edgeKey(edge, index) {
    return `${edge.from_node}:${edge.from_port}->${edge.to_node}:${edge.to_port}:${index}`;
  }

  function normalizeGraphCenter() {
    const center = graphNodeCenter(graph.nodes);
    if (!center || (center.x === 0 && center.y === 0)) {
      return;
    }
    for (const node of graph.nodes) {
      node.x -= center.x;
      node.y -= center.y;
    }
    viewportState.x += center.x * viewportState.scale;
    viewportState.y += center.y * viewportState.scale;
  }

  function addNode(type, position = null) {
    const spec = flatNodeCatalog.value.find((node) => node.type === type);
    if (!spec) {
      setStatus(`Unknown node type: ${type}`, "error");
      return;
    }
    const offset = graph.nodes.length * 28;
    const center = graphNodeCenter(graph.nodes) || {x: 0, y: 0};
    const nodePosition = position || {x: center.x + offset, y: center.y + offset};
    const item = {
      id: nextId(spec.type),
      type: spec.type,
      className: spec.className,
      title: spec.title,
      description: spec.description,
      inputs: spec.inputs,
      outputs: spec.outputs,
      props: cloneDefaults(spec.defaults),
      x: nodePosition.x,
      y: nodePosition.y,
    };
    graph.nodes.push(item);
    normalizeGraphCenter();
    selectedId.value = item.id;
    nextTick(refreshEdgeLayout);
  }

  function removeNode(id) {
    graph.nodes = graph.nodes.filter((node) => node.id !== id);
    graph.edges = graph.edges.filter((edge) => edge.from_node !== id && edge.to_node !== id);
    normalizeGraphCenter();
    if (selectedId.value === id) {
      selectedId.value = graph.nodes[0]?.id ?? null;
    }
    refreshEdgeLayout();
  }

  function removeEdgeAt(index) {
    graph.edges = graph.edges.filter((edge, edgeIndex) => edgeIndex !== index);
    refreshEdgeLayout();
  }

  function updateProperty(id, key, value) {
    const node = graph.nodes.find((item) => item.id === id);
    if (node) {
      node.props[key] = value;
    }
  }

  function selectNode(id) {
    selectedId.value = id;
  }

  function resetGraph() {
    graph.nodes = [];
    graph.edges = [];
    selectedId.value = null;
    latestNodeOutputs.value = {};
  }

  function serializeGraph({sessions = [], activeSessionId = "default"} = {}) {
    return {
      nodes: graph.nodes.map((node) => ({
        id: node.id,
        type: node.type,
        props: node.props,
        x: node.x,
        y: node.y,
      })),
      edges: graph.edges,
      providers: providers.value,
      personas: personas.value,
      sessions,
      active_session_id: activeSessionId,
    };
  }

  function restoreGraph(config) {
    graph.nodes = (config.nodes || []).flatMap((nodeConfig) => {
      const spec = flatNodeCatalog.value.find((node) => node.type === nodeConfig.type);
      if (!spec) {
        return [];
      }
      return [{
        id: nodeConfig.id,
        type: spec.type,
        className: spec.className,
        title: spec.title,
        description: spec.description,
        inputs: spec.inputs,
        outputs: spec.outputs,
        props: {...cloneDefaults(spec.defaults), ...(nodeConfig.props || {})},
        x: Number.isFinite(nodeConfig.x) ? nodeConfig.x : 48,
        y: Number.isFinite(nodeConfig.y) ? nodeConfig.y : 48,
      }];
    });
    graph.edges = config.edges || [];
    selectedId.value = graph.nodes[0]?.id ?? null;
    latestNodeOutputs.value = {};
    normalizeGraphCenter();
    nextTick(refreshEdgeLayout);
  }

  function updateLatestNodeOutputs(trace = []) {
    latestNodeOutputs.value = Object.fromEntries(
      trace.map((item) => [item.node_id, item.outputs || {}]),
    );
  }

  function nodeDisplayText(node) {
    const outputs = latestNodeOutputs.value[node.id];
    return outputs?.text || "";
  }

  return {
    nodeCatalog,
    flatNodeCatalog,
    graph,
    selectedId,
    nodeSearch,
    selectedPackage,
    selectedInputType,
    selectedOutputType,
    latestNodeOutputs,
    filterOptionValues,
    nodeFilterSummary,
    filteredCatalog,
    generatedPython,
    setNodeCatalog,
    nextId,
    findNode,
    edgeKey,
    normalizeGraphCenter,
    addNode,
    removeNode,
    removeEdgeAt,
    updateProperty,
    selectNode,
    resetGraph,
    serializeGraph,
    restoreGraph,
    updateLatestNodeOutputs,
    nodeDisplayText,
  };
}
