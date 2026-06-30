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

export function quote(value) {
  return JSON.stringify(value);
}

export function nodeToPython(node, providers, personas) {
  if (node.type === "chat_input") {
    return `graph.add_node(${quote(node.id)}, ChatInputNode("message from web chat"))`;
  }

  if (node.type === "provider_call") {
    const provider = providers.find((item) => item.id === node.props.provider_id) || {id: node.props.provider_id};
    return `graph.add_node(${quote(node.id)}, ProviderCallNode(provider=${quote(provider)}))`;
  }

  if (node.type === "prompt_builder") {
    return `graph.add_node(${quote(node.id)}, PromptBuilderNode(\n`
      + `    system_prompt=${quote(node.props.system_prompt)},\n`
      + `    user_prompt=${quote(node.props.user_prompt)},\n`
      + `    tools_json=${quote(node.props.tools_json)},\n`
      + `    contexts_json=${quote(node.props.contexts_json)},\n`
      + "))";
  }

  if (node.type === "persona") {
    const persona = personas.find((item) => item.persona_id === node.props.persona_id) || {persona_id: node.props.persona_id};
    return `graph.add_node(${quote(node.id)}, PersonaNode(persona=${quote(persona)}))`;
  }

  return `graph.add_node(${quote(node.id)}, ChatOutputNode())`;
}

export function generatePython(graph, providers, personas) {
  const imports = new Set(["Graph", "GraphExecutor"]);
  graph.nodes.forEach((node) => imports.add(node.className));
  const importLine = `from flainbot import ${Array.from(imports).sort().join(", ")}`;
  const nodeLines = graph.nodes.length > 0 ? graph.nodes.map((node) => nodeToPython(node, providers, personas)).join("\n") : "# Add nodes in the planner";
  const edgeLines = graph.edges.map((edge) => (
    `graph.connect(${quote(edge.from_node)}, ${quote(edge.from_port)}, ${quote(edge.to_node)}, ${quote(edge.to_port)})`
  )).join("\n");

  return `${importLine}\n\n\ngraph = Graph()\n${nodeLines}\n${edgeLines ? `${edgeLines}\n` : ""}outputs = GraphExecutor(graph).run()\nprint(outputs)\n`;
}

export function parseJsonOrEmpty(value, emptyValue) {
  const trimmed = value.trim();
  return trimmed ? JSON.parse(trimmed) : emptyValue;
}
