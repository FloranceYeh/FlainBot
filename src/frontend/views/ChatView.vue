<template>
  <section id="chat-view" class="view chat-shell" data-view="chat" v-show="active">
    <header class="chat-header">
      <div>
        <h2>FlainBot Chat</h2>
        <p>Graph runtime: input node to model node to output node.</p>
      </div>
      <div class="session-controls">
        <select id="session-select" :value="activeSessionId" @change="$emit('select-session', $event.target.value)">
          <option v-for="session in sessions" :key="session.id" :value="session.id">{{ session.title }}</option>
        </select>
        <button id="new-session" type="button" @click="$emit('new-session')">New</button>
        <button id="delete-session" type="button" class="danger" @click="$emit('delete-session')">Delete</button>
      </div>
    </header>
    <section id="messages" ref="messages" class="messages" aria-live="polite">
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
    <form id="chat-form" class="composer" @submit.prevent="$emit('submit')">
      <input :value="messageInput" id="message-input" name="message" autocomplete="off" placeholder="Type a message" @input="$emit('update:messageInput', $event.target.value)">
      <button type="submit">Send</button>
    </form>
  </section>
</template>

<script>
export default {
  name: "ChatView",
  props: {
    active: {type: Boolean, required: true},
    activeSessionId: {type: String, required: true},
    messageInput: {type: String, required: true},
    messages: {type: Array, required: true},
    sessions: {type: Array, required: true},
  },
  emits: ["delete-session", "messages-ref", "new-session", "select-session", "submit", "update:messageInput"],
  mounted() {
    this.$emit("messages-ref", this.$refs.messages);
  },
};
</script>
