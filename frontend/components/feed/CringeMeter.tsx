import type { CringeResult } from "@/lib/contracts";
import { scoreTone, scoreWidth } from "./helpers";

export interface CringeMeterProps {
  cringe: CringeResult;
}

export function CringeMeter({ cringe }: CringeMeterProps) {
  const width = scoreWidth(cringe);
  return (
    <section className="mt-4" aria-label={`Cringe score ${width} out of 100`}>
      <div className="flex items-baseline justify-between gap-3 text-xs">
        <span className={`font-semibold ${scoreTone(width)}`}>Cringe score {width}/100</span>
        <span className="text-zinc-500">
          Wording {Math.round(cringe.rule_score)} · audience flags {cringe.llm_score === null ? "—" : `${Math.round(cringe.llm_score)}%`}
        </span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
        <div className="h-full bg-amber-500 transition-[width] duration-500" style={{ width: `${width}%` }} />
      </div>
      <details className="mt-2 text-xs text-zinc-500">
        <summary className="cursor-pointer">Why this score?</summary>
        <p className="mt-2">60% wording signals + 40% of the simulated audience flagging cringe. These signals describe phrasing, not your sincerity.</p>
      {cringe.reasons.length > 0 && (
        <ul className="mt-2 space-y-1 text-xs text-zinc-500">
          {cringe.reasons.slice(0, 5).map((reason) => (
            <li key={reason.id}>
              {reason.label} <span className="text-zinc-400">+{reason.points}</span>
            </li>
          ))}
        </ul>
      )}
      </details>
    </section>
  );
}
