<template>
  <div class="app-shell">
    <header class="workbench-topbar">
      <h1 class="workbench-title">FlainBot</h1>
      <nav class="topbar-tabs" aria-label="Views">
        <button
          v-for="view in views"
          :key="view.id"
          class="view-tab"
          :class="{active: activeView === view.id}"
          :data-route="view.id"
          :aria-current="activeView === view.id ? 'page' : 'false'"
          type="button"
          @click="navigateToView(view.id)"
        >{{ view.label }}</button>
      </nav>
    </header>

    <main>
      <section
        id="planner-view"
        class="planner-workbench result-collapsed view"
        :class="{'result-collapsed': resultRailCollapsed}"
        data-view="planner"
        v-show="activeView === 'planner'"
      >
        <NodeShelf
          :filtered-catalog="filteredCatalog"
          :filter-option-values="filterOptionValues"
          :node-filter-summary="nodeFilterSummary"
          v-model:node-search="nodeSearch"
          v-model:selected-input-type="selectedInputType"
          v-model:selected-output-type="selectedOutputType"
          v-model:selected-package="selectedPackage"
          @preview="showNodePreview"
          @move-preview="moveNodePreview"
          @hide-preview="hideNodePreview"
        />
        <GraphCanvas
          :canvas-space-style="canvasSpaceStyle"
          :connection-drag="connectionDrag"
          :graph="graph"
          :personas="personas"
          :preview-connection-path="previewConnectionPath"
          :providers="providers"
          :rendered-edges="renderedEdges"
          :selected-id="selectedId"
          :status-message="statusMessage"
          :status-type="statusType"
          @canvas-drop="handleCanvasDrop"
          @canvas-pan="startCanvasPan"
          @canvas-pointer-move="handleCanvasPointerMove"
          @canvas-pointer-up="handleCanvasPointerUp"
          @canvas-ref="canvasEl = $event"
          @remove-node="removeNode"
          @reset-graph="resetGraph"
          @save-graph="handleSaveGraph"
          @select-node="selectNode"
          @start-connection="startConnectionDrag"
          @start-drag="startDrag"
          @update-property="updateProperty"
          @zoom-canvas="zoomCanvas"
        />
        <ResultRail
          :collapsed="resultRailCollapsed"
          :generated-python="generatedPython"
          @copy="copyCode"
          @toggle="toggleResultPanel"
        />
      </section>

      <ProvidersView
        :active="activeView === 'providers'"
        :provider-form="providerForm"
        :providers="providers"
        @remove="removeProvider"
        @submit="handleProviderSubmit"
      />
      <PersonasView
        :active="activeView === 'personas'"
        :persona-form="personaForm"
        :personas="personas"
        @remove="removePersona"
        @submit="handlePersonaSubmit"
      />
      <ChatView
        :active="activeView === 'chat'"
        :messages="messages"
        v-model:message-input="messageInput"
        @messages-ref="messagesEl = $event"
        @submit="handleChatSubmit"
      />
    </main>
  </div>

  <NodePreview
    :node-preview="nodePreview"
    :node-preview-style="nodePreviewStyle"
    :preview-node="previewNode"
  />
</template>

<script>
import {computed, defineComponent, nextTick, onMounted, reactive, ref} from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import NodePreview from "./components/NodePreview.vue";
import NodeShelf from "./components/NodeShelf.vue";
import ResultRail from "./components/ResultRail.vue";
import ProvidersView from "./views/ProvidersView.vue";
import PersonasView from "./views/PersonasView.vue";
import ChatView from "./views/ChatView.vue";
import {
  loadNodeCatalog,
  loadPersonas,
  loadProviders,
  saveGraph,
  savePersonas,
  saveProviders,
  sendChatMessage,
  apiUrl,
} from "./api.js";
import {
  cloneDefaults,
  connectionArrow,
  connectionPath,
  edgeToReplaceForPort,
  filterNodeCatalog,
  filterOptions,
  flattenNodeCatalog,
  generatePython,
  parseJsonOrEmpty,
  portEdgeAnchor,
} from "./graph.js";

