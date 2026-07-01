<template>
  <section id="logs-view" class="view logs-shell" data-view="logs" v-show="active">
    <header class="logs-header">
      <div>
        <h2>Runtime Logs</h2>
        <p>{{ logs.length }} entries</p>
      </div>
      <div class="logs-toolbar">
        <select id="log-level-filter" :value="selectedLevel" @change="$emit('update:selectedLevel', $event.target.value)">
          <option v-for="level in levelOptions" :key="level" :value="level">{{ level }}</option>
        </select>
        <select id="log-source-filter" :value="selectedSource" @change="$emit('update:selectedSource', $event.target.value)">
          <option v-for="source in sourceOptions" :key="source" :value="source">{{ source }}</option>
        </select>
        <button id="refresh-logs" type="button" @click="$emit('refresh')">Refresh</button>
        <button id="clear-logs" type="button" class="danger" @click="$emit('clear')">Clear</button>
      </div>
    </header>

    <section class="logs-list" aria-live="polite">
      <p v-if="filteredLogs.length === 0" class="empty-state">No log entries.</p>
      <article
        v-for="log in filteredLogs"
        v-else
        :key="log.id"
        class="log-entry"
        :class="`level-${log.level}`"
      >
        <div class="log-meta">
          <span class="log-level">{{ log.level }}</span>
          <span class="log-source">{{ log.source }}</span>
          <time>{{ formatTimestamp(log.timestamp) }}</time>
        </div>
        <div class="log-main">
          <h3>{{ log.message }}</h3>
          <details v-if="Object.keys(log.details || {}).length > 0" class="log-details">
            <summary>Details</summary>
            <pre><code>{{ JSON.stringify(log.details || {}, null, 2) }}</code></pre>
          </details>
        </div>
      </article>
    </section>
  </section>
</template>

<script>
export default {
  name: "LogsView",
  props: {
    active: {type: Boolean, required: true},
    filteredLogs: {type: Array, required: true},
    levelOptions: {type: Array, required: true},
    logs: {type: Array, required: true},
    selectedLevel: {type: String, required: true},
    selectedSource: {type: String, required: true},
    sourceOptions: {type: Array, required: true},
  },
  emits: ["clear", "refresh", "update:selectedLevel", "update:selectedSource"],
  methods: {
    formatTimestamp(timestamp) {
      if (!timestamp) {
        return "";
      }
      return new Date(timestamp).toLocaleString();
    },
  },
};
</script>
