# Thought Leadr: architecture

Read `requirements.md` first for what the product does and why. This file says how it is built. `agents.md` says who builds which part.

Items marked **VERIFY** are things I could only confirm from secondary documentation. Check them against the current Render docs (https://render.com/docs/workflows) before relying on them.

## 1. System overview

Three deployables, two folders of code, one repo:

| Deployable | Folder | Render type | Start command |
|---|---|---|---|
| Frontend (Next.js UI) | `frontend/` | web service | `npm run start` |
| API (FastAPI) | `backend/` (`backend/app/`) | web service | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Workflow tasks (Python) | `backend/` (`backend/workflows/`) | **Workflow service** | `render-workflows workflows.main:app` (confirmed from the SDK's CLI) |

The API and the workflow service use the **same root directory** (`backend/`), so they share one Python codebase, one `requirements.txt`, the same Pydantic models and the same `cringe/` module.

```
                       Browser
                         |  GET /  (static UI)               ^ GET /api/runs/:id  (poll ~1s)
                         v                                   |
              +-----------------------+   fetch (CORS)  +--------------------------------------+
              | Render WEB: frontend/ |---------------->| Render WEB: backend/app  (FastAPI)   |
              | Next.js, TypeScript   |                 |  - in-memory RunStore                |
              +-----------------------+                 |  - POST /api/runs -> start_task()    |
                                                        |  - POST /internal/runs/:id/events    |
                                                        |  - POST /internal/runs/:id/demo-fail |
                                                        |  - abuse guard (limits, busy 429)    |
                                                        +--------------------------------------+
                                                           | start_task (Render Python SDK)   ^ events
                                                           v                                  | (HTTPS POST, Bearer)
                                                        +--------------------------------------+
                                                        | Render WORKFLOW: backend/workflows   |
                                                        |  run_pipeline (root)                 |
                                                        |   +-- write_variant_batch  x N (Claude)
                                                        |   +-- run_commenter_batch  x M (Featherless)
                                                        |   +-- translate_reality        (Claude)
                                                        |  run_tone_down (root)        (Claude)|
                                                        +--------------------------------------+
                                                                |                  |
                                                                v                  v
                                                          Anthropic API     Featherless AI API
```

### Why events are pushed to the API

- A workflow task run only returns its result **when it finishes**. A user watching a comment section needs results as they happen.
- Task runs **cannot receive incoming connections**, but they can make outgoing ones. So tasks POST progress events to the API, and the browser polls the API.
- This also avoids polling the Render API every second. Root-level Render API calls are rate limited (50 per minute on Hobby, **VERIFY**).
- The API holds run state in memory. There is no database. That is deliberate for a 7-hour build.
- Event delivery is idempotent. Every event has an `event_id`, and the store ignores a repeat. Render retries failed tasks, and a retried task re-sends events.
- The API also watches the started task run (`await` on the SDK's awaitable run). If the root run fails or is cancelled without posting `run_failed`, the API marks the run failed so the UI never hangs.

## 2. Repository layout and ownership

The template for both apps already exists on `main`. Files marked *(template)* exist today.

```
/
  README.md  agents.md  CLAUDE.md  requirements.md  architecture.md  ideas.md   (.gitignore)
  data/                       # read by the backend
    personas.json             # Ishan  (I1)  50 personas, 10 archetypes x 5
    voices.json               # Mahir  (M2)  20 post voices + prompt templates
    cringe_lexicon.json       # Ishan  (I3)  phrase lists used by rule features
    samples/                  # shared  example RunState / event JSON, ranking_case.json
  backend/                    # Python 3.11+  (venv in backend/.venv, git-ignored)
    requirements.txt  pytest.ini  .env.example                              (template)
    app/                      # FastAPI service
      main.py  config.py                                                    (template)
      models.py               # shared contract (Pydantic). Changes need both people.  (M1)
      store.py                # Mahir (M5)  RunStore, event application, dedupe, TTL
      render_client.py        # Mahir (M5)  start_task + watcher around the Render Python SDK
      guard.py                # Mahir (M9)  rate/concurrency limits, input checks, busy 429
      routes/runs.py          # Mahir (M5)  POST /api/runs, GET /api/runs/{id}
      routes/internal.py      # Mahir (M5/M7)  events + demo-fail-claim (secret protected)
      routes/tone_down.py     # Ishan (I4)  POST /api/runs/{id}/tone-down
    workflows/                # Render Workflow service (same root dir as the API)
      main.py                 # Mahir (M1)  app = Workflows(...); registers tasks; app.start()
      events.py               # Mahir (M1)  post_event(), claim_demo_fail()
      llm/anthropic_client.py # Mahir (M2)
      llm/featherless_client.py # Ishan (I2)
      tasks/pipeline.py       # Mahir (M2, M3)  run_pipeline, write_variant_batch, filter_top3
      tasks/reality.py        # Mahir (M4)
      tasks/commenters.py     # Ishan (I2)  run_commenter_batch
      tasks/tone_down.py      # Ishan (I4)  run_tone_down
    cringe/                   # Ishan (I3)  features(), score()  (stub created by M1)
    scripts/consistency.py    # Ishan (I7)
    tests/
  frontend/                   # Next.js App Router, TypeScript, Tailwind  (template)
    app/layout.tsx  app/page.tsx  lib/api.ts                                (template)
    app/page.tsx              # Mahir (M6)  Generate page (replaces the template page)
    app/check/page.tsx        # Ishan (I6)  Check page
    components/feed/          # Ishan (I5)  PostCard, ReactionsBar, CommentThread, CringeMeter
    components/generate/      # Mahir (M6)  InputBox, RankedList, RealityToggle, ToneSlider
    lib/contracts.ts          # shared contract (zod + TS types). Changes need both people. (M1)
    lib/useRun.ts             # Mahir (M5)  polling hook
    lib/rank.ts               # Mahir (M3)  client-side re-rank used by ToneSlider
    AGENTS.md                 # generated by create-next-app: points at the bundled Next.js docs. Keep it.
```

Rule: **only edit files in your own column.** If you need a change in someone else's file or in a shared contract, tell the other person and agree before editing.

## 3. Contracts

`backend/app/models.py` (Pydantic) and `frontend/lib/contracts.ts` (zod) describe the same shapes. There is no code generation. The first PR that touches contracts (M1) writes both and commits example JSON in `data/samples/` that validates against both. After that, any change updates both files and the samples in the same PR.

### 3.1 Enums

```
RunMode      = "generate" | "check"
RunStatus    = "queued" | "running" | "completed" | "failed"
Stage        = "queued" | "variants" | "filtering" | "commenting" | "ranking" | "reality" | "done"
Action       = "like" | "comment" | "ignore" | "report"
```

### 3.2 Types (shown as TypeScript; mirror in Pydantic)

```ts
type RunRequest = {
  mode: RunMode;
  text: string;            // generate: the boring sentence (<= 280 chars). check: the draft post (<= 3000 chars)
  demo_fail?: boolean;     // true => one commenter batch fails once and is retried
};

type Variant = {
  post_id: string;         // "v01".."v20"; in check mode a single post "draft"
  voice_id: string;        // from voices.json ("user" for the draft)
  voice_label: string;     // e.g. "Humblebrag"
  text: string;
};

type CommentResult = {
  event_id: string;        // idempotency key: `${run_id}:${post_id}:${persona_id}`
  post_id: string;
  persona_id: string;      // from personas.json
  persona_name: string;    // fictional display name
  persona_label: string;   // e.g. "Talent Acquisition Partner"
  archetype: string;
  action: Action;
  comment: string | null;  // present when action === "comment"
  appeal: 1 | 2 | 3 | 4 | 5;
  cringe_flag: boolean;
};

type CringeFeature = { id: string; label: string; count: number; points: number };
type CringeResult = {
  post_id: string;
  rule_score: number;      // 0..100
  llm_score: number | null;// 0..100, share of commenters with cringe_flag; null until comments exist
  score: number;           // 0..100 blended (see section 7)
  reasons: CringeFeature[];// triggered features, highest points first, max 5
};

type PostScore = {
  post_id: string;
  engagement_rate: number; // (likes + comments) / persona_count, 0..1
  appeal_mean: number;     // 1..5
  cringe: CringeResult;
  base_score: number;      // see section 8, computed from engagement and appeal only
};

type Reality = {
  post_id: string;
  original: string;        // the user's sentence, verbatim
  translation: string;     // one line: what got inflated
  inflations: string[];    // up to 3 short phrases
};

type Rewrite = { post_id: string; text: string; cringe_before: number; cringe_after: number };

type RunEvent = {
  event_id: string;
  seq: number;             // assigned by the API, increasing
  type:
    | "run_started" | "stage" | "variants_ready" | "finalists_selected"
    | "comment" | "cringe_scored" | "ranking_ready" | "reality_ready"
    | "rewrite_ready" | "demo_failure_triggered" | "run_completed" | "run_failed";
  payload: unknown;        // shape depends on type, see 3.3
};

type RunState = {
  run_id: string;
  mode: RunMode;
  status: RunStatus;
  stage: Stage;
  input_text: string;
  demo_fail: boolean;
  task_run_id: string | null;      // Render task run id, for the dashboard
  variants: Variant[];             // all 20 (generate) or the draft (check)
  finalist_ids: string[];          // 3 post_ids (generate) or ["draft"] (check)
  comments: CommentResult[];       // arrive over time
  persona_total: number;           // 50
  scores: PostScore[];             // arrive as finalists finish
  ranking: string[];               // post_ids, best first (server default tone weight)
  reality: Reality | null;
  rewrite: Rewrite | null;
  retries_seen: number;            // count of demo_failure_triggered events
  error: string | null;
  started_at: string;              // ISO
  updated_at: string;
  last_seq: number;
};

type ApiError = { error: string; code: "busy" | "invalid_input" | "render_unavailable" | "not_found" | "internal" };
```

### 3.3 Event payloads

| type | payload |
|---|---|
| run_started | `{ mode, input_text }` |
| stage | `{ stage }` |
| variants_ready | `{ variants: Variant[] }` (all 20) |
| finalists_selected | `{ finalist_ids: string[] }` |
| comment | `CommentResult` (one persona on one post) |
| cringe_scored | `PostScore` (sent once a finalist has all persona results) |
| ranking_ready | `{ ranking: string[] }` |
| reality_ready | `Reality` |
| rewrite_ready | `Rewrite` |
| demo_failure_triggered | `{ batch_id: string }` |
| run_completed | `{}` |
| run_failed | `{ error: string }` |

## 4. HTTP API (FastAPI, `backend/app/`)

CORS allows only the origins in `CORS_ORIGINS` (the frontend URL). Errors use the `ApiError` shape with a matching HTTP status (400 invalid input, 404 not found, 429 busy, 502 Render unavailable).

| Method and path | Caller | Behaviour |
|---|---|---|
| `GET /health` | anyone | `{"status": "ok"}` (template, already implemented) |
| `POST /api/runs` | browser | Validates `RunRequest` (length limits, section 9). Runs the abuse guard (section 10). Creates `run_id` (uuid4), `RunState` with status `queued`. Calls `RenderAsync().workflows.start_task("<workflow-slug>/run_pipeline", [{run_id, mode, text, demo_fail}])`, stores `task_run_id`, starts the watcher. Returns `{run_id}`. If Render throws, mark the run failed and return 502 `render_unavailable`. |
| `GET /api/runs/{id}` | browser | Returns the full `RunState`. 404 for unknown ids. The browser polls about every 1000 ms until `status` is `completed` or `failed`, with a hard stop at 120 s. |
| `POST /api/runs/{id}/tone-down` | browser | Check mode only. Starts `run_tone_down` for the draft. The result arrives as a `rewrite_ready` event. |
| `POST /internal/runs/{id}/events` | workflow tasks only | Requires `Authorization: Bearer ${WORKFLOW_EVENT_SECRET}` (constant-time compare). Body is one `RunEvent` without `seq`. Applies it to the run if the `event_id` has not been seen. Returns `{ok: true, duplicate: bool}`. |
| `POST /internal/runs/{id}/demo-fail-claim` | workflow tasks only | Same auth. Atomically returns `{fail: true}` the **first** time it is called for a run with `demo_fail` set, otherwise `{fail: false}`. Used by the failure switch (section 6). |

`RunStore` is a dict guarded by an `asyncio.Lock`. Runs expire after 1 hour. The API **must run as one instance with one worker** (`--workers 1`, one Render instance) because state is in memory.

Render SDK usage (Python, confirmed in the SDK source): `from render import RenderAsync`; `await RenderAsync().workflows.start_task(task_slug, input_data)` returns an awaitable run, and awaiting it raises on failure. `task_slug` is `{workflow-slug}/{task-name}`; `input_data` is a list of positional arguments. `RENDER_API_KEY` is read from the environment. The SDK is already in `requirements.txt`.

## 5. Workflow tasks (Python, `backend/workflows/`)

All tasks use the Render Python SDK (PyPI package `render`, v1.6, confirmed; `render_sdk` is only a deprecated shim). Verified against the installed SDK source:

- Create the app with `Workflows(default_retry=..., default_timeout=..., default_plan=...)`. Register tasks with `@app.task`. Call `app.start()` in the entry point.
- Every task function takes a `TaskContext` as its first argument. Chain a task with `await ctx.run(other_task, args...)`. Run children in parallel with `asyncio.gather` or `asyncio.TaskGroup` (otherwise they run one after another).
- Retry settings are `Retry(max_retries, wait_duration_ms, backoff_scaling=1.5)` (confirmed). `TaskContext` exposes run ids, not the attempt number, which is why the failure switch asks the API (section 6).
- Tasks take JSON-serialisable arguments, so tasks receive plain dicts. In tests call the task body directly with `task_definition.func(ctx, ...)`.
- A task slug has the form `{workflow-slug}/{task-name}`.
- Limits: a Hobby workspace can start new compute at about 16 CPU per minute (more on Pro). Chained runs over the limit **fail at `ctx.run()`**. Total arguments per run are capped at 4 MB. Up to 1,000 chained runs per minute. **VERIFY** against https://render.com/docs/workflows-limits.

### 5.1 Granularity (the main performance decision)

Every task run is its own instance with its own startup time. So 150 persona calls must **not** be 150 task runs. Group calls inside a task and use `asyncio.gather` within it.

Defaults in `backend/app/config.py` (adjustable by env var):

| Constant | Default | Meaning |
|---|---|---|
| `VARIANT_BATCHES` | 4 | `write_variant_batch` runs; each writes 5 voices concurrently |
| `COMMENTER_BATCHES_PER_POST` | 2 | `run_commenter_batch` runs per finalist; each handles 25 personas concurrently |
| `LLM_CONCURRENCY` | 12 | semaphore inside a task for outgoing model calls |
| `MAX_ACTIVE_RUNS` | 2 | API-side cap on simultaneous runs (section 10) |

Run count for one generate run: 1 root + 4 variant batches + 6 commenter batches (3 finalists x 2) + 1 reality = **12**. A check run: 1 root + 2 commenter batches (+ 1 rewrite on demand) = **3 to 4**.

Do this first (M1, then M8): time one trivial chained run to measure startup latency, and confirm the workspace plan. If 12 runs per click is too slow or hits the per-minute compute cap, lower the batch counts. Rehearsals and **judges trying the app during judging** use the same budget as the real demo.

### 5.2 Tasks

**`run_pipeline(ctx, req)`** (root; Mahir M2/M3)
1. `post_event(stage: variants)`.
2. generate mode: `asyncio.gather` over `VARIANT_BATCHES` calls to `ctx.run(write_variant_batch, ...)`. Merge into 20 `Variant`s. Post `variants_ready`.
   check mode: build the single `Variant(post_id="draft", voice_id="user", text=req.text)`.
3. generate mode: `filter_top3(variants)` (a plain function, not a task). Post `finalists_selected`.
4. `post_event(stage: commenting)`. For each finalist, `asyncio.gather` over `COMMENTER_BATCHES_PER_POST` calls to `ctx.run(run_commenter_batch, ...)`. Each batch posts one `comment` event per persona as it completes.
5. When all batches for a finalist return: compute `cringe.score(...)` and the `PostScore`, post `cringe_scored`.
6. `post_event(stage: ranking)`. Compute ranking, post `ranking_ready`.
7. generate mode: `ctx.run(translate_reality, ...)` for the top-ranked post, post `reality_ready`.
8. Post `run_completed`. On any unrecovered exception post `run_failed` and re-raise.

**`write_variant_batch(ctx, run_id, input_text, voice_ids)`** (Mahir M2)
Calls Claude once per voice (concurrently, bounded by `LLM_CONCURRENCY`), using the template in `voices.json`. Validates the guardrails in section 9. Returns `list[Variant]`. Retries a voice once on a guardrail failure with a stricter instruction before dropping that voice.

**`run_commenter_batch(ctx, run_id, post, persona_ids, batch_id)`** (Ishan I2)
1. If this run has the demo switch on and this is the designated batch (section 6), claim the failure and raise.
2. For each persona, concurrently, call the commenter provider. Validate the strict JSON schema in section 11. On invalid JSON retry once with a "return only JSON" reminder; on a second failure record `action: "ignore"`, `appeal: 3`, `cringe_flag: false` and log a warning.
3. Post a `comment` event per persona as soon as it is done.
4. Return `list[CommentResult]`.

**`translate_reality(ctx, run_id, original, post)`** (Mahir M4)
One Claude call returning `{translation, inflations}` JSON. Returns `Reality`.

**`run_tone_down(ctx, run_id, draft, cringe_result)`** (Ishan I4)
Root task for check mode. One Claude call that rewrites the draft to remove the triggered features while keeping the facts. Re-score the rewrite with the rule part only (fast, repeatable). Post `rewrite_ready`.

## 6. Retry and the demo failure switch

Durability story for the Render judges:

- Every task has `Retry(max_retries=2, wait_duration_ms=1000, backoff_scaling=1.5)` (**VERIFY** parameter names).
- A task run is retried on an exception, a timeout, or an instance error.
- Event posting is idempotent (`event_id`), so a retried batch can safely re-send.
- Side effects live in child tasks and are keyed (the `event_id`).

**Failure switch.** When `RunRequest.demo_fail` is true:

1. The UI shows a "Demo mode: simulated failure" badge. It is labelled honestly; do not hide it.
2. `run_pipeline` designates the **first** commenter batch of the **first** finalist as the failing batch (`batch_id` like `v07-b1`).
3. At the start of that batch, the task calls `POST /internal/runs/{id}/demo-fail-claim`. The API answers `{fail: true}` exactly once per run. If true, the task posts `demo_failure_triggered`, then raises `RuntimeError("simulated failure (demo mode)")`.
4. Render retries the batch. The second attempt claims again, gets `{fail: false}`, and runs normally.
5. The UI shows "Retried 1 task automatically" using `retries_seen`, and the Render dashboard shows the failed attempt followed by a successful one.

This does not rely on knowing the attempt number inside the SDK. The API is the single source of truth for "have we failed yet".

## 7. Cringe score (Ishan I3, `backend/cringe/`)

Public interface (M1 creates a stub with these signatures so imports work from day one):

```python
def features(text: str) -> list[CringeFeature]          # rule-based, deterministic
def rule_score(feats: list[CringeFeature]) -> float     # 0..100
def score(post_id: str, text: str, comments: list[CommentResult] | None) -> CringeResult
def hype_score(text: str) -> float                      # used by filter_top3 (higher = more thought-leader-like)
```

Rule features (case-insensitive; lexicons in `data/cringe_lexicon.json`). Points are added, then the total is capped at 100.

| id | Detects | Points |
|---|---|---|
| `one_line_paragraphs` | share of lines that are a single short sentence (<= 12 words) separated by blank lines; points = 12 x share | up to 12 |
| `hook_phrase` | "unpopular opinion", "nobody talks about", "here's the truth", "I was fired", "stop doing", "harsh truth" | 10 |
| `engagement_bait` | ending with "Agree?", "Thoughts?", "Repost if", "Follow for more" | 10 |
| `humblebrag` | "humbled", "honored", "thrilled to announce", "grateful", "blessed" (2 pts each, cap 12) | up to 12 |
| `hashtags` | more than 3 hashtags (1 pt each beyond 3, cap 8) | up to 8 |
| `emoji_overload` | more than 3 emoji (1 pt each beyond 3, cap 8) | up to 8 |
| `buzzwords` | "synergy", "leverage", "ecosystem", "disrupt", "growth mindset", "thought leader", "journey", "unlock" (2 pts each, cap 10) | up to 10 |
| `listicle` | "3 lessons", "5 things", numbered lines | 6 |
| `fake_vulnerability` | "I cried", "broke down", "at 3am", "nobody believed" | 8 |
| `over_length` | more than 1300 characters | 6 |

Blend: if there are no comments yet, `score = rule_score`. Otherwise `llm_score = 100 x (share of commenters with cringe_flag)` and `score = 0.6 x rule_score + 0.4 x llm_score`. `reasons` is the triggered features sorted by points, max 5. Unit tests cover each feature and the blend, and a set of 10 known-cringe vs 10 plain posts must separate (I7).

## 8. Ranking (Mahir M3; Python in `backend/workflows/tasks/pipeline.py`, client copy in `frontend/lib/rank.ts`)

```
engagement_rate = (likes + comments) / persona_count          # 0..1
appeal_norm     = (appeal_mean - 1) / 4                       # 0..1
base_score      = 100 x (0.5 x engagement_rate + 0.5 x appeal_norm)

final_score(w)  = base_score - w x cringe.score               # w = tone weight, default 0.5
```

- The server computes `ranking` with `w = 0.5`.
- The tone slider (0 to 1) re-ranks **in the browser only** using `rank.ts` over the same numbers, so it needs no model call and behaves identically every time. The Python and TypeScript implementations must agree; one test in each language reads the shared `data/samples/ranking_case.json`.
- `filter_top3`: sort the 20 variants by `hype_score` descending and take the top 3 with **distinct** `voice_id`s.

## 9. Content and input guardrails in code

- **Input limits:** generate text 1 to 280 characters, check text 1 to 3000. Reject empty, whitespace-only and control characters. Strip and normalise whitespace.
- **User text is data, not instructions.** Wrap it in delimiters in every prompt (for example `<user_text>...</user_text>`), tell the model to treat it as content to rewrite and never as instructions, and never place it in a system prompt. A persona or variant answer that echoes system-prompt text is treated as invalid.
- **Offensive input.** Prompts instruct the model to decline hateful, harassing or sexual content by returning a short neutral post about "a quiet day at work". A small blocklist in `guard.py` rejects obviously abusive input with `invalid_input` before any model call. This runs on a public demo URL, so assume someone will try.
- **Tone, not facts.** Variant prompts say: use only facts from the input; exaggerate tone and framing, never facts; do not add employers, job titles, schools, numbers, names of people, or companies.
- **Post-validation.** Any digit sequence in the output that is not in the input (other than list markers 1 to 5) fails the variant. Capitalised multi-word names that are not in the input also fail. A failed variant is retried once with a stricter prompt.
- **Fictional audience.** Persona names are fictional and generic. No real public figures anywhere in prompts, data or UI.
- **Own branding.** The UI uses its own name ("Thought Leadr"), colours and icons. Never use LinkedIn's logo, name, or exact colours.
- **No forecasts.** The UI never shows a number as a forecast of real engagement. Counts are labelled "simulated audience".
- **Plain text only** in the UI; never `dangerouslySetInnerHTML`.

## 10. Abuse and load protection (Mahir M9, `backend/app/guard.py`)

The deployed API will be public and judges may try it during judging, while real model and Render budget is limited.

- `MAX_ACTIVE_RUNS` (default 2): if exceeded, `POST /api/runs` returns 429 `busy` with the message "Both demo slots are busy, try again in a few seconds", and the UI shows it nicely.
- Per-IP limit: at most 1 new run per 10 seconds and 20 per hour. (Behind Render's proxy, read the client IP from `X-Forwarded-For`.)
- A global cap `MAX_RUNS_PER_HOUR` (default 60) protects model credits.
- Input limits and blocklist from section 9.
- Demo mode (`demo_fail`) is allowed from any client; it only affects the caller's own run.

## 11. Personas and commenter contract (Ishan I1/I2)

`data/personas.json` is an array of 50 objects:

```json
{
  "id": "p01",
  "archetype": "recruiter",
  "name": "Dana",
  "label": "Talent Acquisition Partner",
  "industry": "Tech",
  "bio": "Scrolls 200 profiles a day, comments on anything with 'open to work' energy.",
  "hype_tolerance": 4,
  "cynicism": 2,
  "like_bias": 0.8,
  "comment_style": "short, upbeat, ends with a handshake emoji"
}
```

10 archetypes, 5 variations each: `recruiter`, `agree_guy` (engagement farmer), `ai_pivot_bro` (was crypto, now AI), `great_post_bot`, `skeptical_senior_eng`, `laid_off_job_seeker`, `hustle_founder`, `hr_people_ops`, `quiet_lurker`, `corporate_comms_exec`. Variations differ in industry, seniority, mood and tolerance for hype.

Commenter prompt: the system message sets the persona and says "react as this person would scrolling their feed; be brief; no real people". The user message has the post inside delimiters. The model must return **only** this JSON:

```json
{ "action": "like|comment|ignore|report", "comment": "string or null", "appeal": 1, "cringe_flag": false }
```

Rules: `comment` is non-null only when `action` is `comment` (max 140 chars). `appeal` is an integer 1 to 5. `cringe_flag` is true if the persona would roll their eyes. Validate with Pydantic. Use `temperature` around 0.8 so personas vary.

## 12. Models and providers

| Use | Provider | Env var for model | Notes |
|---|---|---|---|
| Post variants, reality translation, tone-down rewrite | Anthropic | `CLAUDE_MODEL` (default `claude-haiku-5-5`) | Fast, structured. Raise to `claude-sonnet-5-5` if variant quality is poor and latency allows. |
| Commenter personas | Featherless AI (OpenAI-compatible) | `FEATHERLESS_MODEL` | Pick a small instruct model. **VERIFY** the base URL (`FEATHERLESS_BASE_URL`, expected `https://api.featherless.ai/v1`) and model id in the Featherless dashboard. Participants get a free month through the event's participant setup guide / promo code. |

**Risk: Featherless concurrency.** Featherless limits concurrent requests by plan. 50+ calls in parallel may queue or fail. Mitigations: the `LLM_CONCURRENCY` semaphore, backoff on 429, and a switch `COMMENTER_PROVIDER=featherless|anthropic` that sends the same commenter prompts to Claude instead. Test Featherless concurrency in the first hour (I2) and switch if it is too slow. The demo does not depend on which provider answers.

Call budget per generate run: 20 variants + 150 commenters + 1 reality = about 171 model calls. Per check run: 50 commenters + optional 1 rewrite.

## 13. Environment variables

`frontend/` (Render web service; build-time, `NEXT_PUBLIC_*` are public):

| Var | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | public URL of the FastAPI service (local: `http://localhost:8000`) |
| `NEXT_PUBLIC_USE_SAMPLES` | `true` renders from `data/samples` copies without a backend (UI development) |
| `NEXT_PUBLIC_RENDER_DASHBOARD_URL` | link shown in the UI for the demo |
| `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | stretch (I9) |

`backend/` API service and workflow service (both read `backend/app/config.py`):

| Var | Used by | Purpose |
|---|---|---|
| `RENDER_API_KEY` | API | lets the Render SDK start task runs (**VERIFY** where to create it) |
| `RENDER_WORKFLOW_SLUG` | API | the workflow service slug, used to build `{slug}/run_pipeline` |
| `WORKFLOW_EVENT_SECRET` | both | shared secret for the internal endpoints |
| `CORS_ORIGINS` | API | comma-separated allowed origins (the frontend URL) |
| `WEB_BASE_URL` | workflow | public URL of the API, e.g. `https://thought-leadr-api.onrender.com` |
| `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | workflow | Claude |
| `FEATHERLESS_API_KEY`, `FEATHERLESS_BASE_URL`, `FEATHERLESS_MODEL` | workflow | Featherless |
| `COMMENTER_PROVIDER` | workflow | `featherless` (default) or `anthropic` |
| `VARIANT_BATCHES`, `COMMENTER_BATCHES_PER_POST`, `LLM_CONCURRENCY` | workflow | optional overrides for section 5.1 |
| `MAX_ACTIVE_RUNS`, `MAX_RUNS_PER_HOUR` | API | abuse guard (section 10) |
| `SENTRY_DSN` | both | stretch (I9) |

Rules: secrets live only in Render environment settings and local `.env` files. `.env*` is git-ignored except `.env.example`.

## 14. Deployment on Render (Mahir M1)

1. **Frontend web service.** Root directory `frontend`, build `npm install && npm run build`, start `npm run start`. Set `NEXT_PUBLIC_API_URL` to the API's URL **before** building (it is baked in at build time).
2. **API web service.** Root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`. Set the Python version to 3.11 (an env var or a `.python-version` file; **VERIFY**, the SDK needs a recent Python). Health check path `/health`.
3. **Workflow service.** Create it in the dashboard (Workflows are not replicated by Blueprints, per the docs, so do not rely on `render.yaml` for this). Root directory `backend`, build `pip install -r requirements.txt`, start command `render-workflows workflows.main:app`. Set env vars (section 13). Still **VERIFY** in the dashboard: that the root directory setting works as expected for "My own workflow".
4. Use always-on instances for the API and frontend (or ping them before the demo), so there is no cold start while presenting.
5. Deploy the minimal round trip first: `POST /api/runs` starts `run_pipeline`, which posts `run_started` and `run_completed`; the browser sees the run complete. Confirm this before building anything else.
6. Auto-deploy from `main`. Because of this, **never push a broken `main`** (see `agents.md`).
7. Record the three service URLs and the dashboard link in the README before the demo.

## 15. Errors, logging, observability

- Python: `logging` at INFO with `run_id` in every line. Never log full model outputs or post text at INFO, only counts and ids.
- API: log each internal endpoint call with `run_id` and event `type`.
- Every model call has a timeout (20 s) and one retry for transient errors.
- UI states for: queued, running (with a stage label), failed (message and a "Try again" button), busy (429 message), and a 120 s overall timeout.
- Stretch (I9): PostHog events `run_started`, `run_completed`, `reality_toggled`, `tone_changed`, `draft_checked`. Sentry in both services. Scrub post text from Sentry payloads.

## 16. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Task startup latency or per-minute compute cap on Hobby | Run takes too long, chained runs fail | Measure in the first hour. Reduce `*_BATCHES`. Ask Render staff about credits or a higher plan at the event. |
| Judges or attendees spam the public app during judging | Budget and Render limits exhausted before your slot | Abuse guard (section 10), busy message, keep the URL out of public channels until your slot |
| Featherless concurrency limits | Commenters slow or 429 | Semaphore plus `COMMENTER_PROVIDER=anthropic` fallback |
| Model returns invalid JSON | Missing comments | Pydantic validation, one reminder retry, then default result |
| Prompt injection or offensive input on a public demo | Embarrassing output on stage | Delimited user text, blocklist, invalid-answer checks (section 9) |
| API restarts mid-demo | In-memory runs lost | One instance, always-on plan, no deploys during the demo window |
| Retried task duplicates events | Double comments | Idempotent `event_id` |
| Guardrail miss: invented facts in a post | Credibility, safety | Post-validation in code (section 9), reviewed during rehearsal |
| CORS or `NEXT_PUBLIC_API_URL` misconfigured after deploy | Frontend cannot reach the API | M1 round-trip test on the deployed URLs before building features |
| Render SDK differs from these notes | Blocked early | The M1 round-trip test comes first; update this file with what you learn |
