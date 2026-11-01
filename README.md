# Thought Leadr

LARP as a thought leader. Type something boring, get LinkedIn-style posts, and test them on a simulated audience of 50 fictional commenters. Built at LarpHacks for the Render sub-track (Render Workflows).

- What it does and why: [requirements.md](requirements.md)
- How it is built: [architecture.md](architecture.md)
- Who builds what, and rules for AI agents: [agents.md](agents.md)

## Layout

| Folder | What | Deploys as |
|---|---|---|
| `frontend/` | Next.js (TypeScript, Tailwind) UI | Render web service |
| `backend/app/` | FastAPI API: runs, event intake, Render trigger | Render web service |
| `backend/workflows/` | Render Workflow tasks (Python) | Render Workflow service |
| `data/` | personas, voices, lexicon, sample JSON | read by backend |

## Run locally

```bash
# backend (Python 3.11+)
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in keys
uvicorn app.main:app --reload --port 8000
pytest -q

# frontend (Node 20+)
cd frontend
npm install
cp .env.example .env.local
npm run dev                 # http://localhost:3000
npm run lint && npm run typecheck && npm test
```

Open http://localhost:3000. The page shows whether it can reach the backend at `/health`.

## Branches

Branch from `main`, one branch per task card in `agents.md` (`mahir/<name>`, `ishan/<name>`), and open small PRs back into `main`.

## Submission note

All code in this repository was written during LarpHacks.
