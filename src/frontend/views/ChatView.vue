<template>
  <section id="chat-view" class="view chat-shell" data-view="chat" v-show="active">
    <header class="chat-header">
      <h2>FlainBot Chat</h2>
      <p>Graph runtime: input node to model node to output node.</p>
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
    messageInput: {type: String, required: true},
    messages: {type: Array, required: true},
  },
  emits: ["messages-ref", "submit", "update:messageInput"],
  mounted() {
    this.$emit("messages-ref", this.$refs.messages);
  },
};
</script>
