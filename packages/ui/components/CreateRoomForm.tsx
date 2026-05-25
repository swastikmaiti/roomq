"use client";

import { useState } from "react";

import { createRoom, type CreateRoomResponse } from "@/lib/api";

const DURATIONS = [
  { label: "1 hour", minutes: 60 },
  { label: "2 hours", minutes: 120 },
  { label: "3 hours", minutes: 180 },
  { label: "4 hours", minutes: 240 },
  { label: "5 hours", minutes: 300 },
];

export function CreateRoomForm({
  onCreated,
}: {
  onCreated: (room: CreateRoomResponse) => void;
}) {
  const [minutes, setMinutes] = useState(60);
  const [agenda, setAgenda] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const room = await createRoom({
        active_for_minutes: minutes,
        agenda: agenda.trim() || undefined,
      });
      onCreated(room);
    } catch {
      setError("Could not create the room. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-medium">Create a meeting room</h2>

      <label className="block text-sm">
        <span className="mb-1 block text-neutral-600 dark:text-neutral-400">Active for</span>
        <select
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
          className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
        >
          {DURATIONS.map((d) => (
            <option key={d.minutes} value={d.minutes}>
              {d.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm">
        <span className="mb-1 block text-neutral-600 dark:text-neutral-400">
          Agenda <span className="text-neutral-400">(optional)</span>
        </span>
        <input
          type="text"
          value={agenda}
          maxLength={200}
          onChange={(e) => setAgenda(e.target.value)}
          placeholder="What should the agents work on?"
          className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
        />
      </label>

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-neutral-900 px-4 py-2 font-medium text-white hover:bg-neutral-800 disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-200"
      >
        {submitting ? "Creating…" : "Create room"}
      </button>
    </form>
  );
}
