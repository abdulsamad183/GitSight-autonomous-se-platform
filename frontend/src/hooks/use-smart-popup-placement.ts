"use client";

import { useLayoutEffect, useState } from "react";
import { useStore } from "@xyflow/react";

export type PopupPlacement = "top" | "bottom" | "left" | "right";

const GAP = 12;
const ESTIMATED_WIDTH = 256;
const ESTIMATED_HEIGHT = 200;

function getPaneBounds(anchor: HTMLElement): DOMRect {
  const pane = anchor.closest(".react-flow");
  if (pane) {
    return pane.getBoundingClientRect();
  }
  return new DOMRect(0, 0, window.innerWidth, window.innerHeight);
}

function fits(
  side: PopupPlacement,
  anchor: DOMRect,
  popup: { width: number; height: number },
  bounds: DOMRect,
): boolean {
  switch (side) {
    case "top":
      return anchor.top - bounds.top - GAP >= popup.height;
    case "bottom":
      return bounds.bottom - anchor.bottom - GAP >= popup.height;
    case "left":
      return anchor.left - bounds.left - GAP >= popup.width;
    case "right":
      return bounds.right - anchor.right - GAP >= popup.width;
  }
}

function availableSpace(
  side: PopupPlacement,
  anchor: DOMRect,
  bounds: DOMRect,
): number {
  switch (side) {
    case "top":
      return anchor.top - bounds.top - GAP;
    case "bottom":
      return bounds.bottom - anchor.bottom - GAP;
    case "left":
      return anchor.left - bounds.left - GAP;
    case "right":
      return bounds.right - anchor.right - GAP;
  }
}

function choosePlacement(
  anchor: DOMRect,
  popup: { width: number; height: number },
  bounds: DOMRect,
): PopupPlacement {
  const sides: PopupPlacement[] = ["top", "bottom", "right", "left"];

  const fitting = sides
    .filter((side) => fits(side, anchor, popup, bounds))
    .sort((a, b) => availableSpace(b, anchor, bounds) - availableSpace(a, anchor, bounds));

  if (fitting.length > 0) {
    return fitting[0];
  }

  return sides.sort(
    (a, b) => availableSpace(b, anchor, bounds) - availableSpace(a, anchor, bounds),
  )[0];
}

export const popupPlacementClasses: Record<PopupPlacement, string> = {
  top: "bottom-full left-1/2 mb-3 -translate-x-1/2",
  bottom: "top-full left-1/2 mt-3 -translate-x-1/2",
  left: "right-full top-1/2 mr-3 -translate-y-1/2",
  right: "left-full top-1/2 ml-3 -translate-y-1/2",
};

export const popupArrowClasses: Record<PopupPlacement, string> = {
  top: "mx-auto mt-1 rotate-45 border-b border-r",
  bottom: "mx-auto -mt-2.5 rotate-[225deg] border-b border-r",
  left: "absolute right-0 top-1/2 translate-x-[calc(50%-2px)] -translate-y-1/2 rotate-[-45deg] border-b border-r",
  right:
    "absolute left-0 top-1/2 -translate-x-[calc(50%-2px)] -translate-y-1/2 rotate-[135deg] border-b border-r",
};

export function useSmartPopupPlacement(
  anchorRef: React.RefObject<HTMLElement | null>,
  popupRef: React.RefObject<HTMLElement | null>,
  enabled: boolean,
): PopupPlacement {
  const transform = useStore((state) => state.transform);
  const [placement, setPlacement] = useState<PopupPlacement>("top");

  useLayoutEffect(() => {
    if (!enabled || !anchorRef.current) return;

    const update = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;

      const anchorRect = anchor.getBoundingClientRect();
      const bounds = getPaneBounds(anchor);
      const popupRect = popupRef.current?.getBoundingClientRect();

      const popupSize = {
        width: popupRect?.width ?? ESTIMATED_WIDTH,
        height: popupRect?.height ?? ESTIMATED_HEIGHT,
      };

      setPlacement(choosePlacement(anchorRect, popupSize, bounds));
    };

    update();

    const pane = anchorRef.current.closest(".react-flow");
    const resizeObserver =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => update())
        : null;

    resizeObserver?.observe(anchorRef.current);
    if (popupRef.current) resizeObserver?.observe(popupRef.current);
    if (pane) resizeObserver?.observe(pane);

    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [enabled, anchorRef, popupRef, transform]);

  return placement;
}
