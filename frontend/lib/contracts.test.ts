import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { RunEvent, RunRequest, RunState } from "./contracts";

const samples = join(__dirname, "..", "..", "data", "samples");
const load = (name: string) => JSON.parse(readFileSync(join(samples, name), "utf-8"));

describe("contracts match data/samples", () => {
  it("parses the sample RunState", () => {
    expect(RunState.parse(load("run_state.json")).run_id).toBe("run-sample-0001");
  });

  it("parses every sample event", () => {
    const events = load("events.json") as unknown[];
    expect(events.length).toBeGreaterThan(0);
    for (const e of events) RunEvent.parse(e);
  });

  it("parses the sample request", () => {
    expect(RunRequest.parse(load("run_request.json")).mode).toBe("generate");
  });

  it("rejects over-length generate text and empty text", () => {
    expect(RunRequest.safeParse({ mode: "generate", text: "x".repeat(281) }).success).toBe(false);
    expect(RunRequest.safeParse({ mode: "check", text: "x".repeat(281) }).success).toBe(true);
    expect(RunRequest.safeParse({ mode: "generate", text: "   " }).success).toBe(false);
  });
});
