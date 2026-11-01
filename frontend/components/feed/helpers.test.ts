import { describe, expect, it } from "vitest";
import type { CommentResult } from "../../lib/contracts";
import { dedupeComments, reactionCounts, scoreWidth, visibleComments } from "./helpers";

const comment = (event_id: string, action: CommentResult["action"], text: string | null = null): CommentResult => ({
  event_id,
  post_id: "draft",
  persona_id: event_id,
  persona_name: event_id,
  persona_label: "Fictional audience member",
  archetype: "builder",
  action,
  comment: text,
  appeal: 3,
  cringe_flag: false,
});

describe("feed helpers", () => {
  it("deduplicates by event id while preserving arrival order", () => {
    const comments = [comment("b", "like"), comment("a", "comment", "hello"), comment("b", "ignore")];
    expect(dedupeComments(comments).map((item) => item.event_id)).toEqual(["b", "a"]);
  });

  it("aggregates reactions from unique events", () => {
    expect(reactionCounts([comment("a", "like"), comment("b", "comment", "hi"), comment("a", "like")])).toEqual({
      likes: 1,
      comments: 1,
      ignored: 0,
      reports: 0,
    });
  });

  it("shows only valid comment actions", () => {
    expect(visibleComments([comment("a", "comment", "yes"), comment("b", "comment"), comment("c", "like")])).toHaveLength(1);
  });

  it("clamps the displayed score to the meter range", () => {
    expect(scoreWidth({ post_id: "draft", rule_score: 120, llm_score: null, score: 120, reasons: [] })).toBe(100);
  });
});
