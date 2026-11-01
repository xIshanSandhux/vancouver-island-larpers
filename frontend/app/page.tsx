"use client";

import { useEffect, useState } from "react";
import { API_URL, getHealth } from "@/lib/api";

// Template home page. Replace with the Generate page (task M6).
export default function Home() {
  const [backend, setBackend] = useState<"checking" | "ok" | "down">("checking");

  useEffect(() => {
    getHealth()
      .then(() => setBackend("ok"))
      .catch(() => setBackend("down"));
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-4 px-4 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">Thought Leadr</h1>
      <p className="text-zinc-600">Template page. The real UI is built on feature branches.</p>
      <p className="font-mono text-sm">
        backend ({API_URL}): {backend}
      </p>
    </main>
  );
}
