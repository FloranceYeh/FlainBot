<template>
  <section id="personas-view" class="view personas-shell" data-view="personas" v-show="active">
    <section class="panel persona-editor" aria-labelledby="personas-title">
      <div class="section-header">
        <h2 id="personas-title">Personas</h2>
        <span class="count">Create reusable prompt profiles for Apply Persona nodes.</span>
      </div>
      <form id="persona-form" class="persona-form" autocomplete="off" @submit.prevent="$emit('submit', $event)">
        <div class="field">
          <label>ID</label>
          <input v-model="personaForm.persona_id" name="persona_id" placeholder="persona-id" required>
        </div>
        <div class="field">
          <label>System Prompt</label>
          <textarea v-model="personaForm.system_prompt" name="system_prompt" placeholder="system-prompt" required></textarea>
        </div>
        <div class="field">
          <label>Begin Dialogs</label>
          <textarea v-model="personaForm.begin_dialogs" name="begin_dialogs" placeholder="user and assistant lines"></textarea>
        </div>
        <div class="field">
          <label>Tools JSON</label>
          <textarea v-model="personaForm.tools_json" name="tools_json" placeholder="[]"></textarea>
        </div>
        <div class="field">
          <label>Skills JSON</label>
          <textarea v-model="personaForm.skills_json" name="skills_json" placeholder="[]"></textarea>
        </div>
        <div class="field">
          <label>Custom Error Message</label>
          <input v-model="personaForm.custom_error_message" name="custom_error_message" placeholder="fallback-message">
        </div>
        <button type="submit">Save Persona</button>
      </form>
    </section>
    <section class="panel persona-list-panel" aria-labelledby="persona-list-title">
      <div class="section-header">
        <h2 id="persona-list-title">Configured Personas</h2>
      </div>
      <div id="persona-list" class="persona-list">
        <p v-if="personas.length === 0" class="empty-state">No personas configured.</p>
        <article v-for="persona in personas" :key="persona.persona_id" class="persona-card">
          <div>
            <span class="node-type">{{ persona.begin_dialogs.length }} begin dialogs</span>
            <h3>{{ persona.persona_id }}</h3>
            <p>{{ persona.system_prompt }}</p>
          </div>
          <div class="card-actions">
            <button type="button" :data-edit-persona="persona.persona_id" @click="$emit('edit', persona)">Edit</button>
            <button type="button" class="danger" :data-remove-persona="persona.persona_id" @click="$emit('remove', persona.persona_id)">Remove</button>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script>
export default {
  name: "PersonasView",
  props: {
    active: {type: Boolean, required: true},
    personaForm: {type: Object, required: true},
    personas: {type: Array, required: true},
  },
  emits: ["edit", "remove", "submit"],
};
</script>
