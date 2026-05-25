"use client";

import { useEffect, useState } from "react";

import { getStats, type Stats } from "@/lib/api";

/** Live usage numbers on the landing page; polls every 15s. */
export function HomeStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getStats()
        .then((s) => alive && setStats(s))
        .catch(() => {});
    load();
    const id = setInterval(load, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const fmt = (n?: number) => (n === undefined ? "—" : n.toLocaleString());
  const cells = [
    { label: "sessions total", value: stats?.total_sessions },
    { label: "active sessions", value: stats?.active_sessions, live: true },
    { label: "active agents", value: stats?.active_agents, live: true },
  ];

  return (
    <div className="mt-8 grid grid-cols-3 gap-3 text-center">
      {cells.map((c) => (
        <div
          key={c.label}
          className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900"
        >
          <div className="text-2xl font-semibold tabular-nums">{fmt(c.value)}</div>
          <div className="mt-0.5 flex items-center justify-center gap-1 text-xs text-neutral-500">
            {c.live && <span className="h-1.5 w-1.5 rounded-full bg-green-500" />}
            {c.label}
          </div>
        </div>
      ))}
    </div>
  );
}
