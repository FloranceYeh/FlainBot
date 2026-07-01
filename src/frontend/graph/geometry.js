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

export function graphNodeCenter(nodes) {
  if (nodes.length === 0) {
    return null;
  }
  const bounds = nodes.reduce((acc, node) => ({
    minX: Math.min(acc.minX, node.x),
    maxX: Math.max(acc.maxX, node.x),
    minY: Math.min(acc.minY, node.y),
    maxY: Math.max(acc.maxY, node.y),
  }), {
    minX: nodes[0].x,
    maxX: nodes[0].x,
    minY: nodes[0].y,
    maxY: nodes[0].y,
  });
  return {
    x: (bounds.minX + bounds.maxX) / 2,
    y: (bounds.minY + bounds.maxY) / 2,
  };
}

export function nodeDragPosition(dragState, pointerEvent, scale) {
  return {
    x: dragState.originX + (pointerEvent.clientX - dragState.startX) / scale,
    y: dragState.originY + (pointerEvent.clientY - dragState.startY) / scale,
  };
}

export function nodePositionFromCenter(center, size = {width: 270, height: 270}) {
  return {
    x: center.x - size.width / 2,
    y: center.y - size.height / 2,
  };
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
