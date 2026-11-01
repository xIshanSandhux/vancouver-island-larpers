import Link from "next/link";
import type { ReactNode } from "react";
import type { RunState } from "@/lib/contracts";
import { RENDER_DASHBOARD_URL } from "@/lib/api";

export function FeedShell({ children, mode, run, status }: {
  children: ReactNode;
  mode: "generate" | "check";
  run?: RunState | null;
  status?: ReactNode;
}) {
  const expected = run ? run.finalist_ids.length * run.persona_total : 0;
  return (
    <div className="min-h-screen bg-[#f3f2ee] text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="sticky top-0 z-30 border-b border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/95">
        <nav aria-label="Main navigation" className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-teal-800 text-sm text-white">tl.</span>
            <span>Thought Leadr</span>
          </Link>
          <div className="flex gap-1 text-sm">
            <Link aria-current={mode === "generate" ? "page" : undefined} className={`rounded-lg px-3 py-2 ${mode === "generate" ? "bg-teal-50 font-semibold text-teal-900 dark:bg-teal-950 dark:text-teal-200" : "text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"}`} href="/">Generate</Link>
            <Link aria-current={mode === "check" ? "page" : undefined} className={`rounded-lg px-3 py-2 ${mode === "check" ? "bg-teal-50 font-semibold text-teal-900 dark:bg-teal-950 dark:text-teal-200" : "text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"}`} href="/check">Check a draft</Link>
          </div>
        </nav>
      </header>
      <div className="mx-auto grid max-w-6xl items-start gap-5 px-4 py-6 lg:grid-cols-[200px_minmax(0,1fr)_260px]">
        <aside aria-label="Your parody profile" className="hidden overflow-hidden rounded-xl border border-zinc-200 bg-white lg:block dark:border-zinc-800 dark:bg-zinc-900">
          <div className="h-16 bg-gradient-to-br from-teal-800 via-teal-600 to-amber-200" />
          <div className="px-4 pb-5">
            <div className="-mt-6 grid h-14 w-14 place-items-center rounded-full border-4 border-white bg-amber-100 text-lg font-semibold text-amber-900 dark:border-zinc-900">Y</div>
            <h2 className="mt-2 font-semibold">You, allegedly</h2>
            <p className="mt-1 text-xs leading-relaxed text-zinc-500">Turning everyday events into unsolicited leadership advice.</p>
            <div className="mt-4 border-t border-zinc-100 pt-3 text-xs dark:border-zinc-800">
              <p className="font-medium text-teal-800 dark:text-teal-300">Larping as: Thought Leader</p>
              <p className="mt-2 text-zinc-500">Fictional profile. Very real main-character energy.</p>
            </div>
          </div>
        </aside>
        <main id="main-content" className="min-w-0 space-y-4">{children}</main>
        <aside aria-label="Audience and workflow" className="space-y-4 lg:sticky lg:top-20">
          <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-semibold uppercase tracking-wider text-teal-800 dark:text-teal-300">The rehearsal room</p>
            <h2 className="mt-2 text-lg font-semibold">50 fictional perspectives.</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">Recruiters, skeptics, founders, lurkers, and the person who always says “Great post.”</p>
            {run && <p className="mt-4 border-t border-zinc-100 pt-3 text-sm tabular-nums dark:border-zinc-800">{run.comments.length} / {expected || (mode === "generate" ? 150 : 50)} reactions received</p>}
            <p className="mt-3 text-xs leading-relaxed text-zinc-500">A simulated audience, not a forecast of real engagement.</p>
          </section>
          {status}
          <section className="rounded-xl border border-zinc-200 bg-white p-4 text-xs leading-relaxed text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Powered by Render Workflows</h2>
            <p className="mt-2">Parallel writing and audience tasks, live progress, and automatic task retries.</p>
            {RENDER_DASHBOARD_URL && <a href={RENDER_DASHBOARD_URL} target="_blank" rel="noreferrer" className="mt-3 inline-block font-medium text-teal-800 underline dark:text-teal-300">See the task runs ↗</a>}
          </section>
        </aside>
      </div>
    </div>
  );
}
