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
          :node-display-text="nodeDisplayText"
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
        @edit="editProvider"
        @remove="removeProvider"
        @submit="handleProviderSubmit"
      />
      <PersonasView
        :active="activeView === 'personas'"
        :persona-form="personaForm"
        :personas="personas"
        @edit="editPersona"
        @remove="removePersona"
        @submit="handlePersonaSubmit"
      />
      <ChatView
        :active="activeView === 'chat'"
        :active-session-id="activeSessionId"
        :messages="messages"
        :sessions="sessions"
        v-model:message-input="messageInput"
        @delete-session="handleDeleteSession"
        @messages-ref="messagesEl = $event"
        @new-session="handleNewSession"
        @select-session="selectSession"
        @submit="handleChatSubmit"
      />
      <LogsView
        :active="activeView === 'logs'"
        :filtered-log-groups="filteredLogGroups"
        :filtered-logs="filteredLogs"
        :level-options="logLevelOptions"
        :logs="logs"
        :source-options="logSourceOptions"
        v-model:selected-level="selectedLogLevel"
        v-model:selected-source="selectedLogSource"
        @clear="clearLogEntries"
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
import {defineComponent, onBeforeUnmount, onMounted, reactive, ref} from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import NodePreview from "./components/NodePreview.vue";
import NodeShelf from "./components/NodeShelf.vue";
import ResultRail from "./components/ResultRail.vue";
import ProvidersView from "./views/ProvidersView.vue";
import PersonasView from "./views/PersonasView.vue";
import ChatView from "./views/ChatView.vue";
import LogsView from "./views/LogsView.vue";
import {useCanvasInteractions} from "./composables/useCanvasInteractions.js";
import {useChatSessions} from "./composables/useChatSessions.js";
import {useGraphPlanner} from "./composables/useGraphPlanner.js";
import {useLogs} from "./composables/useLogs.js";
import {usePersonaSettings} from "./composables/usePersonaSettings.js";
import {useProviderSettings} from "./composables/useProviderSettings.js";
import {
  loadGraph,
  loadNodeCatalog,
  loadPersonas,
  loadProviders,
  loadSessions,
  saveGraph,
  apiUrl,
} from "./api.js";

