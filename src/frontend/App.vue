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
        <aside class="node-shelf" aria-labelledby="library-title">
          <div class="shelf-header">
            <h2 id="library-title">Nodes</h2>
            <input id="node-search" v-model="nodeSearch" type="search" autocomplete="off" placeholder="Search nodes">
            <div class="node-filters" aria-label="Node filters">
              <details id="node-filter-dropdown" class="filter-dropdown">
                <summary id="node-filter-summary">{{ nodeFilterSummary }}</summary>
                <section class="filter-section" data-filter-label="Package">
                  <h3 id="package-filter-summary">Package</h3>
                  <div id="package-filter-options" class="filter-options">
                    <label v-for="value in filterOptionValues.package" :key="value" class="filter-option">
                      <input v-model="selectedPackage" type="checkbox" :value="value">
                      <span>{{ value }}</span>
                    </label>
                  </div>
                </section>
                <section class="filter-section" data-filter-label="Input type">
                  <h3 id="input-type-filter-summary">Input type</h3>
                  <div id="input-type-filter-options" class="filter-options">
                    <label v-for="value in filterOptionValues.input" :key="value" class="filter-option">
                      <input v-model="selectedInputType" type="checkbox" :value="value">
                      <span>{{ value }}</span>
                    </label>
                  </div>
                </section>
                <section class="filter-section" data-filter-label="Output type">
                  <h3 id="output-type-filter-summary">Output type</h3>
                  <div id="output-type-filter-options" class="filter-options">
                    <label v-for="value in filterOptionValues.output" :key="value" class="filter-option">
                      <input v-model="selectedOutputType" type="checkbox" :value="value">
                      <span>{{ value }}</span>
                    </label>
                  </div>
                </section>
              </details>
            </div>
          </div>
          <div id="node-library" class="node-list">
            <section v-for="packageItem in filteredCatalog" :key="packageItem.id" class="node-package">
              <h3>{{ packageItem.title }}</h3>
              <p>{{ packageItem.description }}</p>
              <template v-for="item in packageItem.items" :key="`${packageItem.id}-${item.id || item.type}`">
                <CatalogGroup v-if="item.kind === 'group'" :item="item" :depth="0" @add-node="addNode" @preview="showNodePreview" @move-preview="moveNodePreview" @hide-preview="hideNodePreview" />
                <NodeCard v-else-if="item.kind === 'node'" :node="item" @add-node="addNode" @preview="showNodePreview" @move-preview="moveNodePreview" @hide-preview="hideNodePreview" />
              </template>
            </section>
          </div>
        </aside>

        <section class="canvas-panel" aria-labelledby="graph-title">
          <div class="canvas-toolbar">
            <h2 id="graph-title">FlainBot Node Planner</h2>
            <p id="status-message" class="status-message" :class="statusType" role="status" aria-live="polite">{{ statusMessage }}</p>
            <span id="graph-count" class="count">{{ graph.nodes.length }} nodes / {{ graph.edges.length }} edges</span>
            <div class="canvas-actions">
              <button id="save-graph" type="button" @click="handleSaveGraph">Save</button>
              <button id="reset-graph" type="button" @click="resetGraph">Reset</button>
            </div>
          </div>
          <div
            id="graph-canvas"
            ref="canvasEl"
            class="graph-canvas"
            @pointermove="handleCanvasPointerMove"
            @pointerup="handleCanvasPointerUp"
            @pointercancel="handleCanvasPointerUp"
            @wheel.prevent="zoomCanvas"
            @pointerdown="startCanvasPan"
          >
            <div id="canvas-space" class="canvas-space" data-canvas-space :style="canvasSpaceStyle">
              <svg id="edge-layer" class="edge-layer">
                <path
                  v-for="edge in renderedEdges"
                  :key="edge.key"
                  :d="edge.d"
                ></path>
                <polygon
                  v-for="edge in renderedEdges"
                  :key="`${edge.key}:arrow`"
                  class="edge-arrow"
                  points="-6 -4, 6 0, -6 4"
                  :transform="`translate(${edge.arrow.x} ${edge.arrow.y}) rotate(${edge.arrow.angle})`"
                ></polygon>
                <path
                  v-if="previewConnectionPath"
                  class="preview-connection"
                  :d="previewConnectionPath"
                ></path>
              </svg>
              <div id="node-layer" class="node-layer">
                <article
                  v-for="node in graph.nodes"
                  :key="node.id"
                  class="graph-node"
                  :class="{selected: node.id === selectedId}"
                  :style="{left: `${node.x}px`, top: `${node.y}px`}"
                  :data-node-id="node.id"
                  @pointerdown="selectNode(node.id)"
                >
                  <div class="node-header" data-drag-handle="true" @pointerdown.stop="startDrag($event, node.id)">
                    <span class="node-type">{{ node.id }} / {{ node.className }}</span>
                    <h3>{{ node.title }}</h3>
                  </div>
                  <div class="node-body">
                    <div class="ports">
                      <div class="port-column">
                        <span class="port-title">Inputs</span>
                        <PortList :node="node" direction="input" :connection-drag="connectionDrag" @start-connection="startConnectionDrag" />
                      </div>
                      <div class="port-column">
                        <span class="port-title">Outputs</span>
                        <PortList :node="node" direction="output" :connection-drag="connectionDrag" @start-connection="startConnectionDrag" />
                      </div>
                    </div>
                    <form v-if="Object.keys(node.props).length > 0 || node.type === 'provider_call' || node.type === 'persona'" class="node-properties" autocomplete="off" @submit.prevent>
                      <div v-if="node.type === 'provider_call'" class="field">
                        <label>provider_id</label>
                        <select :value="node.props.provider_id" data-prop-key="provider_id" @input="updateProperty(node.id, 'provider_id', $event.target.value)">
                          <option value="">Select provider</option>
                          <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.id }} / {{ provider.format }}</option>
                        </select>
                      </div>
                      <div v-else-if="node.type === 'persona'" class="field">
                        <label>persona_id</label>
                        <select :value="node.props.persona_id" data-prop-key="persona_id" @input="updateProperty(node.id, 'persona_id', $event.target.value)">
                          <option value="">Select persona</option>
                          <option v-for="persona in personas" :key="persona.persona_id" :value="persona.persona_id">{{ persona.persona_id }}</option>
                        </select>
                      </div>
                      <template v-else>
                        <div v-for="(value, key) in node.props" :key="key" class="field">
                          <label>{{ key }}</label>
                          <input :value="value" :data-prop-key="key" @input="updateProperty(node.id, key, $event.target.value)">
                        </div>
                      </template>
                    </form>
                    <div class="node-actions">
                      <button type="button" class="danger" data-action="remove" @click="removeNode(node.id)">Remove</button>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </section>

        <aside id="result-panel" class="result-rail collapsed" :class="{collapsed: resultRailCollapsed}" aria-label="Results">
          <button id="toggle-result-panel" class="result-toggle" type="button" :aria-expanded="resultRailCollapsed ? 'false' : 'true'" title="Toggle generated output" @click="toggleResultPanel">
            <span class="result-toggle-label">Generated Python</span>
          </button>
          <div id="python-panel" class="result-section">
            <div class="result-actions">
              <button id="copy-code" type="button" @click="copyCode">Copy</button>
            </div>
            <pre><code id="python-code">{{ generatedPython }}</code></pre>
          </div>
        </aside>
      </section>

      <section id="providers-view" class="view providers-shell" data-view="providers" v-show="activeView === 'providers'">
        <section class="panel provider-editor" aria-labelledby="providers-title">
          <div class="section-header">
            <h2 id="providers-title">Providers</h2>
            <span class="count">Create reusable provider configs for Call Provider nodes.</span>
          </div>
          <form id="provider-form" class="provider-form" autocomplete="off" @submit.prevent="handleProviderSubmit">
            <div class="field">
              <label>ID</label>
              <input v-model="providerForm.id" name="id" placeholder="provider-id" required>
            </div>
            <div class="field">
              <label>Format</label>
              <select v-model="providerForm.format" name="format">
                <option value="openai_chat">OpenAI Chat</option>
                <option value="anthropic_messages">Anthropic Messages</option>
              </select>
            </div>
            <div class="field">
              <label>Base URL</label>
              <input v-model="providerForm.base_url" name="base_url" placeholder="provider-base-url" required>
            </div>
            <div class="field">
              <label>API Key</label>
              <input v-model="providerForm.api_key" name="api_key">
            </div>
            <div class="field">
              <label>Model</label>
              <input v-model="providerForm.model" name="model" placeholder="your-model-name" required>
            </div>
            <button type="submit">Save Provider</button>
          </form>
        </section>
        <section class="panel provider-list-panel" aria-labelledby="provider-list-title">
          <div class="section-header">
            <h2 id="provider-list-title">Configured Providers</h2>
          </div>
          <div id="provider-list" class="provider-list">
            <p v-if="providers.length === 0" class="empty-state">No providers configured.</p>
            <article v-for="provider in providers" :key="provider.id" class="provider-card">
              <div>
                <span class="node-type">{{ provider.format }}</span>
                <h3>{{ provider.id }}</h3>
                <p>{{ provider.base_url }} / {{ provider.model }}</p>
              </div>
              <button type="button" class="danger" :data-remove-provider="provider.id" @click="removeProvider(provider.id)">Remove</button>
            </article>
          </div>
        </section>
      </section>

      <section id="personas-view" class="view personas-shell" data-view="personas" v-show="activeView === 'personas'">
        <section class="panel persona-editor" aria-labelledby="personas-title">
          <div class="section-header">
            <h2 id="personas-title">Personas</h2>
            <span class="count">Create reusable prompt profiles for Apply Persona nodes.</span>
          </div>
          <form id="persona-form" class="persona-form" autocomplete="off" @submit.prevent="handlePersonaSubmit">
            <div class="field">
              <label>ID</label>
              <input v-model="personaForm.persona_id" name="persona_id" placeholder="persona-id" required>
            </div>
            <div class="field">
              <label>System Prompt</label>
              <textarea v-model="personaForm.system_prompt" name="system_prompt" placeholder="system-prompt" required></textarea>
            </div>
            <div class="field">
              <label>Begin Dialogs</label>
              <textarea v-model="personaForm.begin_dialogs" name="begin_dialogs" placeholder="user and assistant lines"></textarea>
            </div>
            <div class="field">
              <label>Tools JSON</label>
              <textarea v-model="personaForm.tools_json" name="tools_json" placeholder="[]"></textarea>
            </div>
            <div class="field">
              <label>Skills JSON</label>
              <textarea v-model="personaForm.skills_json" name="skills_json" placeholder="[]"></textarea>
            </div>
            <div class="field">
              <label>Custom Error Message</label>
              <input v-model="personaForm.custom_error_message" name="custom_error_message" placeholder="fallback-message">
            </div>
            <button type="submit">Save Persona</button>
          </form>
        </section>
        <section class="panel persona-list-panel" aria-labelledby="persona-list-title">
          <div class="section-header">
            <h2 id="persona-list-title">Configured Personas</h2>
          </div>
          <div id="persona-list" class="persona-list">
            <p v-if="personas.length === 0" class="empty-state">No personas configured.</p>
            <article v-for="persona in personas" :key="persona.persona_id" class="persona-card">
              <div>
                <span class="node-type">{{ persona.begin_dialogs.length }} begin dialogs</span>
                <h3>{{ persona.persona_id }}</h3>
                <p>{{ persona.system_prompt }}</p>
              </div>
              <button type="button" class="danger" :data-remove-persona="persona.persona_id" @click="removePersona(persona.persona_id)">Remove</button>
            </article>
          </div>
        </section>
      </section>

      <section id="chat-view" class="view chat-shell" data-view="chat" v-show="activeView === 'chat'">
        <header class="chat-header">
          <h2>FlainBot Chat</h2>
          <p>Graph runtime: input node to model node to output node.</p>
        </header>
        <section id="messages" ref="messagesEl" class="messages" aria-live="polite">
          <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
            <template v-if="message.trace.length > 0">
              <p>{{ message.text }}</p>
              <details class="trace-panel">
                <summary>Runtime trace ({{ message.trace.length }})</summary>
                <pre><code>{{ JSON.stringify(message.trace, null, 2) }}</code></pre>
              </details>
            </template>
            <template v-else>{{ message.text }}</template>
          </div>
        </section>
        <form id="chat-form" class="composer" @submit.prevent="handleChatSubmit">
          <input v-model="messageInput" id="message-input" name="message" autocomplete="off" placeholder="Type a message">
          <button type="submit">Send</button>
        </form>
      </section>
    </main>
  </div>

  <div
    id="node-preview-popover"
    class="node-preview"
    :style="nodePreviewStyle"
    :hidden="!nodePreview.visible"
  >
    <article v-if="nodePreview.node" class="graph-node preview-node">
      <div class="node-header">
        <span class="node-type">preview / {{ nodePreview.node.className }}</span>
        <h3>{{ nodePreview.node.title }}</h3>
      </div>
      <div class="node-body">
        <p>{{ nodePreview.node.description }}</p>
        <div class="ports">
          <div class="port-column">
            <span class="port-title">Inputs</span>
            <PortList :node="previewNode" direction="input" :connection-drag="null" />
          </div>
          <div class="port-column">
            <span class="port-title">Outputs</span>
            <PortList :node="previewNode" direction="output" :connection-drag="null" />
          </div>
        </div>
        <form v-if="previewNode && Object.keys(previewNode.props).length > 0" class="node-properties" autocomplete="off" @submit.prevent>
          <div v-for="(value, key) in previewNode.props" :key="key" class="field">
            <label>{{ key }}</label>
            <input :value="value" readonly>
          </div>
        </form>
      </div>
    </article>
  </div>
