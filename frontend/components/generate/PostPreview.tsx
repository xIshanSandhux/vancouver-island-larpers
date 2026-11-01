"use client";

// Compatibility adapter for the existing Generate page while the shared feed owns rendering.
import type { CommentResult, PostScore, Variant } from "@/lib/contracts";
import { CringeMeter, PostCard, ReactionsBar, CommentThread } from "@/components/feed";

export { CringeMeter, ReactionsBar, CommentThread };

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
    <PostCard
      variant={variant}
      score={score}
      comments={comments}
      personaTotal={personaTotal}
      position={position}
      streaming={comments.length < personaTotal}
    >
      {children}
    </PostCard>
  );
}
