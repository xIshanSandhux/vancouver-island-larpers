# Thought Leadr: requirements

Hackathon: LarpHacks (a DevFest event). Theme: **"Create a product to help you LARP as someone you are not."**
Team: Mahir and Ishan. Competing in the **main track** and the **Render sub-track** ("deploy a working app using Render Workflows").

`architecture.md` says how it is built. `agents.md` says who builds what and how to work in this repo.

## 1. Product

**One-sentence pitch:** Type something boring and Thought Leadr turns it into a LinkedIn-style thought-leader post, then tests it on 50 simulated commenters, so you can LARP as a thought leader (or find out how cringe your real draft is) before you post.

**Two modes**

1. **Generate** (the joke): a boring sentence ("I got a coffee and went to a meeting") becomes 20 posts in 20 different "voices". The best 3 are tested on a simulated audience of 50 fictional commenters, ranked, and the winner is shown with a "reality toggle" that reveals what actually happened.
2. **Check** (the useful part): paste a real draft. The same 50 commenters react, a cringe score explains why, and a "tone down" button rewrites it with less hype.

**Who it is for:** people who post on professional networks and want to know how a post reads before they publish; everyone who has read one of these posts and wants to see the genre mocked.

**Honest positioning (important for Q&A):** it is a *rehearsal audience and cringe check*, not a prediction of real engagement. The simulated audience is made of stereotyped fictional personas run by language models. Nothing here is validated against real posts. The UI labels counts as "simulated audience".

## 2. Scope

### In scope
- Generate mode and Check mode as described above.
- 20 fixed voices, 50 fixed personas (10 archetypes x 5), two-stage pipeline (20 posts, filter to 3, 50 commenters on each).
- Live-streaming comment section (browser polls once a second).
- Cringe score with reasons (rule-based plus model flags).
- Reality toggle, tone slider (client-side re-rank), tone-down rewrite.
- Demo failure switch so the retry shows up in the Render dashboard.
- Deploy on Render as three services from one repo: the Next.js frontend (web service), the FastAPI API (web service) and the Python Workflow service (the Render sub-track requirement).
- LinkedIn-*style* UI under our own name and colours, framed on screen as "Larping as: Thought Leader".
- Basic ease-of-use polish (example inputs, loading, error and busy states) and abuse protection for a public URL.

### Out of scope (explicitly cut, do not build)
- ElevenLabs voice or audio, Agentboxd inboxes, any other sponsor integration except the stretch items below.
- User accounts, authentication, saved history, any database.
- A cached-replay or offline fallback mode in the app.
- Posting to any real social network, scraping, or using anyone's real profile.
- Mobile apps, i18n, accessibility audits beyond sensible defaults.
- Predicting real engagement numbers.

### Stretch (only after the core demo works end to end, and only if time allows)
- PostHog analytics (I9).
- Sentry error tracking in both services (I9).
- ConfigCat (a hackathon sponsor) feature flag for Demo mode. Only if it takes minutes; it earns nothing in the Render sub-track.

## 3. Functional requirements

Each requirement has an ID used in `agents.md` task cards. "Done when" is the acceptance test.

**FR-1: Start a generate run.**
The home page has one text box (max 280 characters), a Generate button, and a Demo mode toggle. Submitting calls `POST /api/runs` and shows a live run view.
*Done when:* typing a sentence and clicking Generate creates a run, the UI shows a stage label, and the page reaches a final state without a reload.

**FR-2: Generate 20 post variants.**
Using Claude, produce 20 posts, one per voice in `data/voices.json` (humblebrag, hot take, story-time, lessons-learned, "I was fired" confessional, unpopular opinion, gratitude, leadership-from-coffee, numbered list, "nobody talks about", and 10 more). Each post is 40 to 140 words and must follow the guardrails in section 5.
*Done when:* a run produces 20 variants with distinct `voice_id`s, all passing the guardrail validation, in under about 10 seconds.

**FR-3: Filter to three finalists.**
Score all 20 with the deterministic `hype_score` and take the top 3 with distinct voices.
*Done when:* given the same variants, `filter_top3` always returns the same 3, with distinct voices.

**FR-4: Simulated audience.**
For each finalist, 50 personas react. Each persona returns `action` (like, comment, ignore, report), an optional short comment, an `appeal` (1 to 5) and a `cringe_flag`. Personas come from `data/personas.json`.
*Done when:* a run produces 150 comment results (50 x 3) with valid structure, and a malformed model answer never crashes the run (it falls back to a default and is logged).