</template>

<script>
import {computed, defineComponent, nextTick, onMounted, reactive, ref} from "vue";
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
  portName,
  portType,
} from "./graph.js";

const PortList = defineComponent({
  name: "PortList",
  props: {
    node: {type: Object, required: true},
    direction: {type: String, required: true},
    connectionDrag: {type: Object, default: null},
  },
  emits: ["start-connection"],
  methods: {portName, portType},
  computed: {
    ports() {
      return this.direction === "input" ? this.node.inputs : this.node.outputs;
    },
  },
  template: `
    <span v-if="ports.length === 0" class="node-type">none</span>
    <button
      v-for="port in ports"
      v-else
      :key="portName(port)"
      type="button"
      class="port"
      :class="[direction, {compatible: connectionDrag && node.id !== connectionDrag.nodeId && direction !== connectionDrag.direction}]"
      :data-node-id="node.id"
      :data-port="portName(port)"
      :data-port-type="portType(port)"
      :data-direction="direction"
      :data-compatible="connectionDrag && node.id !== connectionDrag.nodeId && direction !== connectionDrag.direction ? 'true' : 'false'"
      @pointerdown.stop="$emit('start-connection', $event)"
    ><span>{{ portName(port) }}</span><span class="port-type">{{ portType(port) }}</span></button>
  `,
});

