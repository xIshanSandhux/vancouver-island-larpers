# agents.md: instructions for AI coding agents (Claude Code and Codex)

You are helping **Mahir** or **Ishan** build **Thought Leadr** at the LarpHacks hackathon. The deadline is a hard **6:00 PM** submission, with about 7 working hours in total. Move fast, keep changes small, and keep `main` deployable.

This one file is the shared instruction file for both tools. Claude Code reads `CLAUDE.md`, which contains one line importing this file. Codex reads `AGENTS.md`. On macOS the filesystem is case-insensitive, so `agents.md` and `AGENTS.md` are the same file locally. If you are on Linux or CI and `AGENTS.md` is missing, copy or symlink it from `agents.md`.

## 1. What this project is (30-second version)

Thought Leadr turns a boring sentence into a LinkedIn-style "thought leader" post, tests it on 50 simulated commenters, and also checks real drafts for cringe. It must be deployed on Render and use **Render Workflows** (that is the sub-track we are competing in).

- Product, scope and acceptance tests: `requirements.md`
- Design, contracts, task graph, env vars: `architecture.md`
- Ideas history (ignore for implementation): `ideas.md`

**Read `requirements.md` and `architecture.md` before writing code.** If they disagree with a task card below, tell the user instead of guessing.

## 2. Golden rules

1. **Stay in your lane.** Edit only files owned by the person you are working for (see the ownership list in `architecture.md` section 2 and the task cards below). If a change is needed in someone else's file, stop and ask the user to coordinate.
2. **Shared contracts need both people.** `workflows/models.py`, `web/lib/contracts.ts` and `data/samples/*.json` describe the same shapes. A change to one must update the others in the same PR, and both people must agree.
3. **Never commit secrets.** API keys live in Render environment settings and local `.env` files. `.env*` is git-ignored. Commit `.env.example` with names only.
4. **Never break `main`.** Render auto-deploys `main` for both services. Run the checks in section 5 before opening a PR.
5. **No copied code.** The hackathon rules require all code to be written during the event. Do not paste code from earlier projects (including the earlier Penny app).
6. **Scope discipline.** Do not add features outside `requirements.md`. Explicitly cut: ElevenLabs, Agentboxd, accounts/auth, databases, saved history, replay or offline mode, real social-network integrations. Stretch items (PostHog, Sentry) are done only after the core demo works.
7. **Guardrails are product requirements.** Generated posts exaggerate tone only, never facts. No real people's names, no LinkedIn logo, name or exact colours. See `requirements.md` section 5 and `architecture.md` section 9.
8. **Verify the Render SDK instead of guessing.** Anything marked **VERIFY** in `architecture.md` must be checked against https://render.com/docs/workflows before you depend on it. When you learn the real answer, update `architecture.md` in the same PR (tell the user, since it is shared).
9. **Prefer boring, small, working code.** The demo must run reliably for two minutes. Do not refactor for elegance.

## 3. Tech stack

- **Web:** Next.js (App Router), TypeScript, Tailwind CSS, `zod` for validation, `@renderinc/sdk` to start task runs. Deployed as a Render web service.
- **Workflows:** Python 3.11+, the Render Workflows Python SDK (`Workflows` app, `@app.task`, `ctx.run`), `pydantic` for models, `httpx` for outgoing HTTP, `anthropic` and an OpenAI-compatible client (`openai` package pointed at Featherless), `pytest`. Deployed as a Render Workflow service.
- **Models:** Anthropic Claude for variants, reality translation and rewrite. Featherless AI for the commenter personas (with an `anthropic` fallback via `COMMENTER_PROVIDER`).
- **Data:** static JSON in `data/`. No database.

## 4. Commands

These are the intended commands. Whoever finishes **M1** must confirm or correct this section in the same PR.

```bash
# Web
cd web
npm install
npm run dev          # http://localhost:3000
npm run lint
npm run typecheck    # tsc --noEmit
npm test             # vitest (rank.ts, contracts)

# Workflows (Python)
cd workflows
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q            # unit tests (cringe, ranking, guardrails)
python main.py       # starts the workflow app (VERIFY how to run tasks locally)
```

Local development without Render: the web app can be run against `data/samples/*.json` (a mock mode set with `NEXT_PUBLIC_USE_SAMPLES=true`), so the UI work does not wait for the workflow service. The workflow tasks can be exercised in `pytest` by calling their inner functions directly with a fake event poster.

## 5. Before every PR

- [ ] `npm run lint && npm run typecheck && npm test` (if you touched `web/`)
- [ ] `pytest -q` (if you touched `workflows/`)
- [ ] Contracts changed? Then both `models.py` and `contracts.ts` and the samples changed too, and the other person was told.
- [ ] No secrets, no `.env`, no large files.
- [ ] The PR is small (aim for under about 400 changed lines) and describes the task ID, the FR IDs it satisfies, and how you checked it.

## 6. Git workflow

