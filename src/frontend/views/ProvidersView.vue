<template>
  <section id="providers-view" class="view providers-shell" data-view="providers" v-show="active">
    <section class="panel provider-editor" aria-labelledby="providers-title">
      <div class="section-header">
        <h2 id="providers-title">Providers</h2>
        <span class="count">Create reusable provider configs for Call Provider nodes.</span>
      </div>
      <form id="provider-form" class="provider-form" autocomplete="off" @submit.prevent="$emit('submit', $event)">
        <div class="field">
          <label>ID</label>
          <input v-model="providerForm.id" name="id" placeholder="provider-id" required>
        </div>
        <div class="field">
          <label>Format</label>
          <select v-model="providerForm.format" name="format">
            <option value="openai_chat">OpenAI Chat</option>
            <option value="anthropic_messages">Anthropic Messages</option>
          </select>
        </div>
        <div class="field">
          <label>Base URL</label>
          <input v-model="providerForm.base_url" name="base_url" placeholder="provider-base-url" required>
        </div>
        <div class="field">
          <label>API Key</label>
          <input v-model="providerForm.api_key" name="api_key">
        </div>
        <div class="field">
          <label>Model</label>
          <input v-model="providerForm.model" name="model" placeholder="your-model-name" required>
        </div>
        <button type="submit">Save Provider</button>
      </form>
    </section>
    <section class="panel provider-list-panel" aria-labelledby="provider-list-title">
      <div class="section-header">
        <h2 id="provider-list-title">Configured Providers</h2>
      </div>
      <div id="provider-list" class="provider-list">
        <p v-if="providers.length === 0" class="empty-state">No providers configured.</p>
        <article v-for="provider in providers" :key="provider.id" class="provider-card">
          <div>
            <span class="node-type">{{ provider.format }}</span>
            <h3>{{ provider.id }}</h3>
            <p>{{ provider.base_url }} / {{ provider.model }}</p>
          </div>
          <button type="button" class="danger" :data-remove-provider="provider.id" @click="$emit('remove', provider.id)">Remove</button>
        </article>
      </div>
    </section>
  </section>
</template>

<script>
export default {
  name: "ProvidersView",
  props: {
    active: {type: Boolean, required: true},
    providerForm: {type: Object, required: true},
    providers: {type: Array, required: true},
  },
  emits: ["remove", "submit"],
};
</script>
