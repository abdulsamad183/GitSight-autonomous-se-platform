"use client";

import { useRef, useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Box, FileCode2, FolderGit2, FunctionSquare } from "lucide-react";

import { GraphNodeHoverCard } from "@/components/graph-node-hover-card";
import {
  popupArrowClasses,
  popupPlacementClasses,
  useSmartPopupPlacement,
} from "@/hooks/use-smart-popup-placement";
import type { GraphNodeType } from "@/types/graph";
import { cn } from "@/lib/utils";

const nodeStyles: Record<
  GraphNodeType,
  { icon: typeof FolderGit2; border: string; bg: string; text: string; hover: string }
> = {
  repository: {
    icon: FolderGit2,
    border: "border-violet-300",
    bg: "bg-gradient-to-br from-violet-500 to-indigo-600",
    text: "text-white",
    hover: "hover:shadow-violet-300/50",
  },
  file: {
    icon: FileCode2,
    border: "border-sky-300",
    bg: "bg-white",
    text: "text-sky-900",
    hover: "hover:shadow-sky-200/80",
  },
  class: {
    icon: Box,
    border: "border-indigo-300",
    bg: "bg-indigo-50",
    text: "text-indigo-900",
    hover: "hover:shadow-indigo-200/80",
  },
  method: {
    icon: FunctionSquare,
    border: "border-violet-200",
    bg: "bg-violet-50",
    text: "text-violet-900",
    hover: "hover:shadow-violet-200/80",
  },
};

export type StructureNodeData = {
  label: string;
  nodeType: GraphNodeType;
  metadata: Record<string, string | number | null | undefined>;
  branch?: string | null;
};

function StructureNode({ data }: NodeProps) {
  const nodeData = data as StructureNodeData;
  const style = nodeStyles[nodeData.nodeType];
  const Icon = style.icon;
  const [hovered, setHovered] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const placement = useSmartPopupPlacement(anchorRef, popupRef, hovered);

  const arrowFirst = placement === "bottom" || placement === "right";

  return (
    <div
      className="relative overflow-visible"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {hovered && (
        <div
          ref={popupRef}
          className={cn(
            "pointer-events-none absolute z-[2000] flex animate-in fade-in zoom-in-95 duration-150",
            placement === "left" || placement === "right" ? "flex-row items-center" : "flex-col",
            popupPlacementClasses[placement],
          )}
        >
          {arrowFirst && (
            <div
              className={cn(
                "relative z-[2000] size-2.5 border-white/80 bg-white shadow-sm",
                popupArrowClasses[placement],
              )}
            />
          )}
          <GraphNodeHoverCard
            label={nodeData.label}
            nodeType={nodeData.nodeType}
            metadata={nodeData.metadata}
            branch={nodeData.branch}
          />
          {!arrowFirst && (
            <div
              className={cn(
                "relative z-[2000] size-2.5 border-white/80 bg-white shadow-sm",
                popupArrowClasses[placement],
              )}
            />
          )}
        </div>
      )}

      <div
        ref={anchorRef}
        className={cn(
          "relative z-[1] min-w-[160px] rounded-xl border-2 px-4 py-3 shadow-md transition-all duration-200",
          style.border,
          style.bg,
          style.text,
          style.hover,
          hovered && "scale-105 shadow-lg ring-2 ring-violet-300/60 ring-offset-2",
        )}
      >
        <Handle
          type="target"
          position={Position.Top}
          className="!size-2 !border-2 !border-violet-400 !bg-white !opacity-0"
        />
        <div className="flex items-center gap-2">
          <Icon className="size-4 shrink-0 opacity-80" />
          <span className="truncate text-sm font-medium">{nodeData.label}</span>
        </div>
        <Handle
          type="source"
          position={Position.Bottom}
          className="!size-2 !border-2 !border-violet-400 !bg-white !opacity-0"
        />
      </div>
    </div>
  );
}

export const structureNodeTypes = {
  structureNode: StructureNode,
};
