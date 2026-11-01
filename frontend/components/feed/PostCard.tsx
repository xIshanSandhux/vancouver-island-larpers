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
  children?: React.ReactNode;
}

export function PostCard({
  variant,
  score,
  comments,
  personaTotal,
  position = 1,
  streaming = false,
  children,
}: PostCardProps) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900">
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
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-200">
            Simulated finalist
          </span>
        )}
      </header>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">{variant.text}</p>
      {score && <CringeMeter cringe={score.cringe} />}
      <ReactionsBar comments={comments} total={personaTotal} />
      <CommentThread comments={comments} streaming={streaming} />
      {children}
    </article>
  );
}