- Branch from the latest `main`. One branch per task card: `mahir/<name>` or `ishan/<name>` (names are listed in the cards).
- Commit often with clear messages starting with the task ID, for example `M2: add 20 voice templates`.
- Open a pull request into `main` when the task's "done when" is met, **not later than 1 to 2 hours after starting**. Do not leave a branch unmerged for long: integration pain grows fast near the deadline.
- Before opening a PR run `git fetch origin && git rebase origin/main`, then re-run the checks in section 5.
- The *other* person (or the user) reviews and merges. If the other person is busy and the checks pass, the author may merge their own PR.
- Never force-push to `main`. Never rewrite history on a branch someone else is using.
- Merge checkpoints (everyone merges what is ready): **12:30, 2:00, 3:30, 4:30 (freeze)**. After 4:30 only bug fixes and the optional stretch tasks.

## 7. Conventions

- **Naming:** Python `snake_case`, classes `PascalCase`; TypeScript `camelCase`, components `PascalCase`. Follow the file and folder layout in `architecture.md` section 2 exactly.
- **Types:** type everything. Pydantic models for every payload in Python, zod schemas for every payload in TypeScript. Parse model outputs with the models; never trust raw JSON.
- **Errors:** model calls have a 20 s timeout and one retry for transient errors. A malformed model answer must degrade to a default and be logged, never crash a run.
- **Logging:** Python `logging`, always include `run_id`. Do not log full model outputs or post text at INFO.
- **Comments:** keep them short and explain *why*, not *what*. Match the surrounding code's comment density.
- **UI text:** plain text only. Never use `dangerouslySetInnerHTML`.
- **Idempotency:** every posted event has an `event_id`; a retried task may re-send the same one.

## 8. Task board

The work is split into two feature slices. Each person owns UI and backend for their slice. Estimates are ideal hours with an AI agent helping; both people have **6.75 h**.

Shared engine rule: **Ishan owns the commenter task and its contract; Mahir's pipeline calls it as a child task.** Until Ishan's task lands, Mahir uses a stub that returns canned `CommentResult`s.

### Mahir: "Generate" slice (6.75 h)

| ID | Task | Branch | FRs | Est. | Depends on |
|---|---|---|---|---|---|
| **M1** | Scaffold repo: `web/` Next.js app, `workflows/` Python service, `data/`, shared contracts in `models.py` + `contracts.ts` + `data/samples/`, **stub `cringe/` module with the signatures from `architecture.md` section 7**, `events.py`, config, `.env.example` files, `.gitignore`. Create both Render services, set env vars, and prove the round trip: `POST /api/runs` starts `run_pipeline`, which posts `run_started` and `run_completed` events, and `GET /api/runs/:id` shows them. Measure task startup latency and note the workspace plan limits. Confirm or fix section 4 of this file. | `mahir/scaffold-and-deploy` | FR-13 | 1.0 | none (first PR; Ishan starts I1/I3 in parallel) |
| **M2** | `data/voices.json` (20 voices with prompt templates), `llm/anthropic_client.py`, `write_variant_batch` and the `run_pipeline` variant stage, guardrail validator (no new numbers or names), tests. | `mahir/variants` | FR-2, FR-14 | 1.0 | M1 |
| **M3** | `filter_top3` (uses `cringe.hype_score`), ranking in Python and `web/lib/rank.ts`, shared test case `data/samples/ranking_case.json` used by both languages, plus the aggregation step in `run_pipeline` that builds `PostScore`s and `ranking_ready`. | `mahir/rank-and-filter` | FR-3, FR-7, FR-9 | 0.75 | M1; stubs for I2 and I3 |
| **M4** | `translate_reality` task (one Claude call, JSON `{translation, inflations}`), validation, tests. | `mahir/reality-translation` | FR-8 | 0.5 | M1 |
| **M5** | Web API and state: `runStore.ts`, `render.ts` (wraps `@renderinc/sdk`), routes `POST /api/runs`, `GET /api/runs/[id]`, `POST /api/runs/[id]/events`, `useRun.ts` polling hook (1 s, 120 s timeout), sample mock mode. | `mahir/run-api-and-polling` | FR-1, FR-5 (plumbing) | 1.0 | M1 |
| **M6** | Generate page: input box with length limit, Demo mode toggle, stage label, ranked finalists list, reality toggle, tone slider (client re-rank via `rank.ts`), retry badge, link to the Render dashboard. Uses Ishan's feed components. | `mahir/generate-ui` | FR-1, FR-7, FR-8, FR-9 | 1.25 | M5; I5 (can start with a placeholder) |
| **M7** | Demo failure switch: `POST /api/runs/[id]/demo-fail-claim`, designated batch logic in `run_pipeline`, `demo_failure_triggered` event, `retries_seen` in the UI, verify in the Render dashboard that a retry appears. | `mahir/demo-failure-switch` | FR-12 | 0.75 | M5; I2 |
| **M8** | Integration owner: end-to-end timing on the deployed services, tune `VARIANT_BATCHES` / `COMMENTER_BATCHES_PER_POST` / `LLM_CONCURRENCY`, fix integration bugs, own the demo script and checklist in `requirements.md`, rehearsal and submission. | `mahir/integration-and-demo` | FR-13 | 0.5 + ongoing | M1 to M7 |

