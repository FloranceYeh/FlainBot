import {computed, ref} from "vue";
import {clearLogs, loadLogs, logStreamUrl} from "../api.js";
import {groupLogsByRun} from "../logs.js";

export function useLogs({setStatus}) {
  const logs = ref([]);
  const selectedLevel = ref("all");
  const selectedSource = ref("all");
  const logStream = ref(null);

  const levelOptions = computed(() => ["all", ...new Set(logs.value.map((log) => log.level).filter(Boolean))]);
  const sourceOptions = computed(() => ["all", ...new Set(logs.value.map((log) => log.source).filter(Boolean))]);
  const filteredLogs = computed(() => logs.value.filter((log) => (
    (selectedLevel.value === "all" || log.level === selectedLevel.value)
    && (selectedSource.value === "all" || log.source === selectedSource.value)
  )));
  const filteredLogGroups = computed(() => groupLogsByRun(filteredLogs.value));

  async function refreshLogs() {
    const payload = await loadLogs();
    logs.value = payload.logs || [];
  }

  function appendLogEntry(log) {
    if (!log || !log.id || logs.value.some((entry) => entry.id === log.id)) {
      return;
    }
    logs.value = [...logs.value, log];
  }

  function startLogStream() {
    if (logStream.value || typeof EventSource === "undefined") {
      return;
    }
    const stream = new EventSource(logStreamUrl());
    stream.onmessage = (event) => {
      try {
        appendLogEntry(JSON.parse(event.data));
      } catch (error) {
        setStatus("Log stream event could not be parsed.", "error");
      }
    };
    stream.onerror = () => {
      setStatus("Log stream reconnecting.", "error");
    };
    logStream.value = stream;
  }

  function stopLogStream() {
    if (!logStream.value) {
      return;
    }
    logStream.value.close();
    logStream.value = null;
  }

  async function clearLogEntries() {
    await clearLogs();
    logs.value = [];
    setStatus("Logs cleared.", "success");
  }

  return {
    clearLogEntries,
    filteredLogGroups,
    filteredLogs,
    levelOptions,
    logs,
    refreshLogs,
    selectedLevel,
    selectedSource,
    sourceOptions,
    startLogStream,
    stopLogStream,
  };
}
