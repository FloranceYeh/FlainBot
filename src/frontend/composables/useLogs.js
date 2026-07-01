import {computed, ref} from "vue";
import {clearLogs, loadLogs} from "../api.js";

export function useLogs({setStatus}) {
  const logs = ref([]);
  const selectedLevel = ref("all");
  const selectedSource = ref("all");

  const levelOptions = computed(() => ["all", ...new Set(logs.value.map((log) => log.level).filter(Boolean))]);
  const sourceOptions = computed(() => ["all", ...new Set(logs.value.map((log) => log.source).filter(Boolean))]);
  const filteredLogs = computed(() => logs.value.filter((log) => (
    (selectedLevel.value === "all" || log.level === selectedLevel.value)
    && (selectedSource.value === "all" || log.source === selectedSource.value)
  )));

  async function refreshLogs() {
    const payload = await loadLogs();
    logs.value = payload.logs || [];
  }

  async function clearLogEntries() {
    await clearLogs();
    logs.value = [];
    setStatus("Logs cleared.", "success");
  }

  return {
    clearLogEntries,
    filteredLogs,
    levelOptions,
    logs,
    refreshLogs,
    selectedLevel,
    selectedSource,
    sourceOptions,
  };
}
