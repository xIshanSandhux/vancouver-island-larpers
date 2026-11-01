"use client";

// Polls one run until it finishes. Comments arrive as the workflow posts them, so the
// feed fills in during the run rather than appearing all at once at the end.
import { useCallback, useEffect, useRef, useState } from "react";
import { RunRequestError, getRun, startRun } from "./api";
import type { RunMode, RunState } from "./contracts";

const POLL_MS = 1000;
const TIMEOUT_MS = 120_000;

export type RunPhase = "idle" | "starting" | "running" | "done" | "error";

export interface UseRun {
  phase: RunPhase;
  run: RunState | null;
  error: string | null;
  errorCode: string | null;
  start: (mode: RunMode, text: string, demoFail: boolean) => Promise<void>;
  reset: () => void;
}

export function useRun(): UseRun {
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [run, setRun] = useState<RunState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);

  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelled = useRef(false);

  const stop = useCallback(() => {
    cancelled.current = true;
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);

  useEffect(() => stop, [stop]);

  const reset = useCallback(() => {
    stop();
    cancelled.current = false;
    setPhase("idle");
    setRun(null);
    setError(null);
    setErrorCode(null);
  }, [stop]);

  const start = useCallback(
    async (mode: RunMode, text: string, demoFail: boolean) => {
      stop();
      cancelled.current = false;
      setRun(null);
      setError(null);
      setErrorCode(null);
      setPhase("starting");

      let runId: string;
      try {
        runId = await startRun(mode, text, demoFail);
      } catch (err) {
        const known = err instanceof RunRequestError;
        setError(known ? err.message : "Could not reach the server.");
        setErrorCode(known ? err.code : "internal");
        setPhase("error");
        return;
      }

      setPhase("running");
      const deadline = Date.now() + TIMEOUT_MS;

      const poll = async () => {
        if (cancelled.current) return;
        try {
          const state = await getRun(runId);
          if (cancelled.current) return;
          setRun(state);

          if (state.status === "completed") return setPhase("done");
          if (state.status === "failed") {
            setError(state.error ?? "The run failed.");
            setErrorCode("internal");
            return setPhase("error");
          }
          if (Date.now() > deadline) {
            setError("This run took too long. Try again.");
            setErrorCode("internal");
            return setPhase("error");
          }
          timer.current = setTimeout(poll, POLL_MS);
        } catch {
          // A single failed poll is usually a blip; keep trying until the deadline.
          if (cancelled.current) return;
          if (Date.now() > deadline) {
            setError("Lost contact with the server.");
            setErrorCode("internal");
            return setPhase("error");
          }
          timer.current = setTimeout(poll, POLL_MS);
        }
      };

      void poll();
    },
    [stop],
  );

  return { phase, run, error, errorCode, start, reset };
}
