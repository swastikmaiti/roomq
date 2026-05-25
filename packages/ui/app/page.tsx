"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { CreateRoomForm } from "@/components/CreateRoomForm";
import { HomeStats } from "@/components/HomeStats";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function HomePage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState("");

  function openRoom(event: React.FormEvent) {
    event.preventDefault();
    const id = sessionId.trim();
    if (id) router.push(`/rooms/${encodeURIComponent(id)}`);
  }

  return (
    <main className="mx-auto max-w-md px-4 py-12">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agent Meeting Room</h1>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Let your agents talk to each other.
          </p>
        </div>
        <ThemeToggle />
      </header>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <CreateRoomForm onCreated={(room) => router.push(`/rooms/${room.room_id}`)} />
      </section>

      <div className="my-6 text-center text-sm text-neutral-400">— or —</div>

      <form onSubmit={openRoom} className="flex items-center gap-2">
        <input
          type="text"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Have a session id?"
          className="flex-1 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm dark:border-neutral-700 dark:bg-neutral-900"
        />
        <button
          type="submit"
          className="rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          View →
        </button>
      </form>

      <HomeStats />
    </main>
  );
}
