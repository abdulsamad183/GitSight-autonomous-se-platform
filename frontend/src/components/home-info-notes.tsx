import { GitBranch, Globe, UserPlus } from "lucide-react";

const notes = [
  {
    id: "public-repos",
    icon: Globe,
    content: (
      <>
        GitSight currently supports <span className="font-medium text-slate-800">public GitHub repositories</span>{" "}
        only. Private repository support is coming soon via GitHub sign-in or a Personal Access Token
        (PAT).
      </>
    ),
  },
  {
    id: "branch-limit",
    icon: GitBranch,
    content: (
      <>
        Analysis is limited to the <span className="font-medium text-slate-800">default branch only</span>{" "}
        (one branch per repository) to keep indexing fast and reliable on hosted infrastructure.
      </>
    ),
  },
  {
    id: "account",
    icon: UserPlus,
    content: (
      <>
        Create a free account with <span className="font-medium text-slate-800">email and password</span>{" "}
        to analyze your repositories. No OTP or extra verification required.
      </>
    ),
  },
] as const;

export function HomeInfoNotes() {
  return (
    <div className="mt-8 flex w-full max-w-lg flex-col gap-3 text-left">
      {notes.map((note) => {
        const Icon = note.icon;
        return (
          <div
            key={note.id}
            className="flex gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-4 py-3"
          >
            <Icon className="mt-0.5 size-4 shrink-0 text-[#2B59FF]" aria-hidden />
            <p className="text-sm leading-relaxed text-slate-600">{note.content}</p>
          </div>
        );
      })}
    </div>
  );
}
