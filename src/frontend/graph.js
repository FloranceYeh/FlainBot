export function cloneDefaults(defaults) {
  return JSON.parse(JSON.stringify(defaults));
}

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

export function connectionPath(from, to) {
  const curve = Math.max(60, Math.abs(to.x - from.x) / 2);
  return `M ${from.x} ${from.y} C ${from.x + curve} ${from.y}, ${to.x - curve} ${to.y}, ${to.x} ${to.y}`;
}

export function connectionArrow(from, to) {
  const curve = Math.max(60, Math.abs(to.x - from.x) / 2);
  const point = cubicPoint(
    from,
    {x: from.x + curve, y: from.y},
    {x: to.x - curve, y: to.y},
    to,
    0.5,
  );
  const tangent = cubicTangent(
    from,
    {x: from.x + curve, y: from.y},
    {x: to.x - curve, y: to.y},
    to,
    0.5,
  );
  return {
    x: point.x,
    y: point.y,
    angle: Math.atan2(tangent.y, tangent.x) * 180 / Math.PI,
  };
}

export function portEdgeAnchor(portRect, canvasRect, viewportState, direction) {
  const edgeX = direction === "output" ? portRect.right : portRect.left;
  return {
    x: (edgeX - canvasRect.left - viewportState.x) / viewportState.scale,
    y: (portRect.top - canvasRect.top + portRect.height / 2 - viewportState.y) / viewportState.scale,
  };
}

export function edgeToReplaceForPort(edges, nodeId, port, direction) {
  if (direction !== "input") {
    return -1;
  }
  return edges.findIndex((edge) => edge.to_node === nodeId && edge.to_port === port);
}

function cubicPoint(start, controlA, controlB, end, t) {
  const mt = 1 - t;
  return {
    x: mt ** 3 * start.x + 3 * mt ** 2 * t * controlA.x + 3 * mt * t ** 2 * controlB.x + t ** 3 * end.x,
    y: mt ** 3 * start.y + 3 * mt ** 2 * t * controlA.y + 3 * mt * t ** 2 * controlB.y + t ** 3 * end.y,
  };
}

function cubicTangent(start, controlA, controlB, end, t) {
  const mt = 1 - t;
  return {
    x: 3 * mt ** 2 * (controlA.x - start.x) + 6 * mt * t * (controlB.x - controlA.x) + 3 * t ** 2 * (end.x - controlB.x),
    y: 3 * mt ** 2 * (controlA.y - start.y) + 6 * mt * t * (controlB.y - controlA.y) + 3 * t ** 2 * (end.y - controlB.y),
  };
}

export function quote(value) {
  return JSON.stringify(value);
}

export function generatePython(graph, providers, personas) {
  const config = {
    nodes: graph.nodes.map((node) => ({
      id: node.id,
      type: node.type,
      props: node.props || {},
    })),
    edges: graph.edges,
    providers,
    personas,
  };
  const configJson = JSON.stringify(config, null, 2);

  return `import json\n\nfrom flainbot import GraphExecutor\nfrom flainbot.config import build_graph_from_config\n\n\nconfig = json.loads(${quote(configJson)})\ngraph = build_graph_from_config(config, message="message from web chat")\noutputs = GraphExecutor(graph).run()\nprint(outputs)\n`;
}

export function parseJsonOrEmpty(value, emptyValue) {
  const trimmed = value.trim();
  return trimmed ? JSON.parse(trimmed) : emptyValue;
}
