import type { CommentResult, CringeResult } from "../../lib/contracts";

export function dedupeComments(comments: CommentResult[]): CommentResult[] {
  const seen = new Set<string>();
  return comments.filter((comment) => {
    if (seen.has(comment.event_id)) return false;
    seen.add(comment.event_id);
    return true;
  });
}

export function reactionCounts(comments: CommentResult[]) {
  const counts = { likes: 0, comments: 0, ignored: 0, reports: 0 };
  for (const comment of dedupeComments(comments)) {
    if (comment.action === "like") counts.likes += 1;
    else if (comment.action === "comment") counts.comments += 1;
    else if (comment.action === "ignore") counts.ignored += 1;
    else counts.reports += 1;
  }
  return counts;
}

export function visibleComments(comments: CommentResult[]): CommentResult[] {
  return dedupeComments(comments).filter((comment) => comment.action === "comment" && Boolean(comment.comment));
}

export function scoreTone(score: number): string {
  if (score >= 67) return "text-amber-700 dark:text-amber-300";
  if (score >= 34) return "text-amber-600 dark:text-amber-400";
  return "text-emerald-700 dark:text-emerald-300";
}

export function scoreWidth(cringe: CringeResult): number {
  return Math.max(0, Math.min(100, Math.round(cringe.score)));
}
