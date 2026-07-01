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
