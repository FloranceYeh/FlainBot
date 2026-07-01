const severityRank = {
  error: 3,
  warning: 2,
  info: 1,
};

export function groupLogsByRun(logs) {
  const groups = [];
  const byRunId = new Map();

  for (const log of logs) {
    const runId = log?.details?.run_id;
    const groupId = runId || log.id;
    let group = byRunId.get(groupId);
    if (!group) {
      group = {
        id: groupId,
        level: log.level || "info",
        source: log.source || "system",
        title: log.message || "",
        timestamp: log.timestamp || "",
        logs: [],
      };
      byRunId.set(groupId, group);
      groups.push(group);
    }

    group.logs.push(log);
    group.title = log.message || group.title;
    group.timestamp = log.timestamp || group.timestamp;
    group.source = groupSource(group.logs);
    if ((severityRank[log.level] || 0) >= (severityRank[group.level] || 0)) {
      group.level = log.level || group.level;
    }
  }

  return groups;
}

function groupSource(logs) {
  const sources = [...new Set(logs.map((log) => log.source).filter(Boolean))];
  if (sources.length === 0) {
    return "system";
  }
  if (sources.length === 1) {
    return sources[0];
  }
  return "runtime";
}
