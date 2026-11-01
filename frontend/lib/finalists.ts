import type { RunState } from "./contracts";
import { rank } from "./rank";

export function finalistOrder(run: RunState, toneWeight: number): string[] {
  // All finalists stay on screen; incomplete scores must not hide pending posts.
  if (run.status !== "completed" || run.scores.length !== run.finalist_ids.length) {
    return run.finalist_ids;
  }
  return rank(run.scores, toneWeight);
}
