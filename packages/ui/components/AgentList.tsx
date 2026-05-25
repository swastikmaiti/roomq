"use client";

import type { RosterEntry } from "@/lib/api";

function Chips({ items, kind }: { items: string[]; kind: "skill" | "capability" }) {
  const color =
    kind === "skill"
      ? "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300"
      : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300";
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {items.map((item) => (
        <span key={item} title={kind} className={`rounded px-1.5 py-0.5 text-[10px] ${color}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

/**
 * Left column: every agent (active + left) with its self-advertised details —
 * name, id, description, skills, capabilities — plus a message-count badge.
 * Hovering highlights that agent's messages; clicking toggles the agent filter.
 */
export function AgentList({
  agents,
  counts,
  hovered,
  onHover,
  filter,
  onFilter,
}: {
  agents: RosterEntry[];
  counts: Record<string, number>;
  hovered: string | null;
  onHover: (id: string | null) => void;
  filter: string | null;
  onFilter: (id: string | null) => void;
}) {
  return (
    <aside className="w-1/4 min-w-[220px] overflow-y-auto border-r border-neutral-200 p-3 dark:border-neutral-800">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        Agents ({agents.length})
      </h2>
      <ul className="space-y-1.5">
        {agents.map((a) => {
          const selected = filter === a.agent_id;
          return (
            <li key={a.agent_id}>
              <button
                onMouseEnter={() => onHover(a.agent_id)}
                onMouseLeave={() => onHover(null)}
                onClick={() => onFilter(selected ? null : a.agent_id)}
                className={`w-full rounded-md border p-2 text-left transition-colors ${
                  selected
                    ? "border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30"
                    : "border-transparent hover:bg-neutral-100 dark:hover:bg-neutral-800/60"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex min-w-0 items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                        a.status === "active" ? "bg-green-500" : "bg-neutral-400"
                      }`}
                    />
                    <span
                      className={`truncate text-sm font-medium ${
                        a.status === "left" ? "text-neutral-400" : ""
                      }`}
                    >
                      {a.name}
                    </span>
                    {a.status === "left" && (
                      <span className="shrink-0 text-[10px] text-neutral-400">(left)</span>
                    )}
                  </span>
                  <span className="ml-2 shrink-0 rounded-full bg-neutral-200 px-1.5 text-xs text-neutral-600 dark:bg-neutral-700 dark:text-neutral-300">
                    {counts[a.agent_id] ?? 0}
                  </span>
                </div>

                <div className="mt-0.5 truncate font-mono text-[10px] text-neutral-400">
                  {a.agent_id}
                </div>

                {a.description && (
                  <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">
                    {a.description}
                  </p>
                )}

                {a.skills && a.skills.length > 0 && <Chips items={a.skills} kind="skill" />}
                {a.capabilities && a.capabilities.length > 0 && (
                  <Chips items={a.capabilities} kind="capability" />
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
