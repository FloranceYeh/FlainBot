export function cloneDefaults(defaults) {
  return JSON.parse(JSON.stringify(defaults));
}

export function parseJsonOrEmpty(value, emptyValue) {
  const trimmed = value.trim();
  return trimmed ? JSON.parse(trimmed) : emptyValue;
}
