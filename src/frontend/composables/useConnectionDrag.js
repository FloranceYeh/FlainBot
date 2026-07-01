import {computed, nextTick, ref} from "vue";
import {connectionArrow, connectionPath, edgeToReplaceForPort, portEdgeAnchor} from "../graph.js";

export function useConnectionDrag({
  graph,
  viewportState,
  canvasEl,
  edgeLayoutTick,
  refreshEdgeLayout,
  findNode,
  edgeKey,
  removeEdgeAt,
  canvasPointFromEvent,
}) {
  const connectionDrag = ref(null);

  const previewConnectionPath = computed(() => {
    if (!connectionDrag.value) {
      return "";
    }
    const from = connectionDrag.value.direction === "output" ? connectionDrag.value.start : connectionDrag.value.current;
    const to = connectionDrag.value.direction === "output" ? connectionDrag.value.current : connectionDrag.value.start;
    return connectionPath(from, to);
  });

  const renderedEdges = computed(() => graph.edges.map((edge, index) => {
    edgeLayoutTick.value;
    const fromNode = findNode(edge.from_node);
    const toNode = findNode(edge.to_node);
    if (!fromNode || !toNode) {
      return null;
    }
    const from = portCenter(edge.from_node, edge.from_port, "output");
    const to = portCenter(edge.to_node, edge.to_port, "input");
    return {key: edgeKey(edge, index), index, from, to, d: connectionPath(from, to), arrow: connectionArrow(from, to)};
  }).filter(Boolean));

  function portCenter(nodeId, port, direction) {
    const selector = `.port[data-node-id="${nodeId}"][data-port="${port}"][data-direction="${direction}"]`;
    const element = document.querySelector(selector);
    if (!element || !canvasEl.value) {
      return {x: 0, y: 0};
    }
    const canvasRect = canvasEl.value.getBoundingClientRect();
    const portRect = element.getBoundingClientRect();
    return portEdgeAnchor(portRect, canvasRect, viewportState, direction);
  }

  function anchorForPort(nodeId, port, direction) {
    return portCenter(nodeId, port, direction);
  }

  function isCompatiblePort(port) {
    if (!connectionDrag.value || !port) {
      return false;
    }
    return port.dataset.nodeId !== connectionDrag.value.nodeId && port.dataset.direction !== connectionDrag.value.direction;
  }

  function closestCompatiblePort(event) {
    const ports = [...document.querySelectorAll(".port")];
    const hitPadding = 18;
    return ports.find((port) => {
      if (!isCompatiblePort(port)) {
        return false;
      }
      const rect = port.getBoundingClientRect();
      return (
        event.clientX >= rect.left - hitPadding
        && event.clientX <= rect.right + hitPadding
        && event.clientY >= rect.top - hitPadding
        && event.clientY <= rect.bottom + hitPadding
      );
    }) || null;
  }

  function startConnectionDrag(event) {
    const port = event.currentTarget;
    event.preventDefault();
    event.stopPropagation();
    const edgeIndex = edgeToReplaceForPort(graph.edges, port.dataset.nodeId, port.dataset.port, port.dataset.direction);
    if (edgeIndex !== -1) {
      removeEdgeAt(edgeIndex);
    }
    connectionDrag.value = {
      nodeId: port.dataset.nodeId,
      port: port.dataset.port,
      direction: port.dataset.direction,
      start: anchorForPort(port.dataset.nodeId, port.dataset.port, port.dataset.direction),
      current: canvasPointFromEvent(event),
    };
    bindConnectionDragEvents();
    port.setPointerCapture(event.pointerId);
  }

  function bindConnectionDragEvents() {
    unbindConnectionDragEvents();
    window.addEventListener("pointermove", handleWindowConnectionPointerMove);
    window.addEventListener("pointerup", handleWindowConnectionPointerUp);
    window.addEventListener("pointercancel", handleWindowConnectionPointerUp);
  }

  function unbindConnectionDragEvents() {
    window.removeEventListener("pointermove", handleWindowConnectionPointerMove);
    window.removeEventListener("pointerup", handleWindowConnectionPointerUp);
    window.removeEventListener("pointercancel", handleWindowConnectionPointerUp);
  }

  function handleWindowConnectionPointerMove(event) {
    moveConnectionDrag(event);
  }

  function handleWindowConnectionPointerUp(event) {
    finishConnectionDrag(event);
  }

  function moveConnectionDrag(event) {
    if (connectionDrag.value) {
      connectionDrag.value.current = canvasPointFromEvent(event);
    }
  }

  function finishConnectionDrag(event) {
    if (!connectionDrag.value) {
      unbindConnectionDragEvents();
      return;
    }
    const target = closestCompatiblePort(event);
    if (isCompatiblePort(target)) {
      const from = connectionDrag.value.direction === "output" ? connectionDrag.value : target.dataset;
      const to = connectionDrag.value.direction === "output" ? target.dataset : connectionDrag.value;
      if (from.nodeId && from.port && to.nodeId && to.port && from.nodeId !== to.nodeId) {
        const edgeIndex = edgeToReplaceForPort(graph.edges, to.nodeId, to.port, "input");
        if (edgeIndex !== -1) {
          removeEdgeAt(edgeIndex);
        }
        graph.edges.push({from_node: from.nodeId, from_port: from.port, to_node: to.nodeId, to_port: to.port});
        nextTick(refreshEdgeLayout);
      }
    }
    connectionDrag.value = null;
    unbindConnectionDragEvents();
  }

  function clearConnectionDrag() {
    connectionDrag.value = null;
  }

  return {
    connectionDrag,
    previewConnectionPath,
    renderedEdges,
    startConnectionDrag,
    moveConnectionDrag,
    finishConnectionDrag,
    clearConnectionDrag,
  };
}
