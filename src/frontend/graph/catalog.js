export function portName(port) {
  return typeof port === "string" ? port : port.name;
}

export function portType(port) {
  return typeof port === "string" ? "any" : port.type;
}

export function portsText(ports) {
  return ports.map((port) => `${portName(port)} ${portType(port)}`).join(" ");
}

export function collectCatalogNodes(items, packageInfo = {}) {
  return items.flatMap((item) => {
    if (item.kind === "node") {
      return [{...item, packageId: item.package || packageInfo.id, packageTitle: packageInfo.title}];
    }
    if (item.kind === "group") {
      return collectCatalogNodes(item.items || [], packageInfo);
    }
    return [];
  });
}

export function flattenNodeCatalog(packages) {
  return packages.flatMap((packageItem) => (
    collectCatalogNodes(packageItem.items || [], {
      id: packageItem.id,
      title: packageItem.title,
    })
  ));
}

export function filterOptions(nodes, portDirection) {
  if (portDirection === "package") {
    return [...new Set(nodes.map((node) => node.packageId || node.package).filter(Boolean))].sort();
  }
  return [...new Set(nodes.flatMap((node) => (
    (portDirection === "input" ? node.inputs : node.outputs).map(portType)
  )))].sort();
}

export function nodeMatchesFilters(node, filters) {
  if (filters.selectedPackage.length > 0 && !filters.selectedPackage.includes(node.packageId || node.package)) {
    return false;
  }
  if (
    filters.selectedInputType.length > 0
    && !(node.inputs || []).some((port) => filters.selectedInputType.includes(portType(port)))
  ) {
    return false;
  }
  if (
    filters.selectedOutputType.length > 0
    && !(node.outputs || []).some((port) => filters.selectedOutputType.includes(portType(port)))
  ) {
    return false;
  }
  return true;
}

export function catalogText(item) {
  if (item.kind === "node") {
    return [
      item.type,
      item.className,
      item.title,
      item.description,
      item.package,
      item.packageId,
      item.packageTitle,
      portsText(item.inputs || []),
      portsText(item.outputs || []),
    ].join(" ").toLowerCase();
  }
  return `${item.id} ${item.title} ${item.description || ""}`.toLowerCase();
}

export function filterCatalogItems(items, query, filters) {
  return items.flatMap((item) => {
    if (item.kind === "node") {
      return catalogText(item).includes(query) && nodeMatchesFilters(item, filters) ? [item] : [];
    }
    if (item.kind !== "group") {
      return [];
    }
    if (catalogText(item).includes(query)) {
      const children = filterCatalogItems(item.items || [], "", filters);
      return children.length > 0 ? [{...item, items: children}] : [];
    }
    const children = filterCatalogItems(item.items || [], query, filters);
    return children.length > 0 ? [{...item, items: children}] : [];
  });
}

export function filterNodeCatalog(nodeCatalog, query, filters) {
  const hasFilters = filters.selectedPackage.length > 0 || filters.selectedInputType.length > 0 || filters.selectedOutputType.length > 0;
  if (!query && !hasFilters) {
    return nodeCatalog;
  }
  return nodeCatalog.flatMap((packageItem) => {
    if (catalogText(packageItem).includes(query)) {
      const children = filterCatalogItems(packageItem.items || [], "", filters);
      return children.length > 0 ? [{...packageItem, items: children}] : [];
    }
    const children = filterCatalogItems(packageItem.items || [], query, filters);
    return children.length > 0 ? [{...packageItem, items: children}] : [];
  });
}
