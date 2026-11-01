import { describe, expect, it } from "vitest";
import type { RunState } from "./contracts";
import { inputError, rewritePollDecision, runErrorTitle } from "./ui";

const state = (overrides: Partial<RunState> = {}): RunState => ({
  run_id: "run-1",
  mode: "check",
  status: "completed",
  stage: "done",
  input_text: "draft",
  demo_fail: false,
  task_run_id: null,
  variants: [],
  finalist_ids: ["draft"],
  comments: [],
  persona_total: 50,
  scores: [],
  ranking: [],
  reality: null,
  rewrite: null,
  rewrite_error: null,
  retries_seen: 0,
  error: null,
  started_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  last_seq: 0,
  ...overrides,
});

describe("demo UI helpers", () => {
  it("maps empty and overlong input to helpful messages", () => {
    expect(inputError("  ", 10)).toContain("Add a draft");
    expect(inputError("12345678901", 10)).toContain("10");
    expect(inputError("short", 10)).toBeNull();
  });

  it("maps API errors to clear headings", () => {
    expect(runErrorTitle("busy")).toBe("The demo is busy");
    expect(runErrorTitle("backend_down")).toContain("unavailable");
    expect(runErrorTitle("timeout")).toContain("too long");
  });

  it("stops rewrite polling on success, failure, or deadline", () => {
    expect(rewritePollDecision(state({ rewrite: { post_id: "draft", text: "x", cringe_before: 70, cringe_after: 10 } }), 1, 2)).toBe("ready");
    expect(rewritePollDecision(state({ rewrite_error: "failed" }), 1, 2)).toBe("failed");
    expect(rewritePollDecision(state(), 2, 2)).toBe("timeout");
    expect(rewritePollDecision(state(), 1, 2)).toBe("pending");
  });
});
