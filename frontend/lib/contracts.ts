// Shared contract between the API, the workflow tasks and the frontend.
// Mirror every change in backend/app/models.py and data/samples/*.json in the same PR
// (architecture.md section 3). Both people must agree on changes.
import { z } from "zod";

export const GENERATE_MAX_CHARS = 280;
export const CHECK_MAX_CHARS = 3000;

export const RunMode = z.enum(["generate", "check"]);
export const RunStatus = z.enum(["queued", "running", "completed", "failed"]);
export const Stage = z.enum([
  "queued",
  "variants",
  "filtering",
  "commenting",
  "ranking",
  "reality",
  "done",
]);
export const Action = z.enum(["like", "comment", "ignore", "report"]);
export const ErrorCode = z.enum(["busy", "invalid_input", "render_unavailable", "not_found", "internal"]);

export const RunRequest = z
  .object({
    mode: RunMode,
    text: z.string().trim().min(1),
    demo_fail: z.boolean().default(false),
  })
  .refine((r) => r.text.length <= (r.mode === "generate" ? GENERATE_MAX_CHARS : CHECK_MAX_CHARS), {
    message: "text is too long for this mode",
    path: ["text"],
  });

export const Variant = z.object({
  post_id: z.string(),
  voice_id: z.string(),
  voice_label: z.string(),
  text: z.string(),
});

export const CommentResult = z.object({
  event_id: z.string(),
  post_id: z.string(),
  persona_id: z.string(),
  persona_name: z.string(),
  persona_label: z.string(),
  archetype: z.string(),
  action: Action,
  comment: z.string().nullable(),
  appeal: z.number().int().min(1).max(5),
  cringe_flag: z.boolean(),
});

export const CringeFeature = z.object({
  id: z.string(),
  label: z.string(),
  count: z.number().int(),
  points: z.number(),
});

export const CringeResult = z.object({
  post_id: z.string(),
  rule_score: z.number().min(0).max(100),
  llm_score: z.number().min(0).max(100).nullable(),
  score: z.number().min(0).max(100),
  reasons: z.array(CringeFeature).max(5),
});

export const PostScore = z.object({
  post_id: z.string(),
  engagement_rate: z.number().min(0).max(1),
  appeal_mean: z.number().min(1).max(5),
  cringe: CringeResult,
  base_score: z.number(),
});

export const Reality = z.object({
  post_id: z.string(),
  original: z.string(),
  translation: z.string(),
  inflations: z.array(z.string()).max(3),
});

export const Rewrite = z.object({
  post_id: z.string(),
  text: z.string(),
  cringe_before: z.number(),
  cringe_after: z.number(),
});

export const EventType = z.enum([
  "run_started",
  "stage",
  "variants_ready",
  "finalists_selected",
  "comment",
  "cringe_scored",
  "ranking_ready",
  "reality_ready",
  "rewrite_ready",
  "rewrite_failed",
  "demo_failure_triggered",
  "run_completed",
  "run_failed",
]);

export const RunEvent = z.object({
  event_id: z.string(),
  seq: z.number().int().nullish(),
  type: EventType,
  payload: z.record(z.string(), z.unknown()),
});

export const RunState = z.object({
  run_id: z.string(),
  mode: RunMode,
  status: RunStatus,
  stage: Stage,
  input_text: z.string(),
  demo_fail: z.boolean(),
  task_run_id: z.string().nullable(),
  variants: z.array(Variant),
  finalist_ids: z.array(z.string()),
  comments: z.array(CommentResult),
  persona_total: z.number().int(),
  scores: z.array(PostScore),
  ranking: z.array(z.string()),
  reality: Reality.nullable(),
  rewrite: Rewrite.nullable(),
  rewrite_error: z.string().nullable().default(null),
  retries_seen: z.number().int(),
  error: z.string().nullable(),
  started_at: z.string(),
  updated_at: z.string(),
  last_seq: z.number().int(),
});

export const ApiError = z.object({ error: z.string(), code: ErrorCode });

export type RunMode = z.infer<typeof RunMode>;
export type RunStatus = z.infer<typeof RunStatus>;
export type Stage = z.infer<typeof Stage>;
export type Action = z.infer<typeof Action>;
export type RunRequest = z.infer<typeof RunRequest>;
export type Variant = z.infer<typeof Variant>;
export type CommentResult = z.infer<typeof CommentResult>;
export type CringeFeature = z.infer<typeof CringeFeature>;
export type CringeResult = z.infer<typeof CringeResult>;
export type PostScore = z.infer<typeof PostScore>;
export type Reality = z.infer<typeof Reality>;
export type Rewrite = z.infer<typeof Rewrite>;
export type RunEvent = z.infer<typeof RunEvent>;
export type RunState = z.infer<typeof RunState>;
export type ApiError = z.infer<typeof ApiError>;
