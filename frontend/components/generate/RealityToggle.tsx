"use client";

import { useState } from "react";
import type { Reality } from "@/lib/contracts";

/** The joke, made explicit: the post next to the sentence it came from. */
export function RealityToggle({ reality }: { reality: Reality }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-4 border-t border-zinc-100 pt-3 dark:border-zinc-800">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:border-zinc-900 hover:text-zinc-900 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-zinc-300 dark:hover:text-zinc-100"
      >
        {open ? "Hide what really happened" : "What really happened?"}
      </button>

      {open && (
        <div className="mt-3 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
          <p className="text-xs uppercase tracking-wide text-zinc-500">You wrote</p>
          <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">{reality.original}</p>
          <p className="mt-3 text-sm italic text-zinc-600 dark:text-zinc-400">{reality.translation}</p>
          {reality.inflations.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {reality.inflations.map((phrase) => (
                <li
                  key={phrase}
                  className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-200"
                >
                  {phrase}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
