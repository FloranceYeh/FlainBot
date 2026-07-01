export function defaultApiBaseUrl() {
  if (window.location.protocol === "file:" || window.location.port === "5500" || window.location.port === "5173") {
    return "http://127.0.0.1:8765";
  }
  return "";
}

const apiBaseUrl = window.FLAINBOT_API_BASE_URL || defaultApiBaseUrl();

export function apiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

async function fetchJson(path, errorPrefix) {
  let response;
  try {
    response = await fetch(apiUrl(path));
  } catch (error) {
    throw new Error(`${errorPrefix}. Start server with: python start.py`);
  }
  if (!response.ok) {
    throw new Error(`${errorPrefix}: ${response.status}`);
  }
  return response.json();
}

export function loadNodeCatalog() {
  return fetchJson("/api/nodes", "Could not load node catalog");
}

export function loadGraph() {
  return fetchJson("/api/graph", "Could not load graph");
}

export function loadProviders() {
  return fetchJson("/api/providers", "Could not load providers");
}

export function loadPersonas() {
  return fetchJson("/api/personas", "Could not load personas");
}

export function loadSessions() {
  return fetchJson("/api/sessions", "Could not load sessions");
}

export function loadLogs() {
  return fetchJson("/api/logs", "Could not load logs");
}

export function logStreamUrl() {
  return apiUrl("/api/logs/stream");
}

export async function postJson(path, payload, errorPrefix) {
  let response;
  try {
    response = await fetch(apiUrl(path), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw new Error("Could not reach FlainBot server. Start it with: python start.py");
  }
  if (!response.ok) {
    throw new Error(`${errorPrefix}: ${response.status}`);
  }
  return response.json();
}

export function saveProviders(providers) {
  return postJson("/api/providers", providers, "provider save failed");
}

export function savePersonas(personas) {
  return postJson("/api/personas", personas, "persona save failed");
}

export function saveSessions(payload) {
  return postJson("/api/sessions", payload, "session save failed");
}

export function saveGraph(graphConfig) {
  return postJson("/api/graph", graphConfig, "save failed");
}

export async function deleteSession(sessionId) {
  let response;
  try {
    response = await fetch(apiUrl(`/api/sessions/${encodeURIComponent(sessionId)}`), {method: "DELETE"});
  } catch (error) {
    throw new Error("Could not reach FlainBot server. Start it with: python start.py");
  }
  if (!response.ok) {
    throw new Error(`session delete failed: ${response.status}`);
  }
  return response.json();
}

export async function clearLogs() {
  let response;
  try {
    response = await fetch(apiUrl("/api/logs"), {method: "DELETE"});
  } catch (error) {
    throw new Error("Could not reach FlainBot server. Start it with: python start.py");
  }
  if (!response.ok) {
    throw new Error(`log clear failed: ${response.status}`);
  }
  return response.json();
}

export function sendChatMessage(message, sessionId) {
  return postJson("/api/chat", {message, session_id: sessionId}, "chat failed");
}
