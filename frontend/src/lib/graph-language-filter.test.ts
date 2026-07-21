import { describe, expect, it } from "vitest";

import { filterGraphByLanguage, listGraphLanguages } from "@/lib/graph-language-filter";
import type { RepositoryGraph } from "@/types/graph";

function makeGraph(): RepositoryGraph {
  return {
    graph_type: "structure",
    branch: "main",
    empty_state: null,
    stats: {
      files_count: 2,
      classes_count: 1,
      methods_count: 1,
      functions_count: 0,
    },
    nodes: [
      {
        id: "repo_1",
        type: "repository",
        label: "demo",
        metadata: {},
      },
      {
        id: "file_py",
        type: "file",
        label: "main.py",
        metadata: { language: "python", path: "main.py" },
      },
      {
        id: "file_js",
        type: "file",
        label: "app.js",
        metadata: { language: "javascript", path: "app.js" },
      },
      {
        id: "class_py",
        type: "class",
        label: "Service",
        metadata: { language: "python", file_path: "main.py" },
      },
      {
        id: "method_py",
        type: "method",
        label: "run",
        metadata: { language: "python", file_path: "main.py" },
      },
    ],
    edges: [
      { id: "e1", source: "repo_1", target: "file_py" },
      { id: "e2", source: "repo_1", target: "file_js" },
      { id: "e3", source: "file_py", target: "class_py" },
      { id: "e4", source: "class_py", target: "method_py" },
    ],
  };
}

describe("graph-language-filter", () => {
  it("lists unique languages", () => {
    expect(listGraphLanguages(makeGraph())).toEqual(["javascript", "python"]);
  });

  it("returns original graph when no language selected", () => {
    const graph = makeGraph();
    expect(filterGraphByLanguage(graph, null)).toBe(graph);
  });

  it("keeps matching language nodes and ancestors", () => {
    const filtered = filterGraphByLanguage(makeGraph(), "python");
    const ids = filtered.nodes.map((node) => node.id).sort();
    expect(ids).toEqual(["class_py", "file_py", "method_py", "repo_1"]);
    expect(filtered.edges.map((edge) => edge.id).sort()).toEqual(["e1", "e3", "e4"]);
  });
});
