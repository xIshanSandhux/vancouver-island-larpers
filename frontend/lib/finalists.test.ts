import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { RunState } from "./contracts";
import { finalistOrder } from "./finalists";
import { rank } from "./rank";

const sample = RunState.parse(JSON.parse(readFileSync(join(__dirname, "../../data/samples/run_state.json"), "utf-8")));

describe("finalist ordering", () => {
  it("keeps every finalist visible when only one has been scored", () => {
    const run = { ...sample, status: "running" as const, scores: sample.scores.slice(0, 1) };
    expect(finalistOrder(run, 0.5)).toEqual(sample.finalist_ids);
  });

  it("keeps stable positions until the run is complete, even with all scores", () => {
    expect(finalistOrder({ ...sample, status: "running" }, 1)).toEqual(sample.finalist_ids);
  });

  it("uses the tone slider ranking once all results are complete", () => {
    expect(finalistOrder({ ...sample, status: "completed" }, 1)).toEqual(rank(sample.scores, 1));
  });
});
