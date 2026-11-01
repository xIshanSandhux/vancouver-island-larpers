"use client";

import Image from "next/image";
import type { TeamMember } from "./team";

/** One person: glowing headshot, name, and role. */
export function TeamCard({ member, delayMs }: { member: TeamMember; delayMs: number }) {
  return (
    <figure
      className="rise-in flex flex-col items-center text-center"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="relative h-40 w-40 sm:h-48 sm:w-48">
        {/* Soft bloom, then the spinning ring, then the photo on top. */}
        <span
          aria-hidden
          className="glow-ring absolute -inset-5 rounded-full opacity-60 blur-2xl"
          style={{ background: member.ring }}
        />
        <span
          aria-hidden
          className="glow-ring absolute -inset-1 rounded-full"
          style={{ background: member.ring }}
        />
        <Image
          src={member.photo}
          alt={member.name}
          width={400}
          height={400}
          priority
          className="absolute inset-0 h-full w-full rounded-full border-4 border-[#06060a] object-cover"
        />
      </div>

      <figcaption className="mt-6">
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          {member.name}
        </h2>
        <p className="mt-2 text-base font-bold text-zinc-200 sm:text-lg">{member.role}</p>
      </figcaption>

      <p className="mt-5 font-mono text-xs text-zinc-500">Thought Leadr team</p>
    </figure>
  );
}
