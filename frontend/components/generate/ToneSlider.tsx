"use client";

/** Re-ranks in the browser (lib/rank.ts). No model call, so it is instant and repeatable. */
export function ToneSlider({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-baseline justify-between">
        <label htmlFor="tone" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          How much should cringe count against a post?
        </label>
        <span className="text-xs tabular-nums text-zinc-500">{value.toFixed(2)}</span>
      </div>
      <input
        id="tone"
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-zinc-900 dark:accent-zinc-100"
      />
      <div className="flex justify-between text-xs text-zinc-500">
        <span>Let it rip</span>
        <span>Keep me employable</span>
      </div>
    </div>
  );
}