export default defineComponent({
  name: "App",
  components: {ChatView, GraphCanvas, NodePreview, NodeShelf, PersonasView, ProvidersView, ResultRail},
  setup() {
    const nodeCatalog = ref([]);
    const flatNodeCatalog = ref([]);
    const graph = reactive({nodes: [], edges: []});
    const providers = ref([]);
    const personas = ref([]);
    const selectedId = ref(null);
    const activeView = ref("planner");
    const nodeSearch = ref("");
    const selectedPackage = ref([]);
    const selectedInputType = ref([]);
    const selectedOutputType = ref([]);
    const statusMessage = ref("");
    const statusType = ref("");
    const resultRailCollapsed = ref(true);
    const viewportState = reactive({x: 0, y: 0, scale: 1});
    const canvasEl = ref(null);
    const messagesEl = ref(null);
    const messageInput = ref("");
    const messages = ref([]);
    const connectionDrag = ref(null);
    const edgeLayoutTick = ref(0);
    const dragState = ref(null);
    const canvasPanState = ref(null);
    const nodePreview = reactive({visible: false, node: null, left: 0, top: 0});
    const providerForm = reactive({id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
    const personaForm = reactive({
      persona_id: "",
      system_prompt: "",
      begin_dialogs: "",
      tools_json: "",
      skills_json: "",
      custom_error_message: "",
    });

    const views = [
      {id: "planner", label: "Planner"},
      {id: "providers", label: "Providers"},
      {id: "personas", label: "Personas"},
      {id: "chat", label: "Chat"},
    ];

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
    const canvasSpaceStyle = computed(() => ({
      transform: `translate(${viewportState.x}px, ${viewportState.y}px) scale(${viewportState.scale})`,
    }));
    const previewNode = computed(() => {
      if (!nodePreview.node) {
        return null;
      }
      return {...nodePreview.node, id: "preview", props: cloneDefaults(nodePreview.node.defaults || {})};
    });
    const nodePreviewStyle = computed(() => ({
      left: `${nodePreview.left}px`,
      top: `${nodePreview.top}px`,
    }));
    const previewConnectionPath = computed(() => {
      if (!connectionDrag.value) {
        return "";
      }
      const from = connectionDrag.value.direction === "output" ? connectionDrag.value.start : connectionDrag.value.current;
      const to = connectionDrag.value.direction === "output" ? connectionDrag.value.current : connectionDrag.value.start;
      return connectionPath(from, to);
    });
    const renderedEdges = computed(() => graph.edges.map((edge, index) => {
      edgeLayoutTick.value;
      const fromNode = findNode(edge.from_node);
      const toNode = findNode(edge.to_node);
      if (!fromNode || !toNode) {
        return null;
      }
      const from = portCenter(edge.from_node, edge.from_port, "output");
      const to = portCenter(edge.to_node, edge.to_port, "input");
      return {key: edgeKey(edge, index), index, from, to, d: connectionPath(from, to), arrow: connectionArrow(from, to)};
    }).filter(Boolean));

    function setStatus(message, type = "") {
      statusMessage.value = message;
      statusType.value = type;
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

    function addNode(type, position = null) {
      const spec = flatNodeCatalog.value.find((node) => node.type === type);
      if (!spec) {
        setStatus(`Unknown node type: ${type}`, "error");
        return;
      }
      const offset = graph.nodes.length * 28;
      const x = position ? Math.max(0, position.x) : 48 + offset;
      const y = position ? Math.max(0, position.y) : 48 + offset;
      const item = {
        id: nextId(spec.type),
        type: spec.type,
        className: spec.className,
        title: spec.title,
        description: spec.description,
        inputs: spec.inputs,
        outputs: spec.outputs,
        props: cloneDefaults(spec.defaults),
        x,
        y,
      };
      graph.nodes.push(item);
      selectedId.value = item.id;
      nextTick(refreshEdgeLayout);
    }

    function removeNode(id) {
      graph.nodes = graph.nodes.filter((node) => node.id !== id);
      graph.edges = graph.edges.filter((edge) => edge.from_node !== id && edge.to_node !== id);
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
      connectionDrag.value = null;
    }

    function toggleResultPanel() {
      resultRailCollapsed.value = !resultRailCollapsed.value;
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
        providers: providers.value,
        personas: personas.value,
      };
    }

    async function handleSaveGraph() {
      setStatus("Saving graph...");
      try {
        await saveGraph(serializeGraph());
        setStatus("Graph saved for Web Chat.", "success");
      } catch (error) {
        setStatus(error.message, "error");
      }
    }

    function activeViewFromHash() {
      if (window.location.hash === "#chat") {
        return "chat";
      }
      if (window.location.hash === "#providers") {
        return "providers";
      }
      if (window.location.hash === "#personas") {
        return "personas";
      }
      return "planner";
    }

    function setActiveView(view) {
      activeView.value = view;
    }

    function navigateToView(view) {
      const hash = view === "planner" ? "#planner" : `#${view}`;
      if (window.location.hash === hash) {
        setActiveView(view);
        return;
      }
      window.location.hash = hash;
    }

    async function handleProviderSubmit(event) {
      const form = event.currentTarget;
      const provider = {
        id: providerForm.id.trim(),
        format: providerForm.format,
        base_url: providerForm.base_url.trim(),
        api_key: providerForm.api_key,
        model: providerForm.model.trim(),
      };
      providers.value = providers.value.filter((item) => item.id !== provider.id);
      providers.value.push(provider);
      try {
        await saveProviders(providers.value);
        Object.assign(providerForm, {id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
        form.reset();
        setStatus("Provider saved.", "success");
      } catch (error) {
        setStatus(error.message, "error");
      }
    }

    async function removeProvider(id) {
      providers.value = providers.value.filter((item) => item.id !== id);
      await saveProviders(providers.value);
    }

    async function handlePersonaSubmit(event) {
      const form = event.currentTarget;
      try {
        const persona = {
          persona_id: personaForm.persona_id.trim(),
          system_prompt: personaForm.system_prompt.trim(),
          begin_dialogs: personaForm.begin_dialogs.split("\n").map((line) => line.trim()).filter(Boolean),
          tools: parseJsonOrEmpty(personaForm.tools_json, []),
          skills: parseJsonOrEmpty(personaForm.skills_json, []),
          custom_error_message: personaForm.custom_error_message.trim() || null,
        };
        personas.value = personas.value.filter((item) => item.persona_id !== persona.persona_id);
        personas.value.push(persona);
        await savePersonas(personas.value);
        Object.assign(personaForm, {
          persona_id: "",
          system_prompt: "",
          begin_dialogs: "",
          tools_json: "",
          skills_json: "",
          custom_error_message: "",
        });
        form.reset();
        setStatus("Persona saved.", "success");
      } catch (error) {
        setStatus(error.message, "error");
      }
    }

    async function removePersona(personaId) {
      personas.value = personas.value.filter((item) => item.persona_id !== personaId);
      await savePersonas(personas.value);
    }

    function portCenter(nodeId, port, direction) {
      const selector = `.port[data-node-id="${nodeId}"][data-port="${port}"][data-direction="${direction}"]`;
      const element = document.querySelector(selector);
      if (!element || !canvasEl.value) {
        return {x: 0, y: 0};
      }
      const canvasRect = canvasEl.value.getBoundingClientRect();
      const portRect = element.getBoundingClientRect();
      return portEdgeAnchor(portRect, canvasRect, viewportState, direction);
    }

    function anchorForPort(nodeId, port, direction) {
      return portCenter(nodeId, port, direction);
    }

    function refreshEdgeLayout() {
      edgeLayoutTick.value += 1;
    }

    function canvasPointFromEvent(event) {
      const canvasRect = canvasEl.value.getBoundingClientRect();
      return {
        x: (event.clientX - canvasRect.left - viewportState.x) / viewportState.scale,
        y: (event.clientY - canvasRect.top - viewportState.y) / viewportState.scale,
      };
    }

    function handleCanvasDrop(event) {
      const type = event.dataTransfer.getData("application/x-flainbot-node-type");
      if (!type) {
        return;
      }
      hideNodePreview();
      addNode(type, canvasPointFromEvent(event));
    }

    function startDrag(event, nodeId) {
      event.preventDefault();
      const node = graph.nodes.find((item) => item.id === nodeId);
      selectedId.value = nodeId;
      dragState.value = {
        nodeId,
        startX: event.clientX,
        startY: event.clientY,
        originX: node.x,
        originY: node.y,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
    }

    function dragMove(event) {
      if (!dragState.value) {
        return;
      }
      const node = graph.nodes.find((item) => item.id === dragState.value.nodeId);
      node.x = Math.max(0, dragState.value.originX + event.clientX - dragState.value.startX);
      node.y = Math.max(0, dragState.value.originY + event.clientY - dragState.value.startY);
      nextTick(refreshEdgeLayout);
    }

    function dragEnd() {
      dragState.value = null;
    }

    function zoomCanvas(event) {
      const delta = event.deltaY > 0 ? -0.08 : 0.08;
      viewportState.scale = Math.min(1.8, Math.max(0.45, viewportState.scale + delta));
      nextTick(refreshEdgeLayout);
    }

    function startCanvasPan(event) {
      if (event.target.closest(".graph-node") || event.button !== 1) {
        return;
      }
      event.preventDefault();
      canvasPanState.value = {
        startX: event.clientX,
        startY: event.clientY,
        originX: viewportState.x,
        originY: viewportState.y,
      };
    }

    function moveCanvasPan(event) {
      if (!canvasPanState.value) {
        return;
      }
      viewportState.x = canvasPanState.value.originX + event.clientX - canvasPanState.value.startX;
      viewportState.y = canvasPanState.value.originY + event.clientY - canvasPanState.value.startY;
      nextTick(refreshEdgeLayout);
    }

    function endCanvasPan() {
      canvasPanState.value = null;
    }

    function isCompatiblePort(port) {
      if (!connectionDrag.value || !port) {
        return false;
      }
      return port.dataset.nodeId !== connectionDrag.value.nodeId && port.dataset.direction !== connectionDrag.value.direction;
    }

    function closestCompatiblePort(event) {
      const ports = [...document.querySelectorAll(".port")];
      const hitPadding = 18;
      return ports.find((port) => {
        if (!isCompatiblePort(port)) {
          return false;
        }
        const rect = port.getBoundingClientRect();
        return (
          event.clientX >= rect.left - hitPadding
          && event.clientX <= rect.right + hitPadding
          && event.clientY >= rect.top - hitPadding
          && event.clientY <= rect.bottom + hitPadding
        );
      }) || null;
    }

    function startConnectionDrag(event) {
      const port = event.currentTarget;
      event.preventDefault();
      event.stopPropagation();
      const edgeIndex = edgeToReplaceForPort(graph.edges, port.dataset.nodeId, port.dataset.port, port.dataset.direction);
      if (edgeIndex !== -1) {
        removeEdgeAt(edgeIndex);
      }
      connectionDrag.value = {
        nodeId: port.dataset.nodeId,
        port: port.dataset.port,
        direction: port.dataset.direction,
        start: anchorForPort(port.dataset.nodeId, port.dataset.port, port.dataset.direction),
        current: canvasPointFromEvent(event),
      };
      bindConnectionDragEvents();
      port.setPointerCapture(event.pointerId);
    }

    function bindConnectionDragEvents() {
      unbindConnectionDragEvents();
      window.addEventListener("pointermove", handleWindowConnectionPointerMove);
      window.addEventListener("pointerup", handleWindowConnectionPointerUp);
      window.addEventListener("pointercancel", handleWindowConnectionPointerUp);
    }

    function unbindConnectionDragEvents() {
      window.removeEventListener("pointermove", handleWindowConnectionPointerMove);
      window.removeEventListener("pointerup", handleWindowConnectionPointerUp);
      window.removeEventListener("pointercancel", handleWindowConnectionPointerUp);
    }

    function handleWindowConnectionPointerMove(event) {
      moveConnectionDrag(event);
    }

    function handleWindowConnectionPointerUp(event) {
      finishConnectionDrag(event);
    }

    function moveConnectionDrag(event) {
      if (connectionDrag.value) {
        connectionDrag.value.current = canvasPointFromEvent(event);
      }
    }

    function finishConnectionDrag(event) {
      if (!connectionDrag.value) {
        unbindConnectionDragEvents();
        return;
      }
      const target = closestCompatiblePort(event);
      if (isCompatiblePort(target)) {
        const from = connectionDrag.value.direction === "output" ? connectionDrag.value : target.dataset;
        const to = connectionDrag.value.direction === "output" ? target.dataset : connectionDrag.value;
        if (from.nodeId && from.port && to.nodeId && to.port && from.nodeId !== to.nodeId) {
          const edgeIndex = edgeToReplaceForPort(graph.edges, to.nodeId, to.port, "input");
          if (edgeIndex !== -1) {
            removeEdgeAt(edgeIndex);
          }
          graph.edges.push({from_node: from.nodeId, from_port: from.port, to_node: to.nodeId, to_port: to.port});
          nextTick(refreshEdgeLayout);
        }
      }
      connectionDrag.value = null;
      unbindConnectionDragEvents();
    }

    function handleCanvasPointerMove(event) {
      dragMove(event);
      moveConnectionDrag(event);
      moveCanvasPan(event);
    }

    function handleCanvasPointerUp(event) {
      dragEnd();
      finishConnectionDrag(event);
      endCanvasPan();
    }

    function moveNodePreview(event) {
      const offset = 12;
      const margin = 12;
      const previewWidth = 270;
      const previewHeight = 216;
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      let left = event.clientX + offset;
      let top = event.clientY + offset;

      if (left + previewWidth + margin > viewportWidth) {
        left = event.clientX - previewWidth - offset;
      }
      if (top + previewHeight + margin > viewportHeight) {
        top = event.clientY - previewHeight - offset;
      }

      nodePreview.left = Math.max(margin, Math.min(left, viewportWidth - previewWidth - margin));
      nodePreview.top = Math.max(margin, Math.min(top, viewportHeight - previewHeight - margin));
    }

    function showNodePreview(node, event) {
      nodePreview.node = node;
      nodePreview.visible = true;
      moveNodePreview(event);
    }

    function hideNodePreview() {
      nodePreview.visible = false;
    }

    async function copyCode() {
      await navigator.clipboard.writeText(generatedPython.value);
    }

    function renderTrace(trace) {
      return trace;
    }

    function appendMessage(role, text, trace = []) {
      messages.value.push({role, text, trace: renderTrace(trace)});
      nextTick(() => {
        if (messagesEl.value) {
          messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
        }
      });
    }

    async function handleChatSubmit() {
      const message = messageInput.value.trim();
      if (!message) {
        return;
      }
      messageInput.value = "";
      appendMessage("user", message);
      try {
        const payload = await sendChatMessage(message);
        appendMessage("assistant", payload.reply, payload.trace);
      } catch (error) {
        appendMessage("assistant", `Request failed: ${error.message}`);
      }
    }

    async function init() {
      try {
        nodeCatalog.value = await loadNodeCatalog();
        flatNodeCatalog.value = flattenNodeCatalog(nodeCatalog.value);
        providers.value = await loadProviders();
        personas.value = await loadPersonas();
      } catch (error) {
        setStatus(error.message, "error");
      }
      setActiveView(activeViewFromHash());
    }

    onMounted(() => {
      window.addEventListener("hashchange", () => setActiveView(activeViewFromHash()));
      init();
    });

    return {
      activeView,
      addNode,
      apiUrl,
      canvasEl,
      canvasSpaceStyle,
      connectionDrag,
      filteredCatalog,
      filterNodeCatalog,
      filterOptionValues,
      generatedPython,
      graph,
      handleCanvasPointerMove,
      handleCanvasPointerUp,
      handleCanvasDrop,
      handleChatSubmit,
      handlePersonaSubmit,
      handleProviderSubmit,
      handleSaveGraph,
      hideNodePreview,
      messageInput,
      messages,
      messagesEl,
      moveNodePreview,
      navigateToView,
      nodeFilterSummary,
      nodePreview,
      nodePreviewStyle,
      nodeSearch,
      personas,
      personaForm,
      previewConnectionPath,
      previewNode,
      providers,
      providerForm,
      removeNode,
      removePersona,
      removeProvider,
      renderedEdges,
      resetGraph,
      resultRailCollapsed,
      selectNode,
      selectedId,
      selectedInputType,
      selectedOutputType,
      selectedPackage,
      setActiveView,
      setStatus,
      showNodePreview,
      startCanvasPan,
      startConnectionDrag,
      startDrag,
      statusMessage,
      statusType,
      toggleResultPanel,
      updateProperty,
      views,
      zoomCanvas,
    };
  },
});
</script>
