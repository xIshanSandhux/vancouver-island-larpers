// Client-side mirror of backend/workflows/ranking.py (architecture.md section 8).
//
// The tone slider re-orders finalists in the browser with no network call, so it has to
// agree with the server's own ranking. data/samples/ranking_case.json pins both.
import type { PostScore } from "./contracts";

export const DEFAULT_TONE_WEIGHT = 0.5;

export function finalScore(score: PostScore, toneWeight: number = DEFAULT_TONE_WEIGHT): number {
  return score.base_score - toneWeight * score.cringe.score;
}

/** Post ids, best first. post_id breaks ties so the order never wobbles. */
export function rank(scores: PostScore[], toneWeight: number = DEFAULT_TONE_WEIGHT): string[] {
  return [...scores]
    .sort((a, b) => {
      const diff = finalScore(b, toneWeight) - finalScore(a, toneWeight);
      return diff !== 0 ? diff : a.post_id.localeCompare(b.post_id);
    })
    .map((s) => s.post_id);
}
