import type { RunState } from "./contracts";

export function inputError(text: string, maxChars: number): string | null {
  if (text.trim().length === 0) return "Add a draft before checking it.";
  if (text.length > maxChars) return `Keep the draft under ${maxChars.toLocaleString()} characters.`;
  return null;
}

export function runErrorTitle(code: string | null): string {
  if (code === "busy") return "The demo is busy";
  if (code === "invalid_input") return "Check the text and try again";
  if (code === "render_unavailable" || code === "backend_down") return "The workflow service is unavailable";
  if (code === "timeout") return "The workflow took too long";
  return "That did not work";
}

export function rewritePollDecision(
  state: RunState,
  now: number,
  deadline: number,
): "ready" | "failed" | "timeout" | "pending" {
  if (state.rewrite) return "ready";
  if (state.rewrite_error || state.status === "failed") return "failed";
  if (now >= deadline) return "timeout";
  return "pending";
}
