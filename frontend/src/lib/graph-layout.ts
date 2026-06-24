import type { Edge, Node } from "@xyflow/react";

const NODE_WIDTH = 180;
const NODE_HEIGHT = 56;

export const nodeDimensions: Record<string, { width: number; height: number }> = {
  repository: { width: 200, height: 64 },
  file: { width: 170, height: 52 },
  class: { width: 165, height: 50 },
  method: { width: 150, height: 46 },
};

const H_GAP = 28;
const V_GAP = 76;

function getDim(node: Node): { width: number; height: number } {
  const nodeType = (node.data as { nodeType: string }).nodeType;
  return nodeDimensions[nodeType] ?? { width: NODE_WIDTH, height: NODE_HEIGHT };
}

function gridColumns(count: number, nodeType?: string): number {
  if (count <= 1) return 1;
  if (nodeType === "repository") {
    return Math.min(count, Math.max(3, Math.ceil(Math.sqrt(count))));
  }
  if (nodeType === "file") {
    return Math.min(count, Math.max(2, Math.ceil(Math.sqrt(count))));
  }
  return Math.min(count, Math.max(2, Math.ceil(Math.sqrt(count))));
}

function buildChildrenMap(edges: Edge[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const edge of edges) {
    const siblings = map.get(edge.source) ?? [];
    siblings.push(edge.target);
    map.set(edge.source, siblings);
  }
  for (const [, children] of map) {
    children.sort();
  }
  return map;
}

function findRootId(nodes: Node[], edges: Edge[]): string {
  const hasParent = new Set(edges.map((edge) => edge.target));
  return nodes.find((node) => !hasParent.has(node.id))?.id ?? nodes[0]?.id ?? "";
}

interface SubtreeLayout {
  width: number;
  height: number;
  positions: Map<string, { x: number; y: number }>;
}

function layoutSubtree(
  nodeId: string,
  nodeMap: Map<string, Node>,
  childrenMap: Map<string, string[]>,
): SubtreeLayout {
  const node = nodeMap.get(nodeId);
  if (!node) {
    return { width: 0, height: 0, positions: new Map() };
  }

  const dim = getDim(node);
  const nodeType = (node.data as { nodeType: string }).nodeType;
  const childIds = childrenMap.get(nodeId) ?? [];

  if (childIds.length === 0) {
    return {
      width: dim.width,
      height: dim.height,
      positions: new Map([[nodeId, { x: 0, y: 0 }]]),
    };
  }

  const childLayouts = childIds.map((id) => layoutSubtree(id, nodeMap, childrenMap));
  const cols = gridColumns(childIds.length, nodeType);
  const rowCount = Math.ceil(childIds.length / cols);

  const rows: Array<{ layouts: SubtreeLayout[]; width: number; height: number }> = [];
  for (let row = 0; row < rowCount; row += 1) {
    const rowLayouts = childLayouts.slice(row * cols, row * cols + cols);
    const rowWidth = rowLayouts.reduce(
      (sum, layout, index) => sum + layout.width + (index > 0 ? H_GAP : 0),
      0,
    );
    const rowHeight = Math.max(...rowLayouts.map((layout) => layout.height), 0);
    rows.push({ layouts: rowLayouts, width: rowWidth, height: rowHeight });
  }

  const gridWidth = Math.max(...rows.map((row) => row.width), dim.width);
  const gridHeight = rows.reduce(
    (sum, row, index) => sum + row.height + (index > 0 ? V_GAP : 0),
    0,
  );

  const positions = new Map<string, { x: number; y: number }>();
  let childY = dim.height + V_GAP;

  for (const row of rows) {
    let childX = (gridWidth - row.width) / 2;
    for (const layout of row.layouts) {
      for (const [id, pos] of layout.positions) {
        positions.set(id, { x: childX + pos.x, y: childY + pos.y });
      }
      childX += layout.width + H_GAP;
    }
    childY += row.height + V_GAP;
  }

  positions.set(nodeId, { x: gridWidth / 2 - dim.width / 2, y: 0 });

  return {
    width: gridWidth,
    height: dim.height + V_GAP + gridHeight,
    positions,
  };
}

/** Squarish tree layout: siblings wrap in a grid instead of one long row. */
export function layoutStructureGraph(nodes: Node[], edges: Edge[]): Node[] {
  if (nodes.length === 0) return nodes;

  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const childrenMap = buildChildrenMap(edges);
  const rootId = findRootId(nodes, edges);
  const { positions } = layoutSubtree(rootId, nodeMap, childrenMap);

  let minX = Infinity;
  let minY = Infinity;
  for (const pos of positions.values()) {
    minX = Math.min(minX, pos.x);
    minY = Math.min(minY, pos.y);
  }

  const offsetX = Number.isFinite(minX) ? -minX + 40 : 40;
  const offsetY = Number.isFinite(minY) ? -minY + 40 : 40;

  return nodes.map((node) => {
    const pos = positions.get(node.id) ?? { x: 0, y: 0 };
    return {
      ...node,
      position: {
        x: pos.x + offsetX,
        y: pos.y + offsetY,
      },
    };
  });
}
