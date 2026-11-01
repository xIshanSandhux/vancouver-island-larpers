"use client";

// Minimal post, reactions and comment rendering.
// PLACEHOLDER: Ishan's components/feed/ (task I5) replaces these with the polished
// versions. The shapes come from lib/contracts.ts, so swapping them in is a prop change.
import type { CommentResult, CringeResult, PostScore, Variant } from "@/lib/contracts";

export function CringeBar({ cringe }: { cringe: CringeResult }) {
  const score = Math.round(cringe.score);
  const tone = score > 66 ? "bg-red-500" : score > 33 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="mt-3">
      <div className="flex items-baseline justify-between text-xs">
        <span className="font-medium text-zinc-700 dark:text-zinc-300">Cringe {score}/100</span>
        {cringe.reasons.length > 0 && (
          <span className="text-zinc-500">{cringe.reasons.map((r) => r.label).join(" · ")}</span>
        )}
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
        <div className={`h-full ${tone}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

export function ReactionsBar({ comments, total }: { comments: CommentResult[]; total: number }) {
  const likes = comments.filter((c) => c.action === "like").length;
  const replies = comments.filter((c) => c.action === "comment").length;
  const ignored = comments.filter((c) => c.action === "ignore").length;
  return (
    <p className="mt-3 border-t border-zinc-100 pt-2 text-xs text-zinc-500 dark:border-zinc-800">
      <span className="tabular-nums">{likes}</span> likes ·{" "}
      <span className="tabular-nums">{replies}</span> comments ·{" "}
      <span className="tabular-nums">{ignored}</span> scrolled past
      <span className="ml-2 text-zinc-400">(simulated audience of {total})</span>
    </p>
  );
}

export function CommentThread({ comments }: { comments: CommentResult[] }) {
  const withText = comments.filter((c) => c.action === "comment" && c.comment);
  if (withText.length === 0) {
    return <p className="mt-3 text-xs text-zinc-400">No comments yet…</p>;
  }
  return (
    <ul className="mt-3 space-y-2">
      {withText.map((c) => (
        <li key={c.event_id} className="rounded-lg bg-zinc-50 p-2 text-sm dark:bg-zinc-800/50">
          <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100">
            {c.persona_name} <span className="font-normal text-zinc-500">· {c.persona_label}</span>
          </p>
          <p className="text-zinc-700 dark:text-zinc-300">{c.comment}</p>
        </li>
      ))}
    </ul>
  );
}

interface PostPreviewProps {
  variant: Variant;
  score?: PostScore;
  comments: CommentResult[];
  personaTotal: number;
  position: number;
  children?: React.ReactNode;
}

export function PostPreview({ variant, score, comments, personaTotal, position, children }: PostPreviewProps) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
            {position}
          </span>
          <div>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">You, allegedly</p>
            <p className="text-xs text-zinc-500">{variant.voice_label}</p>
          </div>
        </div>
        {position === 1 && (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
            Winner
          </span>
        )}
      </header>

      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
        {variant.text}
      </p>

      {score && <CringeBar cringe={score.cringe} />}
      <ReactionsBar comments={comments} total={personaTotal} />
      <CommentThread comments={comments} />
      {children}
    </article>
  );
}
