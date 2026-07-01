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
        <button id="clear-logs" type="button" class="danger" @click="$emit('clear')">Clear</button>
      </div>
    </header>

    <section class="logs-list" aria-live="polite">
      <p v-if="filteredLogGroups.length === 0" class="empty-state">No log entries.</p>
      <article
        v-for="group in filteredLogGroups"
        v-else
        :key="group.id"
        class="run-log-group"
        :class="`level-${group.level}`"
      >
        <header class="run-log-header">
          <div>
            <div class="log-meta">
              <span class="log-level">{{ group.level }}</span>
              <span class="log-source">{{ group.source }}</span>
              <time>{{ formatTimestamp(group.timestamp) }}</time>
            </div>
            <h3>{{ group.title }}</h3>
          </div>
          <span class="run-log-count">{{ group.logs.length }} events</span>
        </header>
        <div class="run-log-events">
          <section
            v-for="log in group.logs"
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
              <h4>{{ log.message }}</h4>
              <div class="log-facts">
                <span v-if="log.details?.event" class="log-event">{{ log.details.event }}</span>
                <span v-if="log.details?.node_id" class="log-node">{{ log.details.node_id }}</span>
              </div>
              <details v-if="Object.keys(log.details || {}).length > 0" class="log-details">
                <summary>Details</summary>
                <pre><code>{{ JSON.stringify(log.details || {}, null, 2) }}</code></pre>
              </details>
            </div>
          </section>
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
    filteredLogGroups: {type: Array, required: true},
    filteredLogs: {type: Array, required: true},
    levelOptions: {type: Array, required: true},
    logs: {type: Array, required: true},
    selectedLevel: {type: String, required: true},
    selectedSource: {type: String, required: true},
    sourceOptions: {type: Array, required: true},
  },
  emits: ["clear", "update:selectedLevel", "update:selectedSource"],
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
