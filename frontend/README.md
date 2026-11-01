# Thought Leadr frontend

The frontend is a Next.js app for the Thought Leadr Generate and Check demo.

## Local setup

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open <http://localhost:3000>. The backend should be running at
`NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`). Set
`NEXT_PUBLIC_USE_SAMPLES=true` when working on the UI without a backend.

## Checks

```powershell
npm run lint
npm run typecheck
npm test
npm run build
```

`NEXT_PUBLIC_RENDER_DASHBOARD_URL` is optional. When set, the app includes a
link to the workflow dashboard.
