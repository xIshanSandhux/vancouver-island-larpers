"use client";

import { useState } from "react";
import type { CommentResult } from "@/lib/contracts";
import { previewComments, visibleComments } from "./helpers";

export interface CommentThreadProps {
  comments: CommentResult[];
  streaming?: boolean;
}

export function CommentThread({ comments, streaming = false }: CommentThreadProps) {
  const [expanded, setExpanded] = useState(false);
  const visible = visibleComments(comments);
  const shown = expanded ? visible : previewComments(comments);
  if (visible.length === 0) {
    return <p className="mt-3 text-xs text-zinc-400">{streaming ? "Reactions are arriving; comments may appear next…" : "No comments yet."}</p>;
  }
  return (
    <div>
    <ul className="mt-3 space-y-3" aria-label="Simulated comments" aria-live={streaming ? "polite" : undefined}>
      {shown.map((comment) => (
        <li
          key={comment.event_id}
          className="flex gap-2 opacity-100 motion-safe:animate-[feed-in_450ms_ease-out]"
        >
          <span aria-hidden="true" className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-teal-100 text-xs font-semibold text-teal-900 dark:bg-teal-950 dark:text-teal-200">{comment.persona_name.slice(0, 1)}</span>
          <div className="min-w-0 flex-1 rounded-xl rounded-tl-none bg-zinc-50 px-3 py-2 dark:bg-zinc-800/60">
          <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100">
            {comment.persona_name}{" "}
            <span className="font-normal text-zinc-500">· {comment.persona_label}</span>
          </p>
          <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{comment.comment}</p>
          </div>
        </li>
      ))}
    </ul>
    {visible.length > 5 && <button type="button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)} className="mt-3 rounded-lg px-2 py-2 text-xs font-semibold text-teal-800 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-950">{expanded ? "Show fewer comments" : `View all ${visible.length} comments`}</button>}
    </div>
  );
}
