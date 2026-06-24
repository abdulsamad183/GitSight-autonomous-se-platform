"use client";

import { BaseEdge, type EdgeProps } from "@xyflow/react";

export type StructureEdgeData = {
  targetNodeType?: string;
  highlighted?: boolean;
  dimmed?: boolean;
};

const EDGE_COLORS: Record<string, string> = {
  file: "#0ea5e9",
  class: "#6366f1",
  method: "#a855f7",
  repository: "#8b5cf6",
};

function getEdgeColor(targetNodeType?: string): string {
  if (!targetNodeType) return "#8b5cf6";
  return EDGE_COLORS[targetNodeType] ?? "#8b5cf6";
}

/** Orthogonal tree edge: down from parent → across → down to child, with rounded corners. */
function buildTreePath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
): string {
  const drop = 22;
  const midY = sourceY + drop;
  const radius = 12;

  if (Math.abs(sourceX - targetX) < 2) {
    return `M ${sourceX},${sourceY} C ${sourceX},${(sourceY + targetY) / 2} ${targetX},${(sourceY + targetY) / 2} ${targetX},${targetY}`;
  }

  const dx = targetX - sourceX;
  const sign = dx > 0 ? 1 : -1;
  const r = Math.min(radius, Math.abs(dx) / 2, drop);

  return [
    `M ${sourceX},${sourceY}`,
    `L ${sourceX},${midY - r}`,
    `Q ${sourceX},${midY} ${sourceX + sign * r},${midY}`,
    `L ${targetX - sign * r},${midY}`,
    `Q ${targetX},${midY} ${targetX},${midY + r}`,
    `L ${targetX},${targetY}`,
  ].join(" ");
}

export function StructureEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  style,
  markerEnd,
}: EdgeProps) {
  const edgeData = (data ?? {}) as StructureEdgeData;
  const color = getEdgeColor(edgeData.targetNodeType);
  const highlighted = edgeData.highlighted;
  const dimmed = edgeData.dimmed;

  const path = buildTreePath(sourceX, sourceY, targetX, targetY);

  return (
    <BaseEdge
      id={id}
      path={path}
      markerEnd={markerEnd}
      style={{
        ...style,
        stroke: color,
        strokeWidth: highlighted ? 3 : 2.25,
        strokeLinecap: "round",
        strokeLinejoin: "round",
        opacity: dimmed ? 0.12 : highlighted ? 1 : 0.82,
        filter: highlighted ? `drop-shadow(0 0 4px ${color}88)` : undefined,
        transition: "opacity 150ms, stroke-width 150ms",
      }}
      interactionWidth={20}
    />
  );
}

export const structureEdgeTypes = {
  structureEdge: StructureEdge,
};

export function getStructureEdgeColor(targetNodeType: string): string {
  return getEdgeColor(targetNodeType);
}
