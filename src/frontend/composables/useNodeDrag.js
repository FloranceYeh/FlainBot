import {computed, nextTick, reactive, ref} from "vue";
import {cloneDefaults, nodeDragPosition, nodePositionFromCenter} from "../graph.js";

export function useNodeDrag({
  graph,
  selectedId,
  viewportState,
  refreshEdgeLayout,
  addNode,
  normalizeGraphCenter,
  canvasPointFromEvent,
}) {
  const dragState = ref(null);
  const nodePreview = reactive({visible: false, node: null, left: 0, top: 0});

  const previewNode = computed(() => {
    if (!nodePreview.node) {
      return null;
    }
    return {...nodePreview.node, id: "preview", props: cloneDefaults(nodePreview.node.defaults || {})};
  });

  const nodePreviewStyle = computed(() => ({
    left: `${nodePreview.left}px`,
    top: `${nodePreview.top}px`,
  }));

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

  return {
    nodePreview,
    previewNode,
    nodePreviewStyle,
    handleCanvasDrop,
    startDrag,
    dragMove,
    dragEnd,
    moveNodePreview,
    showNodePreview,
    hideNodePreview,
  };
}
