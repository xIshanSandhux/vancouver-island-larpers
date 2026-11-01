import type { CommentResult } from "@/lib/contracts";
import { visibleComments } from "./helpers";

export interface CommentThreadProps {
  comments: CommentResult[];
  streaming?: boolean;
}

export function CommentThread({ comments, streaming = false }: CommentThreadProps) {
  const visible = visibleComments(comments);
  if (visible.length === 0) {
    return <p className="mt-3 text-xs text-zinc-400">{streaming ? "Audience reactions are arriving…" : "No comments yet."}</p>;
  }
  return (
    <ul className="mt-3 space-y-2" aria-live={streaming ? "polite" : undefined}>
      {visible.map((comment) => (
        <li
          key={comment.event_id}
          className="rounded-lg bg-zinc-50 p-3 opacity-100 motion-safe:animate-[feed-in_450ms_ease-out] dark:bg-zinc-800/50"
        >
          <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100">
            {comment.persona_name}{" "}
            <span className="font-normal text-zinc-500">· {comment.persona_label}</span>
          </p>
          <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{comment.comment}</p>
        </li>
      ))}
    </ul>
  );
}
