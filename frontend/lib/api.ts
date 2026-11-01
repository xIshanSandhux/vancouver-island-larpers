// Calls to the FastAPI backend. Set NEXT_PUBLIC_API_URL in .env.local or on Render.
//
// NEXT_PUBLIC_* is baked in at build time, so changing it on Render needs a rebuild.
import { ApiError, RunState, type RunMode } from "./contracts";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const RENDER_DASHBOARD_URL = process.env.NEXT_PUBLIC_RENDER_DASHBOARD_URL ?? "";

/** An error the UI can show as-is, rather than a stack trace. */
export class RunRequestError extends Error {
  readonly code: string;
  constructor(message: string, code: string) {
    super(message);
    this.code = code;
  }
}

export async function readError(res: Response): Promise<RunRequestError> {
  try {
    const parsed = ApiError.safeParse(await res.json());
    if (parsed.success) return new RunRequestError(parsed.data.error, parsed.data.code);
  } catch {
    // fall through to the generic message
  }
  return new RunRequestError(
    res.status === 429 ? "The demo is busy. Try again in a few seconds." : "Something went wrong.",
    "internal",
  );
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend health check failed: ${res.status}`);
  return res.json();
}

export async function startRun(mode: RunMode, text: string, demoFail: boolean): Promise<string> {
  const res = await fetch(`${API_URL}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, text, demo_fail: demoFail }),
  });
  if (!res.ok) throw await readError(res);
  return (await res.json()).run_id as string;
}

export async function getRun(runId: string): Promise<RunState> {
  const res = await fetch(`${API_URL}/api/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) throw await readError(res);
  return RunState.parse(await res.json());
}

export async function startToneDown(runId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/runs/${runId}/tone-down`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw await readError(res);
}
