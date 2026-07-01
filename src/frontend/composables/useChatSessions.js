import {nextTick, ref} from "vue";
import {deleteSession, loadSessions, saveSessions, sendChatMessage} from "../api.js";

export function useChatSessions({updateLatestNodeOutputs}) {
  const messagesEl = ref(null);
  const messageInput = ref("");
  const messages = ref([]);
  const sessions = ref([{id: "default", title: "Default", contexts: []}]);
  const activeSessionId = ref("default");

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
    nextTick(scrollMessagesToBottom);
  }

  function scrollMessagesToBottom() {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
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

  function renderTrace(trace) {
    return trace;
  }

  function appendMessage(role, text, trace = []) {
    messages.value.push({role, text, trace: renderTrace(trace)});
    nextTick(scrollMessagesToBottom);
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
      updateLatestNodeOutputs(payload.trace || []);
      for (const reply of payload.replies || [payload.reply]) {
        appendMessage("assistant", reply, payload.trace);
      }
      restoreSessions(await loadSessions(), false);
    } catch (error) {
      appendMessage("assistant", `Request failed: ${error.message}`);
    }
  }

  return {
    messagesEl,
    messageInput,
    messages,
    sessions,
    activeSessionId,
    restoreSessions,
    syncMessagesFromActiveSession,
    selectSession,
    handleNewSession,
    handleDeleteSession,
    handleChatSubmit,
  };
}
