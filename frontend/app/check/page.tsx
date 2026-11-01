"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PostCard } from "@/components/feed";
import { FeedShell } from "@/components/feed/FeedShell";
import { getRun, RunRequestError, startToneDown } from "@/lib/api";
import { CHECK_MAX_CHARS, type RunState } from "@/lib/contracts";
import { useRun } from "@/lib/useRun";
import { inputError, rewritePollDecision, runErrorTitle } from "@/lib/ui";

const EXAMPLE_DRAFT =
  "I used to think consistency was boring. Then I started showing up every week, listening to customers, and making one small improvement at a time. The results were quieter than a breakthrough, but they lasted longer.";

export default function CheckPage() {
  const [text, setText] = useState("");
  const [rewriteRun, setRewriteRun] = useState<RunState | null>(null);
  const [rewritePending, setRewritePending] = useState(false);
  const [rewriteError, setRewriteError] = useState<string | null>(null);
  const { phase, run, error, errorCode, start, reset } = useRun();

  const displayRun = rewriteRun ?? run;
  const score = displayRun?.scores.find((item) => item.post_id === "draft");
  const comments = displayRun?.comments.filter((item) => item.post_id === "draft") ?? [];
  const variant = useMemo(
    () => displayRun?.variants.find((item) => item.post_id === "draft") ?? {
      post_id: "draft",
      voice_id: "user",
      voice_label: "Your draft",
      text: displayRun?.input_text ?? text,
    },
    [displayRun, text],
  );
  const busy = phase === "starting" || phase === "running" || rewritePending;
  const validationMessage = inputError(text, CHECK_MAX_CHARS);

  useEffect(() => {
    if (!rewritePending || !run) return;
    let cancelled = false;
    const deadline = Date.now() + 120_000;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const pollRewrite = async () => {
      try {
        const state = await getRun(run.run_id);
        if (cancelled) return;
        setRewriteRun(state);
        const decision = rewritePollDecision(state, Date.now(), deadline);
        if (decision === "ready") {
          setRewritePending(false);
          setRewriteError(null);
          return;
        }
        if (decision === "failed") {
          setRewritePending(false);
          setRewriteError(state.rewrite_error ?? state.error ?? "Tone down failed. The original draft is unchanged.");
          return;
        }
        if (decision === "timeout") {
          setRewritePending(false);
          setRewriteError("The rewrite took too long. The original draft is unchanged; try again.");
          return;
        }
        timer = setTimeout(() => void pollRewrite(), 1000);
      } catch {
        if (cancelled) return;
        if (Date.now() >= deadline) {
          setRewritePending(false);
          setRewriteError("Lost contact with the server while waiting for the rewrite.");
          return;
        }
        timer = setTimeout(() => void pollRewrite(), 1000);
      }
    };

    void pollRewrite();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [rewritePending, run]);

  const submit = () => {
    if (validationMessage) return;
    setRewriteRun(null);
    setRewriteError(null);
    void start("check", text, false);
  };

  const requestToneDown = async () => {
    if (!run || !score || rewritePending) return;
    setRewriteError(null);
    setRewritePending(true);
    try {
      await startToneDown(run.run_id);
    } catch (caught) {
      setRewritePending(false);
      setRewriteError(caught instanceof RunRequestError ? caught.message : "Could not start tone down.");
    }
  };

  return (
    <FeedShell mode="check" run={displayRun}>
      <header className="mb-6">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Check a draft</h1>
          <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-200">
            Larping as: someone with a good post
          </span>
        </div>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Get a simulated audience read on your draft before you publish it.
        </p>
      </header>

      <label htmlFor="draft" className="text-sm font-medium text-zinc-800 dark:text-zinc-200">Your draft</label>
      <textarea
        id="draft"
        value={text}
        maxLength={CHECK_MAX_CHARS}
        aria-describedby="draft-hint"
        aria-invalid={Boolean(validationMessage)}
        onChange={(event) => setText(event.target.value)}
        disabled={busy}
        rows={10}
        className="mt-2 w-full resize-y rounded-xl border border-zinc-300 bg-white p-3 text-sm leading-relaxed outline-none ring-amber-500 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-900"
        placeholder="Paste the draft you want the audience to check…"
      />
      <div className="mt-1 flex items-center justify-between text-xs text-zinc-500">
        <span>{text.length}/{CHECK_MAX_CHARS} characters</span>
        <button type="button" onClick={() => setText(EXAMPLE_DRAFT)} disabled={busy} className="underline underline-offset-2">
          Try an example
        </button>
      </div>
      <p id="draft-hint" className={`mt-2 text-xs ${validationMessage ? "text-amber-700 dark:text-amber-300" : "text-zinc-500"}`}>
        {validationMessage ?? "Paste a real draft and the simulated audience will explain how it reads."}
      </p>
      <button
        type="button"
        onClick={submit}
        disabled={busy || text.trim().length === 0}
        className="mt-4 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
      >
        Check post
      </button>

      {(phase === "error" || phase === "timeout") && (
        <section className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/40">
          <p className="text-sm font-medium text-red-900 dark:text-red-200">{runErrorTitle(errorCode)}</p>
          <p className="mt-1 text-sm text-red-800 dark:text-red-300">{error}</p>
          <button type="button" onClick={() => { reset(); submit(); }} className="mt-3 rounded-lg bg-red-900 px-4 py-1.5 text-xs font-medium text-white">Try again</button>
        </section>
      )}
      {phase === "starting" && <p className="mt-4 rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-600 dark:bg-zinc-900 dark:text-zinc-300" role="status">Starting the check…</p>}
      {run && phase === "running" && <p className="mt-4 rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-600 dark:bg-zinc-900 dark:text-zinc-300" role="status">{run.status === "queued" ? "Your check is queued. The audience will join shortly." : run.stage === "commenting" ? "The simulated audience is reacting…" : `Workflow stage: ${run.stage}`}</p>}

      {displayRun && (
        <div className="mt-6 space-y-4">
          <PostCard variant={variant} score={score} comments={comments} personaTotal={displayRun.persona_total} streaming={phase === "running"} />
          {phase === "done" && score && !displayRun.rewrite && (
            <button type="button" onClick={() => void requestToneDown()} disabled={rewritePending} className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-900 disabled:opacity-50 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
              Tone down this draft
            </button>
          )}
          {rewritePending && <p className="text-sm text-zinc-500" role="status">Rewriting the draft while keeping its facts…</p>}
          {rewriteError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">
              <p>{rewriteError}</p>
              {phase === "done" && <button type="button" onClick={() => void requestToneDown()} className="mt-2 font-medium underline underline-offset-2">Try tone down again</button>}
            </div>
          )}
          {displayRun.rewrite && (
            <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
              <h2 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">A more grounded version</h2>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-emerald-950 dark:text-emerald-100">{displayRun.rewrite.text}</p>
              <p className="mt-3 text-xs text-emerald-800 dark:text-emerald-300">Before: {Math.round(displayRun.rewrite.cringe_before)}/100 · After: {Math.round(displayRun.rewrite.cringe_after)}/100</p>
            </section>
          )}
        </div>
      )}

      <Link href="/" className="mt-8 inline-block text-sm text-zinc-600 underline underline-offset-2 dark:text-zinc-400">Back to Generate</Link>
    </FeedShell>
  );
}