**FR-5: Live comment section.**
Comments appear in the UI as events arrive, in a feed that looks like a social post: post card, reactions bar (like counts), and a comment thread with fictional names and labels.
*Done when:* during a run, new comments visibly appear before the run completes, and the UI never shows the same comment twice.

**FR-6: Cringe score with reasons.**
Each finalist shows a 0 to 100 cringe score and up to 5 plain-language reasons ("3 humblebrag phrases", "engagement-bait ending").
*Done when:* the score is deterministic for the rule part (same text gives the same rule score), and unit tests cover every rule feature and the blend.

**FR-7: Ranking and winner.**
Finalists are ranked by the formula in `architecture.md` section 8. The winner is highlighted.
*Done when:* the ranking matches the shared test case in both Python and TypeScript.

**FR-8: Reality toggle.**
A toggle on the winning post reveals the user's original sentence beside it, plus a one-line translation of what got inflated and up to 3 short inflated phrases.
*Done when:* toggling shows the original verbatim and a non-empty translation; the toggle works with no extra network call.

**FR-9: Tone slider.**
A slider (0 to 1) changes how much the cringe score is penalised in the ranking. Moving it re-orders the finalists instantly in the browser.
*Done when:* dragging from 0 to 1 can change the order of finalists, with no network call, and the order is the same for the same inputs.

**FR-10: Check mode (paste a draft).**
A second page takes a pasted draft (max 3000 characters), runs the same 50 personas, and shows reactions, the cringe score with reasons, and a Tone down button.
*Done when:* pasting a draft shows live comments, a cringe score, and reasons, and the run finishes in under about 20 seconds.

**FR-11: Tone-down rewrite.**
The Tone down button rewrites the draft to remove the triggered features while keeping the facts, then shows the new text with the cringe score before and after (the after score uses the rule-based part only).
*Done when:* the rewritten draft has a lower rule score than the original for a known-cringe sample, and introduces no numbers or names that were not in the draft.

**FR-12: Demo failure switch.**
With Demo mode on, exactly one commenter batch fails on its first attempt and Render retries it. The UI shows a labelled badge and "Retried 1 task automatically". The Render dashboard shows the failed attempt and then the success.
*Done when:* with the toggle on, every run shows one retry and still completes; with it off, no failure is injected.

**FR-13: Deployment on Render.**
The frontend, the FastAPI API and the Workflow service are deployed on Render and reachable at public URLs. The Workflow service uses Render Workflows tasks with retries and parallel child runs. Judges check that a working app is deployed using Render Workflows, so this is also the sub-track evidence.
*Done when:* a run started from the deployed frontend URL appears as task runs (with at least one parent and several parallel child runs) in the Render dashboard, and the three URLs are in the README.

**FR-14: Branding, theme framing and guardrails.**
The product uses its own name and colours. It never uses LinkedIn's logo, name or exact brand colours. The UI states the theme plainly, for example a header chip "Larping as: Thought Leader" on the Generate page and "Larping as: someone with a good post" on the Check page. Generated posts exaggerate tone only, never facts (see section 5).
*Done when:* no LinkedIn logo or name appears in the UI, the theme chip is visible in the demo, and the guardrail validator rejects an output that adds a number or a name not in the input.

**FR-15: Analytics and error tracking (stretch).**
PostHog events and Sentry in both services, with post text scrubbed.
*Done when:* a run produces PostHog events and a thrown test error appears in Sentry without including post text.

**FR-16: Consistency check (supporting script).**
A script runs the same input twice and prints the rank correlation between the two rankings. A small set of known-cringe vs plain posts is scored and checked for separation.
*Done when:* the script runs from the command line and prints both numbers, which you can quote in Q&A.

**FR-17: Ease of use.** (Ease of use is one of the six judged categories.)
A first-time visitor can use the app with no instructions. Each page has: a one-click "try an example" input, a clear primary button, a visible loading state with a stage label, a plain-language error state with a Try again button, and a friendly busy message. Text is readable at a projector distance.
*Done when:* someone who has never seen the app gets a result within 15 seconds of opening it, using only the example button, and every failure path (backend down, busy, timeout, invalid input) shows a message instead of a blank or frozen page.

**FR-18: Abuse and load protection.**
The public API limits input length, rejects obviously abusive input, caps simultaneous runs and per-IP rate, and answers with a friendly "busy" response instead of failing (`architecture.md` section 10). This protects model credits and the Render compute budget while judges and attendees try the app.
*Done when:* a third simultaneous run gets a 429 with the busy message, an over-length input gets a 400, and neither reaches Render or a model.

