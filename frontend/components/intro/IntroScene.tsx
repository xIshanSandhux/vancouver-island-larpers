"use client";

import { TeamCard } from "./TeamCard";
import { TEAM } from "./team";

interface Props {
  /** "intro" opens the demo, "outro" closes it. Same scene, different words. */
  mode: "intro" | "outro";
  onStart: () => void;
}

/**
 * The full-screen title card we present from, before and after the live demo.
 * Deliberately always dark, whatever the system theme: it is a stage, not a page.
 */
export function IntroScene({ mode, onStart }: Props) {
  const isIntro = mode === "intro";

  return (
    <section
      onClick={onStart}
      className="scene-fade-in fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center overflow-hidden bg-[#06060a] px-6"
    >
      {/* Slow-drifting colour fields. Purely decorative. */}
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <span className="aurora absolute -left-32 top-0 h-[32rem] w-[32rem] rounded-full bg-sky-500/20 blur-[110px]" />
        <span
          className="aurora absolute -right-24 top-16 h-[30rem] w-[30rem] rounded-full bg-fuchsia-500/20 blur-[110px]"
          style={{ animationDelay: "-6s" }}
        />
        <span
          className="aurora absolute bottom-[-10rem] left-1/3 h-[28rem] w-[28rem] rounded-full bg-emerald-400/15 blur-[110px]"
          style={{ animationDelay: "-12s" }}
        />
      </div>

      <div className="relative z-10 flex w-full max-w-5xl flex-col items-center">
        <header className="rise-in flex flex-col items-center text-center">
          <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-zinc-300">
            {isIntro ? "LarpHacks" : "Thanks for watching"}
          </span>
          <h1 className="mt-4 bg-gradient-to-r from-white via-sky-200 to-fuchsia-200 bg-clip-text text-5xl font-semibold tracking-tight text-transparent sm:text-7xl">
            Thought Leadr
          </h1>
          <p className="mt-3 max-w-xl text-base text-zinc-400 sm:text-lg">
            {isIntro
              ? "Type something boring. We make you insufferable, then test it on 50 people who do not exist."
              : "LARP as a thought leader, or find out you already are."}
          </p>
        </header>

        <div className="mt-12 flex flex-col items-center gap-12 sm:flex-row sm:gap-20">
          {TEAM.map((member, i) => (
            <TeamCard key={member.name} member={member} delayMs={220 + i * 160} />
          ))}
        </div>

        <footer
          className="rise-in mt-14 flex flex-col items-center gap-3"
          style={{ animationDelay: "620ms" }}
        >
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onStart();
            }}
            className="rounded-full bg-white px-7 py-3 text-sm font-semibold text-zinc-900 shadow-lg shadow-black/30 transition hover:scale-[1.03] hover:bg-zinc-100 active:scale-100"
          >
            {isIntro ? "Start the demo" : "Back to the demo"}
          </button>
          <p className="hint-pulse text-xs text-zinc-500">
            Press{" "}
            <kbd className="rounded border border-white/20 bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300">
              space
            </kbd>{" "}
            or click anywhere
          </p>
        </footer>
      </div>
    </section>
  );
}
