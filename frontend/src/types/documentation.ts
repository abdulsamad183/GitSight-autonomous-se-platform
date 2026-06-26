export type DocumentGeneratedBy = "repository" | "ai";

export type DocumentType =
  | "repository_overview"
  | "architecture_overview"
  | "modules"
  | "classes"
  | "functions"
  | "branch_summary";

export interface DocumentationTypeItem {
  document_type: DocumentType;
  title: string;
  available: boolean;
  generated_by: DocumentGeneratedBy | null;
  generated_at: string | null;
  source_path: string | null;
}

export interface DocumentationListResponse {
  types: DocumentationTypeItem[];
}

export interface DocumentationResponse {
  document_type: DocumentType;
  title: string;
  content: string;
  generated_by: DocumentGeneratedBy;
  generated_at: string;
  source_path: string | null;
}

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  repository_overview: "Repository Overview",
  architecture_overview: "Architecture Overview",
  modules: "Modules",
  classes: "Classes",
  functions: "Functions",
  branch_summary: "Branches",
};

export const DOCUMENT_CARD_ORDER: DocumentType[] = [
  "repository_overview",
  "architecture_overview",
  "modules",
  "classes",
  "functions",
  "branch_summary",
];
