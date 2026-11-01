# Thought Leadr

Thought Leadr is a rehearsal tool for professional posts. Type an ordinary event, generate several exaggerated drafts, and test the finalists against 50 fictional audience members. In **Check** mode, paste a real draft to see its cringe signals and request a more grounded rewrite.

Built for LarpHacks using Render Workflows and Claude.

## Product flows

```text
                    +------------------+
                    |  Thought Leadr   |
                    |  Next.js frontend|
                    +--------+---------+
                             |
                 start run + poll every second
                             |
                             v
                    +--------+---------+
                    | FastAPI API      |
                    | in-memory state  |
                    +---+----------+---+
                        |          ^
            start task |          | progress events
                        v          |
                 +------+----------+------+
                 | Render Workflow       |
                 |                       |
                 | Generate:             |
                 | variants -> finalists|
                 | -> commenters -> rank|
                 | -> reality            |
                 |                       |
                 | Check:                |
                 | commenters -> score   |
                 |                       |
                 | Tone down: rewrite   |
                 +-----------+-----------+
                             |
                             v
                       +-----+------+
                       | Claude API |
                       +------------+
```

The API keeps run state in memory. Workflow tasks post idempotent events back to the API, and the browser polls the resulting `RunState`. This makes comments and scores appear while a run is still in progress without polling the Render API from the browser.

## Repository guide

| Path | Purpose |
|---|---|
| `frontend/` | Next.js App Router UI for Generate and Check |
| `backend/app/` | FastAPI routes, shared models, in-memory store, and Render trigger |
| `backend/workflows/` | Render Workflow tasks for generation, comments, ranking, reality translation, and Tone down |
| `backend/cringe/` | Deterministic cringe feature extraction and scoring |
| `data/` | Personas, voices, phrase lexicons, and shared sample contracts |
| `backend/tests/` and `frontend/**/*.test.*` | Backend and frontend test suites |

For the full contracts, event lifecycle, workflow details, deployment settings, and guardrails, read the [architecture guide](architecture.md).

Other project references:

- [Product requirements](requirements.md)
- [Agent instructions](agents.md)
- [Frontend setup](frontend/README.md)

## Local setup

### Backend

Python 3.11+ is recommended.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Fill in ANTHROPIC_API_KEY, Render settings, and workflow settings in .env.
```

Run the API:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

The health endpoint is <http://localhost:8000/health>.

### Frontend

Node 20+ is recommended.

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open <http://localhost:3000>. The frontend uses `NEXT_PUBLIC_API_URL` to find the API. Set `NEXT_PUBLIC_USE_SAMPLES=true` when developing the UI without a running backend.

## Environment variables

Backend variables are listed in [`backend/.env.example`](backend/.env.example). Frontend variables are listed in [`frontend/.env.example`](frontend/.env.example).

Important frontend variables:

- `NEXT_PUBLIC_API_URL`: public FastAPI URL; defaults to `http://localhost:8000`.
- `NEXT_PUBLIC_RENDER_DASHBOARD_URL`: optional dashboard link shown in the app.
- `NEXT_PUBLIC_USE_SAMPLES`: enables sample-driven frontend development.

Important backend variables:

- `ANTHROPIC_API_KEY`: Claude access for all model calls.
- `CLAUDE_MODEL`: variants, reality translation, and Tone down.
- `COMMENTER_MODEL`: simulated audience commenters.
- `RENDER_API_KEY`, `RENDER_WORKFLOW_SLUG`, and `WORKFLOW_EVENT_SECRET`: workflow integration.
- `CORS_ORIGINS`: comma-separated frontend origins.

Never commit `.env` files or API keys.

## Verification

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Before a demo, manually verify both flows:

1. Generate a post and watch variants, finalist comments, scores, ranking, and reality translation arrive.
2. Check the example draft, wait for the score, run Tone down, and compare the original and rewritten drafts.
3. Confirm the UI labels all counts as a simulated audience and that failures offer a retry.

## Deployment shape

Render runs three services:

1. Frontend web service rooted at `frontend/`.
2. FastAPI web service rooted at `backend/`.
3. Render Workflow service rooted at `backend/`.

The API and frontend should use one instance for the demo. The API store is intentionally in-memory, so multiple API instances would not share run state. Set `NEXT_PUBLIC_API_URL` before building the frontend because Next.js public environment variables are baked into the build.

## Submission note

All code in this repository was written during LarpHacks.
