const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");

function defaultApiBaseUrl() {
  if (window.location.protocol === "file:" || window.location.port === "5500") {
    return "http://127.0.0.1:8765";
  }
  return "";
}

const apiBaseUrl = window.FLAINBOT_API_BASE_URL || defaultApiBaseUrl();

function apiUrl(path) {
  return `${apiBaseUrl}${path}`;
}

function appendMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) {
    return;
  }

  input.value = "";
  appendMessage("user", message);

  const response = await fetch(apiUrl("/api/chat"), {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({message}),
  });
  const payload = await response.json();
  appendMessage("assistant", payload.reply);
});
