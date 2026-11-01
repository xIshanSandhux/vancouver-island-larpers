import type { CommentResult } from "@/lib/contracts";
import { reactionCounts } from "./helpers";

export interface ReactionsBarProps {
  comments: CommentResult[];
  total: number;
}

export function ReactionsBar({ comments, total }: ReactionsBarProps) {
  const counts = reactionCounts(comments);
  return (
    <p className="mt-4 border-t border-zinc-100 pt-3 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
      <span className="tabular-nums">{counts.likes}</span> liked without commenting ·{" "}
      <span className="tabular-nums">{counts.comments}</span> commented ·{" "}
      <span className="tabular-nums">{counts.ignored}</span> scrolled past
      {counts.reports > 0 && <> · {counts.reports} reported</>}
      <span className="ml-2 font-medium text-teal-800 dark:text-teal-300">· simulated audience of {total}</span>
    </p>
  );
}