### Ishan: "Audience and check" slice (6.75 h)

| ID | Task | Branch | FRs | Est. | Depends on |
|---|---|---|---|---|---|
| **I1** | `data/personas.json`: 50 fictional personas (10 archetypes x 5 variations; fields in `architecture.md` section 10) and the commenter prompt text. No real people. | `ishan/personas` | FR-4, FR-14 | 1.0 | none |
| **I2** | `llm/featherless_client.py` and `run_commenter_batch`: concurrent persona calls with a semaphore, strict JSON validation, one reminder retry then default, per-persona `comment` events, the `COMMENTER_PROVIDER` switch. **Test Featherless concurrency in the first hour** and switch to the Anthropic provider if it is too slow. | `ishan/commenters-task` | FR-4, FR-5 | 1.0 | M1; I1 |
| **I3** | `cringe/` module: `features`, `rule_score`, `score`, `hype_score`, `data/cringe_lexicon.json`, unit tests for every feature and the blend (spec in `architecture.md` section 7). | `ishan/cringe-score` | FR-6 | 1.0 | M1 stub (replace it) |
| **I4** | `run_tone_down` task (Claude rewrite that keeps facts, re-score with rule part only), `POST /api/runs/[id]/tone-down` route, and the UI hook. Guardrail check on the rewrite. | `ishan/tone-down` | FR-11 | 0.75 | M1; I3 |
| **I5** | Feed UI components in `web/components/feed/`: `PostCard`, `ReactionsBar`, `CommentThread` (animated append, no duplicates), `CringeMeter` with reasons. Our own branding and colours. Build against `data/samples/` so it does not wait on the backend. | `ishan/feed-ui` | FR-5, FR-6, FR-14 | 1.25 | M1 (contracts and samples) |
| **I6** | Check page `web/app/check/page.tsx`: paste box (3000 characters), run, live comments, cringe score and reasons, Tone down button and before/after view. | `ishan/paste-draft-ui` | FR-10, FR-11 | 0.75 | M5; I2; I3; I5 |
| **I7** | `workflows/scripts/consistency.py`: runs the same input twice and prints rank correlation; a known-cringe vs plain set (10 and 10) and a printed separation result. Notes for Q&A. | `ishan/sanity-checks` | FR-16 | 0.5 | I2; I3 |
| **I8** | Stretch (only after the core demo works): PostHog events and Sentry in both services with post text scrubbed; then Q&A prep notes. | `ishan/analytics-and-sentry` | FR-15 | 0.5 | everything above works |

### Dependency summary

```
M1 -----> M2 -> M3 ----------------> M6 --> M7 --> M8
  |        \                          ^
  |         +--> (stubs for I2, I3)   |
  +--> M4, M5 ----------------------> +--> I6
  |
  +--> I2 (needs I1) -> I7
  +--> I3 -------------> I4
  +--> I5 ---------------^
I1, I3 can start immediately (before M1 merges).
```

## 9. How to work a task card (agent checklist)

1. Read the card, its FRs in `requirements.md`, and the matching sections of `architecture.md`.
2. `git fetch && git checkout -b <branch> origin/main`.
3. List the files you will touch. If any are outside your owner's lane or are shared contracts, stop and ask the user.
4. Write tests first where the card calls for them (cringe, ranking, guardrails, JSON validation).
5. Implement the smallest thing that meets "done when". Use the sample data and stubs so you are never blocked by the other person.
6. Run the checks in section 5. Run the feature locally if you can.
7. Commit with the task ID, rebase on `main`, open a small PR, and summarise what you did, how you verified it, and anything you assumed.
8. Tell the user if you changed a contract, an env var, or a **VERIFY** item.

## 10. Do-not list

- No ElevenLabs, Agentboxd, accounts, auth, databases, history, replay mode.
- No LinkedIn logo, name or exact brand colours. Product name is **Thought Leadr**.
- No real people, public figures or real company names in personas, prompts or UI.
- No invented facts in generated posts: no new numbers, names, employers or titles.
- No engagement predictions presented as real. Label counts "simulated audience".
- No secrets in the repo, no `.env` committed, no keys in screenshots.
- No force-push to `main`. No deploying a broken `main`.
- No new dependencies unless needed; tell the user when you add one.
- No work after the **4:30 PM feature freeze** except bug fixes and the optional stretch tasks.

## 11. If you get stuck

- Render SDK behaviour differs from `architecture.md`: check https://render.com/docs/workflows and the SDK reference, fix the doc, tell the user.
- Model output is flaky: tighten the prompt, validate with the model class, add the default, log it. Do not add long retry loops.
- Latency too high: lower `VARIANT_BATCHES` and `COMMENTER_BATCHES_PER_POST`, check the Render per-minute compute limit, and consider `COMMENTER_PROVIDER=anthropic`.
- A task is bigger than its estimate: cut scope to the "done when", say what you cut, and move on.
