import {reactive, ref} from "vue";
import {savePersonas} from "../api.js";
import {parseJsonOrEmpty} from "../graph.js";

export function usePersonaSettings({setStatus}) {
  const personas = ref([]);
  const personaEditingId = ref("");
  const personaForm = reactive({
    persona_id: "",
    system_prompt: "",
    begin_dialogs: "",
    tools_json: "",
    skills_json: "",
    custom_error_message: "",
  });

  async function handlePersonaSubmit(event) {
    const form = event.currentTarget;
    try {
      const persona = {
        persona_id: personaForm.persona_id.trim(),
        system_prompt: personaForm.system_prompt.trim(),
        begin_dialogs: personaForm.begin_dialogs.split("\n").map((line) => line.trim()).filter(Boolean),
        tools: parseJsonOrEmpty(personaForm.tools_json, []),
        skills: parseJsonOrEmpty(personaForm.skills_json, []),
        custom_error_message: personaForm.custom_error_message.trim() || null,
      };
      personas.value = personas.value.filter((item) => item.persona_id !== (personaEditingId.value || persona.persona_id));
      personas.value.push(persona);
      await savePersonas(personas.value);
      personaEditingId.value = "";
      Object.assign(personaForm, {
        persona_id: "",
        system_prompt: "",
        begin_dialogs: "",
        tools_json: "",
        skills_json: "",
        custom_error_message: "",
      });
      form.reset();
      setStatus("Persona saved.", "success");
    } catch (error) {
      setStatus(error.message, "error");
    }
  }

  function editPersona(persona) {
    personaEditingId.value = persona.persona_id;
    Object.assign(personaForm, {
      persona_id: persona.persona_id,
      system_prompt: persona.system_prompt,
      begin_dialogs: persona.begin_dialogs.join("\n"),
      tools_json: JSON.stringify(persona.tools || [], null, 2),
      skills_json: JSON.stringify(persona.skills || [], null, 2),
      custom_error_message: persona.custom_error_message || "",
    });
  }

  async function removePersona(personaId) {
    personas.value = personas.value.filter((item) => item.persona_id !== personaId);
    if (personaEditingId.value === personaId) {
      personaEditingId.value = "";
      Object.assign(personaForm, {
        persona_id: "",
        system_prompt: "",
        begin_dialogs: "",
        tools_json: "",
        skills_json: "",
        custom_error_message: "",
      });
    }
    await savePersonas(personas.value);
  }

  return {
    personas,
    personaEditingId,
    personaForm,
    handlePersonaSubmit,
    editPersona,
    removePersona,
  };
}
