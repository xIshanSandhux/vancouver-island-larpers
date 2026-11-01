"use client";

import Image from "next/image";
import type { TeamMember } from "./team";

/** One person: glowing headshot, name, and a QR to their profile. */
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

      <a
        href={member.url}
        target="_blank"
        rel="noreferrer"
        className="group mt-5 flex flex-col items-center gap-2 rounded-2xl p-2 transition hover:bg-white/5"
      >
        <span className="rounded-xl bg-white p-2 shadow-lg shadow-black/40">
          <Image
            src={member.qr}
            alt={`QR code linking to ${member.name} on LinkedIn`}
            width={200}
            height={200}
            className="h-24 w-24 sm:h-28 sm:w-28"
          />
        </span>
        <span className="font-mono text-xs text-zinc-400 transition group-hover:text-white">
          {member.handle}
        </span>
      </a>
    </figure>
  );
}