## 4. Non-functional requirements

- **Latency:** a full generate run finishes in about 30 seconds or less, measured on the deployed services. Comments should start appearing within about 15 seconds. If you cannot hit this, reduce batch counts (see `architecture.md` 5.1) before cutting features.
- **Reliability:** a bad model answer must degrade (default result, logged), not crash the run. Event delivery is idempotent.
- **Security:** no secrets in git. Internal endpoints require the shared secret. Input is length-limited. All text is rendered as plain text in the UI (no HTML injection).
- **Observability:** every log line carries the `run_id`. The Render dashboard is part of the demo.
- **Cost and budget:** about 171 model calls per generate run, and about 12 Render task runs. Count rehearsals and testing against both, and expect attendees to try the app during judging (see FR-18).
- **Public-URL hygiene:** keep the deployed URLs out of public channels (Discord, social) until your demo slot is done; share them in the submission only.
- **Compatibility:** the demo runs in a current desktop Chrome at 1440 px wide. The page should not break at narrow widths but is not optimised for phones.

## 5. Content and safety guardrails

1. **Tone, not facts.** Generated posts may inflate the *framing* of what the user said. They must not add employers, job titles, schools, numbers, named people, or companies that were not in the input.
2. **Fictional audience.** All personas have fictional first names and generic role labels. No real people, no public figures, no real company names.
3. **Own branding.** Parody the genre, not a company. No LinkedIn logo, name, or exact colours.
4. **No deception tooling.** The product helps users rehearse and check tone. It is not for fabricating a real professional profile. The README/demo copy says so in one line.
5. **Honest accuracy.** Counts are labelled "simulated audience". Never show an engagement number as a prediction.
6. **User text is data, not instructions.** Input is delimited in prompts, never placed in a system prompt, and an answer that echoes instructions is discarded. Hateful, harassing or sexual input is declined or blocked. The app runs on a public URL in front of judges, so assume someone will try something rude.

## 6. Accuracy and how we talk about it

- Relative judgments (which draft is more cringe) should be stable. Absolute predictions (how many likes) are not claimed.
- Evidence we can show in Q&A: the consistency script (FR-16) reports rank correlation between two runs of the same post, and a small known-cringe vs plain set shows the score separates them.
- Honest answers to likely questions:
  - *"Why not just ask ChatGPT?"* It runs 150 independent persona reactions in parallel and ranks them with a repeatable cringe score; the fan-out is the product, and it is what Render Workflows is for.
  - *"How accurate is it?"* It is a rehearsal audience, not a forecast. We measured that rankings are stable between runs and that the cringe score separates known-cringe posts from plain ones.
  - *"What did Render do?"* The task graph: variant batches, commenter batches, reality translation, retries, all as Workflow task runs.
  - *"Is it making things up about people?"* No. It only exaggerates tone around what you typed, and we validate that in code.
  - *"Why would anyone use this?"* People rewrite posts before publishing and want a blunt second opinion; the Check mode tells you which phrases read as hype and offers a toned-down rewrite.
  - *"What happens if the model fails?"* Bad JSON gets one retry, then a safe default; a failed task is retried by Render, and the UI shows it instead of hanging.
  - *"What would you build next?"* Audiences tuned to an industry, a browser extension for the real feed, and calibrating the cringe score against real labelled posts.
  - *"Did you write all of this today?"* Yes. All code was written during the hackathon.

## 7. Demo (2 minutes, 5 to 7 seconds of it intro)

Only features that appear in this script get built before the feature freeze.

| Time | Screen | Say |
|---|---|---|
| 0:00 to 0:07 | Title screen | "We are Mahir and Ishan. Everyone on LinkedIn is LARPing as a thought leader. Thought Leadr turns anything boring into one, and tests it on 50 fake commenters first." |
| 0:07 to 0:20 | Type "I got a coffee and went to a meeting", click Generate (Demo mode on) | "Real input, nothing prepared." |
| 0:20 to 0:55 | Comment section streams in on the left; Render dashboard with parallel task runs on the right | "Every draft and every commenter batch is a Render Workflow task run in parallel, with retries and durable steps." |
| 0:55 to 1:15 | Winner appears with cringe score. Toggle reality view. Drag the tone slider so the ranking changes. | "The funniest part is the gap between what happened and what we claimed." |
| 1:15 to 1:35 | Check page: paste a real draft, see reactions, cringe score and reasons | "This is the useful half: check how a post reads before you publish." |
| 1:35 to 1:50 | Dashboard: one task failed and was retried, then succeeded; UI badge says "Retried 1 task automatically" | "A task failed on purpose in demo mode, Render retried it, and finished work was not redone." |
| 1:50 to 2:00 | Result screen | "Thought Leadr. LARP as a thought leader, or find out you already are." |

