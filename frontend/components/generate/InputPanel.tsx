"use client";

import { GENERATE_MAX_CHARS } from "@/lib/contracts";

const EXAMPLES = [
  "I got a coffee and went to a meeting.",
  "I fixed a typo in the README.",
  "My code review got three comments.",
];

interface Props {
  text: string;
  onTextChange: (value: string) => void;
  demoMode: boolean;
  onDemoModeChange: (value: boolean) => void;
  onSubmit: () => void;
  busy: boolean;
}

export function InputPanel({ text, onTextChange, demoMode, onDemoModeChange, onSubmit, busy }: Props) {
  const tooLong = text.length > GENERATE_MAX_CHARS;
  const canSubmit = text.trim().length > 0 && !tooLong && !busy;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <label htmlFor="event" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        What actually happened?
      </label>
      <textarea
        id="event"
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && canSubmit) onSubmit();
        }}
        rows={3}
        placeholder="I got a coffee and went to a meeting."
        className="mt-2 w-full resize-none rounded-lg border border-zinc-300 bg-white p-3 text-base text-zinc-900 outline-none placeholder:text-zinc-400 focus:border-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:border-zinc-300"
      />

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="text-xs text-zinc-500">Try:</span>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => onTextChange(example)}
            className="rounded-full border border-zinc-300 px-3 py-1 text-xs text-zinc-600 transition hover:border-zinc-900 hover:text-zinc-900 dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-zinc-300 dark:hover:text-zinc-100"
          >
            {example}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400">
            <input
              type="checkbox"
              checked={demoMode}
              onChange={(e) => onDemoModeChange(e.target.checked)}
              className="h-4 w-4 accent-zinc-900 dark:accent-zinc-100"
            />
            Demo mode (simulate one task failure)
          </label>
          <span className={`text-xs tabular-nums ${tooLong ? "text-red-600" : "text-zinc-400"}`}>
            {text.length}/{GENERATE_MAX_CHARS}
          </span>
        </div>

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit}
          className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {busy ? "Larping…" : "Make me a thought leader"}
        </button>
      </div>
    </section>
  );
}