const NodeCard = defineComponent({
  name: "NodeCard",
  props: {node: {type: Object, required: true}},
  emits: ["add-node", "preview", "move-preview", "hide-preview"],
  template: `
    <article class="node-card" @mouseenter="$emit('preview', node, $event)" @mousemove="$emit('move-preview', $event)" @mouseleave="$emit('hide-preview')">
      <span class="node-type">{{ node.className }}</span>
      <h4>{{ node.title }}</h4>
      <p>{{ node.description }}</p>
      <button type="button" class="add-node-button" @click="$emit('add-node', node.type)">Add node</button>
    </article>
  `,
});

const CatalogGroup = defineComponent({
  name: "CatalogGroup",
  props: {
    item: {type: Object, required: true},
    depth: {type: Number, default: 0},
  },
  emits: ["add-node", "preview", "move-preview", "hide-preview"],
  template: `
    <section class="node-group" :data-depth="String(depth)">
      <h4>{{ item.title }}</h4>
      <template v-for="child in item.items" :key="child.id || child.type">
        <CatalogGroup
          v-if="child.kind === 'group'"
          :item="child"
          :depth="depth + 1"
          @add-node="$emit('add-node', $event)"
          @preview="(...args) => $emit('preview', ...args)"
          @move-preview="$emit('move-preview', $event)"
          @hide-preview="$emit('hide-preview')"
        />
        <NodeCard
          v-else-if="child.kind === 'node'"
          :node="child"
          @add-node="$emit('add-node', $event)"
          @preview="(...args) => $emit('preview', ...args)"
          @move-preview="$emit('move-preview', $event)"
          @hide-preview="$emit('hide-preview')"
        />
      </template>
    </section>
  `,
});
CatalogGroup.components = {NodeCard, CatalogGroup};

export default defineComponent({
  name: "App",
  components: {CatalogGroup, NodeCard, PortList},
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

    function addNode(type) {
      const spec = flatNodeCatalog.value.find((node) => node.type === type);
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
      selectedId.value = item.id;
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