Rubric mapping (each is 5 points): working product and ease of use come from the first minute; usefulness is the Check mode beat; theme is the product premise; creativity is the simulated audience and reality toggle; demo is the rehearsed script and the visible Render dashboard.

## 8. Schedule (hacking 11:00 AM to a hard 6:00 PM submission)

| Time | Target |
|---|---|
| 11:00 to 11:45 | M1 contracts and the first Render deploy of all three services, with the event round trip working on the deployed URLs (the Next.js and FastAPI templates are already on `main`). Ishan starts I1 and I3 (independent). Measure task startup latency now. Mahir also starts M9 (abuse guard) once M5 exists. |
| 11:45 to 1:00 | Mahir: M2 variants. Ishan: I2 commenters (provider and concurrency test), I5 feed UI against sample JSON. First merges to `main`. |
| 1:00 to 2:00 | Food break; merge what is ready. |
| 2:00 to 3:30 | Integration: M3, M4, M5 with I2/I3 real code. UI wiring (M6, I6). Full generate run end to end by 3:30. |
| 3:30 to 4:30 | M7 failure switch, M8 timing and tuning, I4 tone-down, I7 sanity script. **Feature freeze at 4:30.** Optional: I9 stretch only if everything above is done. |
| 4:30 to 5:00 | Food break and bug-fix only. |
| 5:00 to 5:45 | Rehearse the demo at least three times with a timer. Warm up Render. Record a backup screen recording (optional). Submit by 5:45. |
| 6:00 | Hard submission deadline. |

The 2:30 to 3:30 Google workshop is optional; only attend if you are ahead of schedule.

After submission: **6:30 to 8:00 PM demos and judging**, then **8:00 to 9:00 PM closing ceremony and awards** (networking after). Stay near your laptop from 6:00, with the demo already warmed up and the Render dashboard open. You do not know your slot in advance, so be ready to demo at any time from 6:30.

## 9. Definition of done

- All of FR-1 to FR-14 pass their "Done when" checks on the **deployed** services (FR-15 and FR-16 if time).
- The demo script runs in 2 minutes or less, three times in a row, without errors.
- No secrets in git. `.env.example` files committed. `main` deploys cleanly.
- Both people can explain every box in the architecture diagram for Q&A.

## 10. Demo-day checklist

- [ ] Render web and workflow services running; keys and secrets set; `WEB_BASE_URL` correct.
- [ ] Render workspace plan checked (compute-per-minute limit) and rehearsal runs counted against it.
- [ ] Hit the web URL and run once 5 minutes before going on to warm everything.
- [ ] Demo mode toggle tested on and off.
- [ ] The exact input sentence and a pre-picked cringe draft saved in a note.
- [ ] Render dashboard open in a second window, already filtered to the workflow service.
- [ ] Browser zoom set, notifications off, screen sharing tested.
- [ ] Roles fixed: one person talks, the other drives. No switching mid-demo.
- [ ] Optional: a backup screen recording of a perfect run on the laptop.
- [ ] Render proof captured: dashboard screenshot of one run's parent and parallel child task runs, and one showing the retry.
- [ ] Sub-track chosen on the submission form: **Render** (only one allowed).
- [ ] Submission completed before 6:00 PM (target 5:45), including the items in section 13.
- [ ] Deployed URLs not shared in public channels; the guard limits are on.

## 11. Rules to remember

- All code must be written during the hackathon. Do not copy code from earlier projects (including the earlier Penny finance app).
- Submit one project. It competes in the main track automatically and in **one** chosen sub-track (Render). Judges score the main track and indicate whether it qualifies for the sub-track, so you do not build two projects.
- Hard submission deadline is 6:00 PM. Demos are 2 minutes plus 2 minutes of questions.

## 12. Measurements to record (M8, before rehearsal)

These turn Q&A answers into facts. Put the numbers in the README or a note.

- Time from click to first comment and to final result on the deployed services, over 5 runs (mean and worst).
- Render task startup latency for a chained run, and the number of task runs per generate run and per check run.
- Model call counts and failure or retry counts per run.
- Rank correlation between two runs of the same input, and the known-cringe vs plain separation (FR-16).
- Whether the Render workspace plan blocked or throttled any run.

