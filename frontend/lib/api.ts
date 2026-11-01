// Base URL of the FastAPI backend. Set NEXT_PUBLIC_API_URL in .env.local (local) or Render (deployed).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend health check failed: ${res.status}`);
  return res.json();
}
