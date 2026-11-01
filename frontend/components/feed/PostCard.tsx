import type { CommentResult, PostScore, Variant } from "@/lib/contracts";
import { CommentThread } from "./CommentThread";
import { CringeMeter } from "./CringeMeter";
import { ReactionsBar } from "./ReactionsBar";

export interface PostCardProps {
  variant: Variant;
  score?: PostScore;
  comments: CommentResult[];
  personaTotal: number;
  position?: number;
  streaming?: boolean;
  ranked?: boolean;
  children?: React.ReactNode;
}

export function PostCard({
  variant,
  score,
  comments,
  personaTotal,
  position,
  streaming = false,
  ranked = false,
  children,
}: PostCardProps) {
  return (
    <article className={`overflow-hidden rounded-xl border bg-white p-5 shadow-sm dark:bg-zinc-900 ${ranked && position === 1 ? "border-teal-600 ring-1 ring-teal-600/20" : "border-zinc-200 dark:border-zinc-800"}`}>
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span aria-hidden="true" className="flex h-11 w-11 items-center justify-center rounded-full bg-amber-100 text-base font-semibold text-amber-900">
            Y
          </span>
          <div>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">You, allegedly</p>
            <p className="text-xs text-zinc-500">{variant.voice_label} · Fictional professional feed</p>
          </div>
        </div>
        {position !== undefined && (
          <span className={`shrink-0 rounded-full px-2 py-1 text-xs font-medium ${ranked && position === 1 ? "bg-teal-50 text-teal-900 dark:bg-teal-950 dark:text-teal-200" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"}`}>
            {ranked ? position === 1 ? "#1 · Simulated winner" : `#${position} · Finalist` : "Awaiting final ranking"}
          </span>
        )}
      </header>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">{variant.text}</p>
      {children}
      {score && <CringeMeter cringe={score.cringe} />}
      {score && <details className="mt-3 text-xs text-zinc-500"><summary className="cursor-pointer">How this post ranks</summary><p className="mt-2">Engagement: {Math.round(score.engagement_rate * 100)}% · Average appeal: {score.appeal_mean.toFixed(1)}/5. Ranking balances engagement and appeal, then subtracts the tone slider’s cringe penalty. Critical comments count as engagement too.</p></details>}
      <ReactionsBar comments={comments} total={personaTotal} />
      <CommentThread comments={comments} streaming={streaming} />
    </article>
  );
}
