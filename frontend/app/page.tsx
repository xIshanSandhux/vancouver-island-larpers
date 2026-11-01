"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { InputPanel } from "@/components/generate/InputPanel";
import { IntroScene } from "@/components/intro/IntroScene";
import { PostPreview } from "@/components/generate/PostPreview";
import { RealityToggle } from "@/components/generate/RealityToggle";
import { StageTrail } from "@/components/generate/StageTrail";
import { ToneSlider } from "@/components/generate/ToneSlider";
import { RENDER_DASHBOARD_URL } from "@/lib/api";
import { DEFAULT_TONE_WEIGHT, rank } from "@/lib/rank";
import { useRun } from "@/lib/useRun";

/** We open on the title card, run the demo, then come back to it to close. */
type Scene = "intro" | "demo" | "outro";

export default function GeneratePage() {
  const [scene, setScene] = useState<Scene>("intro");
  const [text, setText] = useState("");
  const [demoMode, setDemoMode] = useState(false);
  const [toneWeight, setToneWeight] = useState(DEFAULT_TONE_WEIGHT);
  const { phase, run, error, errorCode, start, reset } = useRun();

  const busy = phase === "starting" || phase === "running";

  const showDemo = useCallback(() => setScene("demo"), []);

  // Space or Enter opens the demo from a title card; Escape closes back to one.
  // Typing in the input must never trigger either.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      const typing = el?.tagName === "INPUT" || el?.tagName === "TEXTAREA";

      if (scene === "demo") {
        if (e.key === "Escape" && !typing) setScene("outro");
        return;
      }
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        setScene("demo");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [scene]);

  // The slider re-orders what we already have; the server's order is the fallback.
  const order = useMemo(() => {
    if (!run) return [];
    if (run.scores.length > 0) return rank(run.scores, toneWeight);
    return run.ranking.length > 0 ? run.ranking : run.finalist_ids;
  }, [run, toneWeight]);

  const variantFor = (postId: string) => run?.variants.find((v) => v.post_id === postId);

  return (
    <>
      {scene !== "demo" && (
        <IntroScene mode={scene === "intro" ? "intro" : "outro"} onStart={showDemo} />
      )}

      {/* The run itself lives in this component's state, so returning to the title
          card and back never loses a run in flight. The key only replays the
          entrance animation each time the demo comes forward. */}
      <main
        key={scene === "demo" ? "demo" : "hidden"}
        className="stage-in mx-auto w-full max-w-2xl flex-1 px-4 py-10"
      >
        <header className="mb-6">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Thought Leadr
          </h1>
          <span className="rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white dark:bg-zinc-100 dark:text-zinc-900">
            Larping as: Thought Leader
          </span>
        </div>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Type something boring. We write 20 versions of you, then test the best three on 50
          simulated commenters.
        </p>
      </header>

      <InputPanel
        text={text}
        onTextChange={setText}
        demoMode={demoMode}
        onDemoModeChange={setDemoMode}
        onSubmit={() => start("generate", text, demoMode)}
        busy={busy}
      />

      {phase === "error" && (
        <section className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/40">
          <p className="text-sm font-medium text-red-900 dark:text-red-200">
            {errorCode === "busy" ? "The demo is busy" : "That did not work"}
          </p>
          <p className="mt-1 text-sm text-red-800 dark:text-red-300">{error}</p>
          <button
            type="button"
            onClick={() => {
              reset();
              void start("generate", text, demoMode);
            }}
            className="mt-3 rounded-lg bg-red-900 px-4 py-1.5 text-xs font-medium text-white hover:bg-red-800"
          >
            Try again
          </button>
        </section>
      )}

      {phase === "starting" && (
        <p className="mt-4 text-sm text-zinc-500">Starting the workflow…</p>
      )}

      {run && (
        <div className="mt-6 space-y-4">
          <StageTrail run={run} />

          {run.scores.length > 1 && <ToneSlider value={toneWeight} onChange={setToneWeight} />}

          {order.map((postId, index) => {
            const variant = variantFor(postId);
            if (!variant) return null;
            const score = run.scores.find((s) => s.post_id === postId);
            const comments = run.comments.filter((c) => c.post_id === postId);
            const isWinner = index === 0;
            return (
              <PostPreview
                key={postId}
                variant={variant}
                score={score}
                comments={comments}
                personaTotal={run.persona_total}
                position={index + 1}
              >
                {isWinner && run.reality && <RealityToggle reality={run.reality} />}
              </PostPreview>
            );
          })}

          {phase === "done" && (
            <p className="pt-2 text-center text-xs text-zinc-400">
              Simulated audience, not a prediction of real engagement.
              {RENDER_DASHBOARD_URL && (
                <>
                  {" · "}
                  <a
                    href={RENDER_DASHBOARD_URL}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-zinc-600"
                  >
                    See the task runs on Render
                  </a>
                </>
              )}
            </p>
          )}
        </div>
      )}
      </main>

      <button
        type="button"
        onClick={() => setScene("outro")}
        title="Back to the title card (Esc)"
        className="fixed bottom-4 right-4 z-40 rounded-full border border-zinc-300 bg-white/90 px-4 py-2 text-xs font-medium text-zinc-700 shadow-lg backdrop-blur transition hover:border-zinc-900 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900/90 dark:text-zinc-300 dark:hover:border-zinc-300 dark:hover:text-zinc-100"
      >
        Team
      </button>
    </>
  );
}
