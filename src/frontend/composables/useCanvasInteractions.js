import {computed, nextTick, reactive, ref} from "vue";
import {
  connectionArrow,
  connectionPath,
  edgeToReplaceForPort,
  nodeDragPosition,
  nodePositionFromCenter,
  portEdgeAnchor,
} from "../graph.js";

export function useCanvasInteractions({
  graph,
  selectedId,
  viewportState,
  edgeLayoutTick,
  refreshEdgeLayout,
  findNode,
  edgeKey,
  addNode,
  removeEdgeAt,
  normalizeGraphCenter,
}) {
  const canvasEl = ref(null);
  const connectionDrag = ref(null);
  const dragState = ref(null);
  const canvasPanState = ref(null);
  const nodePreview = reactive({visible: false, node: null, left: 0, top: 0});

  const canvasSpaceStyle = computed(() => ({
    transform: `translate(${viewportState.x}px, ${viewportState.y}px) scale(${viewportState.scale})`,
  }));

  const previewNode = computed(() => {
    if (!nodePreview.node) {
      return null;
    }
    return {...nodePreview.node, id: "preview", props: JSON.parse(JSON.stringify(nodePreview.node.defaults || {}))};
  });

  const nodePreviewStyle = computed(() => ({
    left: `${nodePreview.left}px`,
    top: `${nodePreview.top}px`,
  }));

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

  function canvasPointFromEvent(event) {
    const canvasRect = canvasEl.value.getBoundingClientRect();
    return {
      x: (event.clientX - canvasRect.left - viewportState.x) / viewportState.scale,
      y: (event.clientY - canvasRect.top - viewportState.y) / viewportState.scale,
    };
  }

  function handleCanvasDrop(event) {
    const type = event.dataTransfer.getData("application/x-flainbot-node-type");
    if (!type) {
      return;
    }
    hideNodePreview();
    addNode(type, nodePositionFromCenter(canvasPointFromEvent(event)));
  }

  function startDrag(event, nodeId) {
    event.preventDefault();
    const node = graph.nodes.find((item) => item.id === nodeId);
    selectedId.value = nodeId;
    dragState.value = {
      nodeId,
      startX: event.clientX,
      startY: event.clientY,
      originX: node.x,
      originY: node.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function dragMove(event) {
    if (!dragState.value) {
      return;
    }
    const node = graph.nodes.find((item) => item.id === dragState.value.nodeId);
    const nextPosition = nodeDragPosition(dragState.value, event, viewportState.scale);
    node.x = nextPosition.x;
    node.y = nextPosition.y;
    nextTick(refreshEdgeLayout);
  }

  function dragEnd() {
    if (dragState.value) {
      normalizeGraphCenter();
      nextTick(refreshEdgeLayout);
    }
    dragState.value = null;
  }

  function zoomCanvas(event) {
    const delta = event.deltaY > 0 ? -0.08 : 0.08;
    viewportState.scale = Math.min(1.8, Math.max(0.45, viewportState.scale + delta));
    nextTick(refreshEdgeLayout);
  }

  function startCanvasPan(event) {
    if (event.target.closest(".graph-node") || event.button !== 1) {
      return;
    }
    event.preventDefault();
    canvasPanState.value = {
      startX: event.clientX,
      startY: event.clientY,
      originX: viewportState.x,
      originY: viewportState.y,
    };
  }

  function moveCanvasPan(event) {
    if (!canvasPanState.value) {
      return;
    }
    viewportState.x = canvasPanState.value.originX + event.clientX - canvasPanState.value.startX;
    viewportState.y = canvasPanState.value.originY + event.clientY - canvasPanState.value.startY;
    nextTick(refreshEdgeLayout);
  }

  function endCanvasPan() {
    canvasPanState.value = null;
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

  function handleCanvasPointerMove(event) {
    dragMove(event);
    moveConnectionDrag(event);
    moveCanvasPan(event);
  }

  function handleCanvasPointerUp(event) {
    dragEnd();
    finishConnectionDrag(event);
    endCanvasPan();
  }

  function moveNodePreview(event) {
    const offset = 12;
    const margin = 12;
    const previewWidth = 270;
    const previewHeight = 216;
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    let left = event.clientX + offset;
    let top = event.clientY + offset;

    if (left + previewWidth + margin > viewportWidth) {
      left = event.clientX - previewWidth - offset;
    }
    if (top + previewHeight + margin > viewportHeight) {
      top = event.clientY - previewHeight - offset;
    }

    nodePreview.left = Math.max(margin, Math.min(left, viewportWidth - previewWidth - margin));
    nodePreview.top = Math.max(margin, Math.min(top, viewportHeight - previewHeight - margin));
  }

  function showNodePreview(node, event) {
    nodePreview.node = node;
    nodePreview.visible = true;
    moveNodePreview(event);
  }

  function hideNodePreview() {
    nodePreview.visible = false;
  }

  function clearConnectionDrag() {
    connectionDrag.value = null;
  }

  return {
    viewportState,
    canvasEl,
    connectionDrag,
    nodePreview,
    canvasSpaceStyle,
    previewNode,
    nodePreviewStyle,
    previewConnectionPath,
    renderedEdges,
    refreshEdgeLayout,
    canvasPointFromEvent,
    handleCanvasDrop,
    startDrag,
    dragMove,
    dragEnd,
    zoomCanvas,
    startCanvasPan,
    moveCanvasPan,
    endCanvasPan,
    startConnectionDrag,
    moveConnectionDrag,
    finishConnectionDrag,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    moveNodePreview,
    showNodePreview,
    hideNodePreview,
    clearConnectionDrag,
  };
}
