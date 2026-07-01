import {reactive, ref} from "vue";
import {saveProviders} from "../api.js";

export function useProviderSettings({setStatus}) {
  const providers = ref([]);
  const providerEditingId = ref("");
  const providerForm = reactive({id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});

  async function handleProviderSubmit(event) {
    const form = event.currentTarget;
    const provider = {
      id: providerForm.id.trim(),
      format: providerForm.format,
      base_url: providerForm.base_url.trim(),
      api_key: providerForm.api_key,
      model: providerForm.model.trim(),
    };
    providers.value = providers.value.filter((item) => item.id !== (providerEditingId.value || provider.id));
    providers.value.push(provider);
    try {
      await saveProviders(providers.value);
      providerEditingId.value = "";
      Object.assign(providerForm, {id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
      form.reset();
      setStatus("Provider saved.", "success");
    } catch (error) {
      setStatus(error.message, "error");
    }
  }

  function editProvider(provider) {
    providerEditingId.value = provider.id;
    Object.assign(providerForm, {
      id: provider.id,
      format: provider.format,
      base_url: provider.base_url,
      api_key: provider.api_key,
      model: provider.model,
    });
  }

  async function removeProvider(id) {
    providers.value = providers.value.filter((item) => item.id !== id);
    if (providerEditingId.value === id) {
      providerEditingId.value = "";
      Object.assign(providerForm, {id: "", format: "openai_chat", base_url: "", api_key: "", model: ""});
    }
    await saveProviders(providers.value);
  }

  return {
    providers,
    providerEditingId,
    providerForm,
    handleProviderSubmit,
    editProvider,
    removeProvider,
  };
}
