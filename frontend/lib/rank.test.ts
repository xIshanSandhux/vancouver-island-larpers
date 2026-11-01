import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { PostScore } from "./contracts";
import { DEFAULT_TONE_WEIGHT, finalScore, rank } from "./rank";

// The same fixture drives backend/tests/test_ranking.py.
const fixture = JSON.parse(
  readFileSync(join(__dirname, "..", "..", "data", "samples", "ranking_case.json"), "utf-8"),
);
const scores = fixture.scores.map((s: unknown) => PostScore.parse(s));

describe("rank", () => {
  it("matches the shared fixture at every tone weight", () => {
    for (const [weight, expected] of Object.entries(fixture.expected)) {
      expect(rank(scores, Number(weight)), `tone weight ${weight}`).toEqual(expected);
    }
  });

  it("changes the order as the slider moves", () => {
    expect(rank(scores, 0)).not.toEqual(rank(scores, 1));
  });

  it("defaults to the same weight the server uses", () => {
    expect(rank(scores)).toEqual(fixture.expected[String(DEFAULT_TONE_WEIGHT)]);
  });

  it("penalises cringe as the weight rises", () => {
    const cringey = scores.find((s: { post_id: string }) => s.post_id === "v01")!;
    expect(finalScore(cringey, 1)).toBeLessThan(finalScore(cringey, 0));
  });
});
