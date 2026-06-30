<template>
  <aside id="result-panel" class="result-rail collapsed" :class="{collapsed}" aria-label="Results">
    <button id="toggle-result-panel" class="result-toggle" type="button" :aria-expanded="collapsed ? 'false' : 'true'" title="Toggle generated output" @click="$emit('toggle')">
      <span class="result-toggle-label">Generated Python</span>
    </button>
    <div id="python-panel" class="result-section">
      <div class="result-actions">
        <button id="copy-code" type="button" @click="$emit('copy')">Copy</button>
      </div>
      <pre><code id="python-code">{{ generatedPython }}</code></pre>
    </div>
  </aside>
</template>

<script>
export default {
  name: "ResultRail",
  props: {
    collapsed: {type: Boolean, required: true},
    generatedPython: {type: String, required: true},
  },
  emits: ["copy", "toggle"],
};
</script>
