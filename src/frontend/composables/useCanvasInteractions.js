import {useCanvasViewport} from "./useCanvasViewport.js";
import {useConnectionDrag} from "./useConnectionDrag.js";
import {useNodeDrag} from "./useNodeDrag.js";

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
  const viewport = useCanvasViewport({viewportState, refreshEdgeLayout});
  const nodeDrag = useNodeDrag({
    graph,
    selectedId,
    viewportState,
    refreshEdgeLayout,
    addNode,
    normalizeGraphCenter,
    canvasPointFromEvent: viewport.canvasPointFromEvent,
  });
  const connectionDrag = useConnectionDrag({
    graph,
    viewportState,
    canvasEl: viewport.canvasEl,
    edgeLayoutTick,
    refreshEdgeLayout,
    findNode,
    edgeKey,
    removeEdgeAt,
    canvasPointFromEvent: viewport.canvasPointFromEvent,
  });

  function handleCanvasPointerMove(event) {
    nodeDrag.dragMove(event);
    connectionDrag.moveConnectionDrag(event);
    viewport.moveCanvasPan(event);
  }

  function handleCanvasPointerUp(event) {
    nodeDrag.dragEnd();
    connectionDrag.finishConnectionDrag(event);
    viewport.endCanvasPan();
  }

  return {
    viewportState,
    canvasEl: viewport.canvasEl,
    connectionDrag: connectionDrag.connectionDrag,
    nodePreview: nodeDrag.nodePreview,
    canvasSpaceStyle: viewport.canvasSpaceStyle,
    previewNode: nodeDrag.previewNode,
    nodePreviewStyle: nodeDrag.nodePreviewStyle,
    previewConnectionPath: connectionDrag.previewConnectionPath,
    renderedEdges: connectionDrag.renderedEdges,
    refreshEdgeLayout,
    canvasPointFromEvent: viewport.canvasPointFromEvent,
    handleCanvasDrop: nodeDrag.handleCanvasDrop,
    startDrag: nodeDrag.startDrag,
    dragMove: nodeDrag.dragMove,
    dragEnd: nodeDrag.dragEnd,
    zoomCanvas: viewport.zoomCanvas,
    startCanvasPan: viewport.startCanvasPan,
    moveCanvasPan: viewport.moveCanvasPan,
    endCanvasPan: viewport.endCanvasPan,
    startConnectionDrag: connectionDrag.startConnectionDrag,
    moveConnectionDrag: connectionDrag.moveConnectionDrag,
    finishConnectionDrag: connectionDrag.finishConnectionDrag,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    moveNodePreview: nodeDrag.moveNodePreview,
    showNodePreview: nodeDrag.showNodePreview,
    hideNodePreview: nodeDrag.hideNodePreview,
    clearConnectionDrag: connectionDrag.clearConnectionDrag,
  };
}