## 13. Event facts, prizes, rubric and submission

**Prizes we are targeting (from the opening ceremony):**
- Render sub-track, "Best Use of Render: deploy a working app using Render workflows": $500, $300 and $100 **in Render credits** (not cash) for first, second and third. Organizers distribute prizes separately.
- Main track: $300 first, $150 second, $67 third. First place also gets $297 of ElevenLabs credits each and $300 of Featherless credits (we use Featherless, not ElevenLabs).

**Main-track rubric (6 categories, 5 points each, 30 total):** working product, usefulness, theme, creativity, ease of use, demo. Self-check before submitting:

| Category | Our evidence | Gap to watch |
|---|---|---|
| Working product | Deployed, end-to-end run on the live URL | Latency; run it three times in a row |
| Usefulness | Check mode: cringe reasons plus a tone-down rewrite | Say it is a rehearsal check, not a forecast |
| Theme | "Larping as: Thought Leader" framing; reality toggle shows the gap | Make the theme chip visible on screen |
| Creativity | Simulated 50-person audience, reality toggle | Keep the persona comments genuinely funny |
| Ease of use | One box, example chips, clear states (FR-17) | Test with someone who has not seen it |
| Demo | Rehearsed 2-minute script, visible Render dashboard | Practise the 5 to 7 second intro |

**Logistics and contacts:** team formation at 10:30 AM, hacking from 11:00 AM, snacks 1:00 to 2:00, Google workshop 2:30 to 3:30, lunch/dinner 4:30 to 5:00. Questions during the event: hello@larphacks.ca. Announcements are on the event Discord.

**Sponsor perks worth claiming (a few minutes each, none required):**
- Featherless AI: dropped. Its API was not working on the day, so every model call goes to Anthropic Claude instead.
- Render: sponsor notes list **$50 in building credits per hacker**. The LarpHacks redemption code and claim steps were still pending when we signed up, so ask the organizers (Discord or hello@larphacks.ca). After redeeming, check the credit appears in the **workspace you deploy into** before creating paid resources. A successful free deployment does not mean the credit was applied. Free web services sleep after inactivity (cold start), so before the demo move the API and frontend to a paid always-on plan using the credit. Also ask the Render team for a plan or credits if the Hobby compute limit throttles runs.
- PostHog and Sentry are stretch only.

**Submission package (I8; the exact form is not in the slides, so confirm the fields with the organizers early, via the Discord or hello@larphacks.ca):** project name and one-line description, the live frontend URL, a link to the repository (confirm whether it must be public), the chosen sub-track (Render), team members, and a short description of how Render Workflows is used. Prepare the blurb in appendix B and the Render proof screenshots in advance.

## Appendix A: demo content (pre-picked, tested end to end)

- **Generate input:** `I got a coffee and went to a meeting.`
- **Check-mode draft** (invented and deliberately cringe; no real people or companies):

```
I was fired on a Tuesday.

Nobody talks about what happens next.

I cried in a parking lot at 3am.

Then I learned 3 lessons that changed my life:

1. Growth mindset beats talent
2. Leverage your journey
3. Stay humble, stay hungry

I'm humbled and grateful to share this.

Agree? 🚀🔥💯 #leadership #growth #journey #hustle
```

Expected: a high rule-based cringe score with reasons such as hook phrase, fake vulnerability, listicle, humblebrag, engagement bait, emoji overload and hashtags.

## Appendix B: submission blurb (draft; edit once the numbers are known)

> **Thought Leadr** lets you LARP as a LinkedIn thought leader. Type something boring ("I got a coffee and went to a meeting"), and it writes 20 posts in 20 voices, picks the three most thought-leader-ish, and tests them on a simulated audience of 50 fictional commenters (a recruiter, the "Agree?" guy, an AI-pivot bro, and more). You get a ranking, a cringe score with reasons, and a reality toggle that shows what actually happened. Paste a real draft in Check mode to see how it reads and get a toned-down rewrite. The simulated audience is a rehearsal tool, not an engagement forecast.
>
> **Render Workflows:** every run is a durable task graph: a root task fans out variant-writing and commenter tasks as parallel child runs with automatic retries, results stream to the UI as they finish, and a demo mode injects a failure that Render retries visibly. Stack: Next.js, FastAPI, Python Render Workflows and Claude.
