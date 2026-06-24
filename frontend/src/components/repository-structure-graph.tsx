"use client";

import { useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { structureNodeTypes } from "@/components/graph-custom-nodes";
import {
  getStructureEdgeColor,
  structureEdgeTypes,
} from "@/components/graph-structure-edge";
import { layoutStructureGraph } from "@/lib/graph-layout";
import type { RepositoryGraph } from "@/types/graph";

function toFlowElements(
  graph: RepositoryGraph,
  branch: string | null,
  hoveredNodeId: string | null,
): { nodes: Node[]; edges: Edge[] } {
  const nodeTypeById = new Map(graph.nodes.map((node) => [node.id, node.type]));

  const nodes: Node[] = graph.nodes.map((node) => ({
    id: node.id,
    type: "structureNode",
    position: { x: 0, y: 0 },
    data: {
      label: node.label,
      nodeType: node.type,
      metadata: node.metadata,
      branch,
    },
  }));

  const rawEdges: Edge[] = graph.edges.map((edge) => {
    const targetType = nodeTypeById.get(edge.target) ?? "method";
    const color = getStructureEdgeColor(targetType);
    const isConnected =
      hoveredNodeId !== null &&
      (edge.source === hoveredNodeId || edge.target === hoveredNodeId);

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "structureEdge",
      data: {
        targetNodeType: targetType,
        highlighted: isConnected,
        dimmed: hoveredNodeId !== null && !isConnected,
      },
      style: { stroke: color },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color,
        width: isConnected ? 18 : 14,
        height: isConnected ? 18 : 14,
      },
      zIndex: 0,
    };
  });

  const laidOutNodes = layoutStructureGraph(nodes, rawEdges).map((node) => ({
    ...node,
    zIndex: node.id === hoveredNodeId ? 1000 : 0,
  }));

  return {
    nodes: laidOutNodes,
    edges: rawEdges.map((edge) => ({ ...edge, zIndex: 0 })),
  };
}

interface RepositoryStructureGraphProps {
  graph: RepositoryGraph;
  branch: string | null;
}

export function RepositoryStructureGraph({ graph, branch }: RepositoryStructureGraphProps) {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const { nodes, edges } = useMemo(
    () => toFlowElements(graph, branch, hoveredNodeId),
    [graph, branch, hoveredNodeId],
  );

  const onNodeMouseEnter = useCallback((_: React.MouseEvent, node: Node) => {
    setHoveredNodeId(node.id);
  }, []);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredNodeId(null);
  }, []);

  return (
    <div className="h-full w-full [&_.react-flow__edges]:!z-[1] [&_.react-flow__nodes]:!z-[10] [&_.react-flow__node]:!overflow-visible">
      <ReactFlow
        key={graph.branch ?? "default"}
        nodes={nodes}
        edges={edges}
        nodeTypes={structureNodeTypes}
        edgeTypes={structureEdgeTypes}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable={false}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        fitView
        fitViewOptions={{ padding: 0.2, minZoom: 0.2, maxZoom: 1.5 }}
        minZoom={0.05}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#c4b5fd" gap={24} size={1} />
        <Controls className="!rounded-xl !border !border-violet-200 !bg-white/90 !shadow-md" />
        <MiniMap
          className="!rounded-xl !border !border-violet-200 !bg-white/90"
          pannable
          zoomable
          nodeColor={(node) => {
            const nodeType = (node.data as { nodeType: string }).nodeType;
            if (nodeType === "repository") return "#7c3aed";
            if (nodeType === "file") return "#0ea5e9";
            if (nodeType === "class") return "#6366f1";
            return "#a78bfa";
          }}
        />
      </ReactFlow>
    </div>
  );
}
