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
    </main>
  </div>

  <NodePreview
    :node-preview="nodePreview"
    :node-preview-style="nodePreviewStyle"
    :preview-node="previewNode"
  />
</template>

<script>
import {defineComponent, nextTick, onMounted, reactive, ref} from "vue";
import GraphCanvas from "./components/GraphCanvas.vue";
import NodePreview from "./components/NodePreview.vue";
import NodeShelf from "./components/NodeShelf.vue";
import ResultRail from "./components/ResultRail.vue";
import ProvidersView from "./views/ProvidersView.vue";
import PersonasView from "./views/PersonasView.vue";
import ChatView from "./views/ChatView.vue";
import {useCanvasInteractions} from "./composables/useCanvasInteractions.js";
import {useGraphPlanner} from "./composables/useGraphPlanner.js";
import {
  deleteSession,
  loadGraph,
  loadNodeCatalog,
  loadPersonas,
  loadProviders,
  loadSessions,
  saveGraph,
  savePersonas,
  saveProviders,
  saveSessions,
  sendChatMessage,
  apiUrl,
} from "./api.js";
import {parseJsonOrEmpty} from "./graph.js";

export default defineComponent({
  name: "App",
  components: {ChatView, GraphCanvas, NodePreview, NodeShelf, PersonasView, ProvidersView, ResultRail},
  setup() {
    const providers = ref([]);
    const personas = ref([]);
    const activeView = ref("planner");
    const statusMessage = ref("");
    const statusType = ref("");
    const resultRailCollapsed = ref(true);
    const viewportState = reactive({x: 0, y: 0, scale: 1});
    const messagesEl = ref(null);
    const messageInput = ref("");
    const messages = ref([]);
    const sessions = ref([{id: "default", title: "Default", contexts: []}]);
    const activeSessionId = ref("default");
    const edgeLayoutTick = ref(0);
    const providerEditingId = ref("");
    const personaEditingId = ref("");
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

    function setStatus(message, type = "") {
      statusMessage.value = message;
      statusType.value = type;
    }

    function refreshEdgeLayout() {
      edgeLayoutTick.value += 1;
    }

    const planner = useGraphPlanner({
      setStatus,
      providers,
      personas,
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

    function toggleResultPanel() {
      resultRailCollapsed.value = !resultRailCollapsed.value;
    }

    function restoreSessions(payload, syncMessages = true) {
      sessions.value = payload.sessions?.length ? payload.sessions : [{id: "default", title: "Default", contexts: []}];
      activeSessionId.value = payload.active_session_id || sessions.value[0].id;
      if (!sessions.value.some((session) => session.id === activeSessionId.value)) {
        activeSessionId.value = sessions.value[0].id;
      }
      if (syncMessages) {
        syncMessagesFromActiveSession();
      }
    }

    function activeSession() {
      return sessions.value.find((session) => session.id === activeSessionId.value) || sessions.value[0];
    }

    function syncMessagesFromActiveSession() {
      const session = activeSession();
      messages.value = (session?.contexts || []).map((item) => ({
        role: item.role,
        text: item.content,
        trace: [],
      }));
      nextTick(() => {
        if (messagesEl.value) {
          messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
        }
      });
    }

    async function persistSessions() {
      await saveSessions({active_session_id: activeSessionId.value, sessions: sessions.value});
    }

    function nextSessionId() {
      let index = sessions.value.length + 1;
      let id = `session_${index}`;
      while (sessions.value.some((session) => session.id === id)) {
        index += 1;
        id = `session_${index}`;
      }
      return id;
    }

    async function selectSession(sessionId) {
      activeSessionId.value = sessionId;
      syncMessagesFromActiveSession();
      await persistSessions();
    }

    async function handleNewSession() {
      const id = nextSessionId();
      sessions.value.push({id, title: `Session ${sessions.value.length + 1}`, contexts: []});
      activeSessionId.value = id;
      syncMessagesFromActiveSession();
      await persistSessions();
    }

    async function handleDeleteSession() {
      if (sessions.value.length <= 1) {
        return;
      }
      const deletedId = activeSessionId.value;
      sessions.value = sessions.value.filter((session) => session.id !== deletedId);
      activeSessionId.value = sessions.value[0].id;
      syncMessagesFromActiveSession();
      await deleteSession(deletedId);
      await persistSessions();
    }

    async function handleSaveGraph() {
      setStatus("Saving graph...");
      try {
        await saveGraph(planner.serializeGraph({
          sessions: sessions.value,
          activeSessionId: activeSessionId.value,
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
      providers.value = providers.value.filter((item) => item.id !== (providerEditingId.value || provider.id));
      providers.value.push(provider);
      try {
        await saveProviders(providers.value);
        providerEditingId.value = "";
        Object.assign(providerForm, {id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
        form.reset();
        setStatus("Provider saved.", "success");
      } catch (error) {
        setStatus(error.message, "error");
      }
    }

    function editProvider(provider) {
      providerEditingId.value = provider.id;
      Object.assign(providerForm, {
        id: provider.id,
        format: provider.format,
        base_url: provider.base_url,
        api_key: provider.api_key,
        model: provider.model,
      });
    }

    async function removeProvider(id) {
      providers.value = providers.value.filter((item) => item.id !== id);
      if (providerEditingId.value === id) {
        providerEditingId.value = "";
        Object.assign(providerForm, {id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
      }
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
        personas.value = personas.value.filter((item) => item.persona_id !== (personaEditingId.value || persona.persona_id));
        personas.value.push(persona);
        await savePersonas(personas.value);
        personaEditingId.value = "";
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

    function editPersona(persona) {
      personaEditingId.value = persona.persona_id;
      Object.assign(personaForm, {
        persona_id: persona.persona_id,
        system_prompt: persona.system_prompt,
        begin_dialogs: persona.begin_dialogs.join("\n"),
        tools_json: JSON.stringify(persona.tools || [], null, 2),
        skills_json: JSON.stringify(persona.skills || [], null, 2),
        custom_error_message: persona.custom_error_message || "",
      });
    }

    async function removePersona(personaId) {
      personas.value = personas.value.filter((item) => item.persona_id !== personaId);
      if (personaEditingId.value === personaId) {
        personaEditingId.value = "";
        Object.assign(personaForm, {
          persona_id: "",
          system_prompt: "",
          begin_dialogs: "",
          tools_json: "",
          skills_json: "",
          custom_error_message: "",
        });
      }
      await savePersonas(personas.value);
    }

    async function copyCode() {
      await navigator.clipboard.writeText(planner.generatedPython.value);
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
        const payload = await sendChatMessage(message, activeSessionId.value);
        planner.updateLatestNodeOutputs(payload.trace || []);
        for (const reply of payload.replies || [payload.reply]) {
          appendMessage("assistant", reply, payload.trace);
        }
        restoreSessions(await loadSessions(), false);
      } catch (error) {
        appendMessage("assistant", `Request failed: ${error.message}`);
      }
    }

    async function init() {
      try {
        planner.setNodeCatalog(await loadNodeCatalog());
        const savedGraph = await loadGraph();
        planner.restoreGraph(savedGraph);
        providers.value = savedGraph.providers || await loadProviders();
        personas.value = savedGraph.personas || await loadPersonas();
        restoreSessions(await loadSessions());
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
      activeSessionId,
      apiUrl,
      canvasEl: canvas.canvasEl,
      canvasSpaceStyle: canvas.canvasSpaceStyle,
      connectionDrag: canvas.connectionDrag,
      filteredCatalog: planner.filteredCatalog,
      filterOptionValues: planner.filterOptionValues,
      generatedPython: planner.generatedPython,
      graph: planner.graph,
      latestNodeOutputs: planner.latestNodeOutputs,
      editPersona,
      editProvider,
      handleCanvasPointerMove: canvas.handleCanvasPointerMove,
      handleCanvasPointerUp: canvas.handleCanvasPointerUp,
      handleCanvasDrop: canvas.handleCanvasDrop,
      handleChatSubmit,
      handleDeleteSession,
      handleNewSession,
      handlePersonaSubmit,
      handleProviderSubmit,
      handleSaveGraph,
      hideNodePreview: canvas.hideNodePreview,
      messageInput,
      messages,
      messagesEl,
      moveNodePreview: canvas.moveNodePreview,
      navigateToView,
      nodeFilterSummary: planner.nodeFilterSummary,
      nodePreview: canvas.nodePreview,
      nodePreviewStyle: canvas.nodePreviewStyle,
      nodeSearch: planner.nodeSearch,
      personas,
      personaEditingId,
      personaForm,
      previewConnectionPath: canvas.previewConnectionPath,
      previewNode: canvas.previewNode,
      providers,
      providerEditingId,
      providerForm,
      nodeDisplayText: planner.nodeDisplayText,
      removeNode: planner.removeNode,
      removePersona,
      removeProvider,
      renderedEdges: canvas.renderedEdges,
      resetGraph,
      resultRailCollapsed,
      selectNode: planner.selectNode,
      selectSession,
      selectedId: planner.selectedId,
      selectedInputType: planner.selectedInputType,
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
      sessions,
      toggleResultPanel,
      updateProperty: planner.updateProperty,
      views,
      zoomCanvas: canvas.zoomCanvas,
    };
  },
});
</script>
