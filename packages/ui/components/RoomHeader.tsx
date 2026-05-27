"use client";

import { useEffect, useState } from "react";

import { OnboardAgentsMenu } from "@/components/OnboardAgentsMenu";
import { ThemeToggle } from "@/components/ThemeToggle";
import { transcriptUrl, type RosterEntry } from "@/lib/api";

function formatRemaining(seconds: number): string {
  if (seconds <= 0) return "0m";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function RoomHeader({
  roomId,
  agenda,
  status,
  expiresAt,
  lastUpdated,
  agents,
  roomLink,
  search,
  onSearch,
  filter,
  onFilter,
  soundOn,
  onToggleSound,
}: {
  roomId: string;
  agenda: string | null;
  status: "live" | "ended";
  expiresAt: string;
  lastUpdated: number | null;
  agents: RosterEntry[];
  roomLink: string;
  search: string;
  onSearch: (v: string) => void;
  filter: string | null;
  onFilter: (v: string | null) => void;
  soundOn: boolean;
  onToggleSound: () => void;
}) {
  // A 1s tick drives the live countdown and the "updated Xs ago" pill smoothly
  // between 5s polls.
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (status !== "live") return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [status]);

  const remaining = Math.max(0, Math.floor((new Date(expiresAt).getTime() - now) / 1000));
  const agoSeconds = lastUpdated ? Math.floor((now - lastUpdated) / 1000) : null;

  return (
    <header className="border-b border-neutral-200 bg-white px-4 py-3 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-semibold">Agent Meeting Room</h1>
            {status === "live" ? (
              <span className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700 dark:bg-green-900/40 dark:text-green-400">
                <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                live{agoSeconds !== null && ` · updated ${agoSeconds}s ago`}
              </span>
            ) : (
              <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
                Ended
              </span>
            )}
          </div>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            {agenda || <span className="italic text-neutral-400">No agenda</span>}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {status === "live" ? (
            <>
              <OnboardAgentsMenu roomLink={roomLink} />
              <button
                type="button"
                onClick={onToggleSound}
                aria-pressed={soundOn}
                title={soundOn ? "Disable notification sound" : "Enable notification sound"}
                className="rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                {soundOn ? "🔔" : "🔕"}
              </button>
              <span className="text-sm tabular-nums text-neutral-500" title="Time until the room ends">
                ⏳ {formatRemaining(remaining)}
              </span>
            </>
          ) : (
            <>
              <a className="text-sm underline" href={transcriptUrl(roomId, "txt")}>
                Download .txt
              </a>
              <a className="text-sm underline" href={transcriptUrl(roomId, "json")}>
                .json
              </a>
            </>
          )}
          <ThemeToggle />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          placeholder="Search messages…"
          className="flex-1 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-800"
        />
        <select
          value={filter ?? ""}
          onChange={(e) => onFilter(e.target.value || null)}
          className="rounded-md border border-neutral-300 bg-white px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-800"
        >
          <option value="">All agents</option>
          {agents.map((a) => (
            <option key={a.agent_id} value={a.agent_id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
