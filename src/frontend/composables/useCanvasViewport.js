import {computed, nextTick, ref} from "vue";

export function useCanvasViewport({viewportState, refreshEdgeLayout}) {
  const canvasEl = ref(null);
  const canvasPanState = ref(null);

  const canvasSpaceStyle = computed(() => ({
    transform: `translate(${viewportState.x}px, ${viewportState.y}px) scale(${viewportState.scale})`,
  }));

  function canvasPointFromEvent(event) {
    const canvasRect = canvasEl.value.getBoundingClientRect();
    return {
      x: (event.clientX - canvasRect.left - viewportState.x) / viewportState.scale,
      y: (event.clientY - canvasRect.top - viewportState.y) / viewportState.scale,
    };
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

  return {
    canvasEl,
    canvasSpaceStyle,
    canvasPointFromEvent,
    zoomCanvas,
    startCanvasPan,
    moveCanvasPan,
    endCanvasPan,
  };
}