export default defineComponent({
  name: "App",
  components: {ChatView, GraphCanvas, LogsView, NodePreview, NodeShelf, PersonasView, ProvidersView, ResultRail},
  setup() {
    const activeView = ref("planner");
    const statusMessage = ref("");
    const statusType = ref("");
    const resultRailCollapsed = ref(true);
    const viewportState = reactive({x: 0, y: 0, scale: 1});
    const edgeLayoutTick = ref(0);

    const views = [
      {id: "planner", label: "Planner"},
      {id: "providers", label: "Providers"},
      {id: "personas", label: "Personas"},
      {id: "chat", label: "Chat"},
      {id: "logs", label: "Logs"},
    ];

    function setStatus(message, type = "") {
      statusMessage.value = message;
      statusType.value = type;
    }

    function refreshEdgeLayout() {
      edgeLayoutTick.value += 1;
    }

    const providerSettings = useProviderSettings({setStatus});
    const personaSettings = usePersonaSettings({setStatus});

    const planner = useGraphPlanner({
      setStatus,
      providers: providerSettings.providers,
      personas: personaSettings.personas,
      viewportState,
      refreshEdgeLayout,
    });

    const canvas = useCanvasInteractions({
      graph: planner.graph,
      selectedId: planner.selectedId,
      viewportState,
      edgeLayoutTick,
      refreshEdgeLayout,
      findNode: planner.findNode,
      edgeKey: planner.edgeKey,
      addNode: planner.addNode,
      removeEdgeAt: planner.removeEdgeAt,
      normalizeGraphCenter: planner.normalizeGraphCenter,
    });

    function resetGraph() {
      planner.resetGraph();
      canvas.clearConnectionDrag();
    }

    const chat = useChatSessions({
      updateLatestNodeOutputs: planner.updateLatestNodeOutputs,
    });
    const logState = useLogs({setStatus});

    function toggleResultPanel() {
      resultRailCollapsed.value = !resultRailCollapsed.value;
    }

    async function handleSaveGraph() {
      setStatus("Saving graph...");
      try {
        await saveGraph(planner.serializeGraph({
          sessions: chat.sessions.value,
          activeSessionId: chat.activeSessionId.value,
        }));
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
      if (window.location.hash === "#logs") {
        return "logs";
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

    async function copyCode() {
      await navigator.clipboard.writeText(planner.generatedPython.value);
    }

    async function init() {
      try {
        planner.setNodeCatalog(await loadNodeCatalog());
        const savedGraph = await loadGraph();
        planner.restoreGraph(savedGraph);
        providerSettings.providers.value = savedGraph.providers || await loadProviders();
        personaSettings.personas.value = savedGraph.personas || await loadPersonas();
        chat.restoreSessions(await loadSessions());
        await logState.refreshLogs();
        logState.startLogStream();
      } catch (error) {
        setStatus(error.message, "error");
      }
      setActiveView(activeViewFromHash());
    }

    onMounted(() => {
      window.addEventListener("hashchange", () => setActiveView(activeViewFromHash()));
      init();
    });
    onBeforeUnmount(() => {
      logState.stopLogStream();
    });

    return {
      activeView,
      activeSessionId: chat.activeSessionId,
      apiUrl,
      canvasEl: canvas.canvasEl,
      canvasSpaceStyle: canvas.canvasSpaceStyle,
      connectionDrag: canvas.connectionDrag,
      filteredCatalog: planner.filteredCatalog,
      filterOptionValues: planner.filterOptionValues,
      generatedPython: planner.generatedPython,
      graph: planner.graph,
      latestNodeOutputs: planner.latestNodeOutputs,
      editPersona: personaSettings.editPersona,
      editProvider: providerSettings.editProvider,
      clearLogEntries: logState.clearLogEntries,
      filteredLogGroups: logState.filteredLogGroups,
      filteredLogs: logState.filteredLogs,
      handleCanvasPointerMove: canvas.handleCanvasPointerMove,
      handleCanvasPointerUp: canvas.handleCanvasPointerUp,
      handleCanvasDrop: canvas.handleCanvasDrop,
      handleChatSubmit: chat.handleChatSubmit,
      handleDeleteSession: chat.handleDeleteSession,
      handleNewSession: chat.handleNewSession,
      handlePersonaSubmit: personaSettings.handlePersonaSubmit,
      handleProviderSubmit: providerSettings.handleProviderSubmit,
      handleSaveGraph,
      hideNodePreview: canvas.hideNodePreview,
      logs: logState.logs,
      logLevelOptions: logState.levelOptions,
      logSourceOptions: logState.sourceOptions,
      messageInput: chat.messageInput,
      messages: chat.messages,
      messagesEl: chat.messagesEl,
      moveNodePreview: canvas.moveNodePreview,
      navigateToView,
      nodeFilterSummary: planner.nodeFilterSummary,
      nodePreview: canvas.nodePreview,
      nodePreviewStyle: canvas.nodePreviewStyle,
      nodeSearch: planner.nodeSearch,
      personas: personaSettings.personas,
      personaEditingId: personaSettings.personaEditingId,
      personaForm: personaSettings.personaForm,
      previewConnectionPath: canvas.previewConnectionPath,
      previewNode: canvas.previewNode,
      providers: providerSettings.providers,
      providerEditingId: providerSettings.providerEditingId,
      providerForm: providerSettings.providerForm,
      nodeDisplayText: planner.nodeDisplayText,
      removeNode: planner.removeNode,
      removePersona: personaSettings.removePersona,
      removeProvider: providerSettings.removeProvider,
      renderedEdges: canvas.renderedEdges,
      resetGraph,
      resultRailCollapsed,
      selectNode: planner.selectNode,
      selectSession: chat.selectSession,
      selectedId: planner.selectedId,
      selectedInputType: planner.selectedInputType,
      selectedLogLevel: logState.selectedLevel,
      selectedLogSource: logState.selectedSource,
      selectedOutputType: planner.selectedOutputType,
      selectedPackage: planner.selectedPackage,
      setActiveView,
      setStatus,
      showNodePreview: canvas.showNodePreview,
      startCanvasPan: canvas.startCanvasPan,
      startConnectionDrag: canvas.startConnectionDrag,
      startDrag: canvas.startDrag,
      statusMessage,
      statusType,
      sessions: chat.sessions,
      toggleResultPanel,
      updateProperty: planner.updateProperty,
      views,
      zoomCanvas: canvas.zoomCanvas,
    };
  },
});
</script>
