"use client";

import type { RunState, Stage } from "@/lib/contracts";

const STEPS: { stage: Stage; label: string }[] = [
  { stage: "variants", label: "Writing 20 posts" },
  { stage: "filtering", label: "Picking finalists" },
  { stage: "commenting", label: "50 people reacting" },
  { stage: "ranking", label: "Ranking" },
  { stage: "reality", label: "Checking reality" },
];

/** Shows where the workflow is, so a 20-second run never looks frozen. */
export function StageTrail({ run }: { run: RunState }) {
  const order = STEPS.map((s) => s.stage);
  const current = run.stage === "done" ? STEPS.length : order.indexOf(run.stage);
  const reacted = run.comments.length;
  const expected = Math.max(1, run.finalist_ids.length) * run.persona_total;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <ol className="flex flex-wrap gap-x-4 gap-y-2">
        {STEPS.map((step, i) => {
          const state = i < current ? "done" : i === current ? "active" : "todo";
          return (
            <li
              key={step.stage}
              className={
                state === "done"
                  ? "text-xs text-zinc-400 line-through"
                  : state === "active"
                    ? "text-xs font-medium text-zinc-900 dark:text-zinc-100"
                    : "text-xs text-zinc-400"
              }
            >
              {state === "active" && <span className="mr-1 animate-pulse">●</span>}
              {step.label}
            </li>
          );
        })}
      </ol>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
        {run.stage === "commenting" && (
          <span className="tabular-nums">
            {reacted} of {expected} reactions in
          </span>
        )}
        {run.retries_seen > 0 && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-200">
            Retried {run.retries_seen} task automatically
          </span>
        )}
        {run.demo_fail && (
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            Demo mode: simulated failure
          </span>
        )}
      </div>
    </div>
  );
}
