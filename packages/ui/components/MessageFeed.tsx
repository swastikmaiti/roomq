"use client";

import { EmptyState } from "@/components/EmptyState";
import type { SnapshotMessage } from "@/lib/api";

function time(iso: string): string {
  return iso.length >= 19 ? iso.slice(11, 19) : iso;
}

function recipients(msg: SnapshotMessage, names: Record<string, string>): string {
  if (msg.broadcast) return "everyone";
  return msg.to.map((id) => names[id] ?? id).join(", ") || "—";
}

export function MessageFeed({
  messages,
  byId,
  names,
  hovered,
}: {
  messages: SnapshotMessage[];
  byId: Record<string, SnapshotMessage>;
  names: Record<string, string>;
  hovered: string | null;
}) {
  if (messages.length === 0) {
    return <EmptyState title="No messages yet" hint="Agents that join will appear here." />;
  }

  return (
    <div className="flex-1 space-y-3 overflow-y-auto p-4">
      {messages.map((msg) => {
        if (msg.kind === "system") {
          return (
            <div key={msg.msg_id} className="text-center text-xs italic text-neutral-500">
              🛈 {msg.content} <span className="not-italic">· {time(msg.sent_at)}</span>
            </div>
          );
        }

        const reply = msg.in_reply_to ? byId[msg.in_reply_to] : null;
        const highlighted = hovered && msg.from_agent_id === hovered;

        return (
          <div
            key={msg.msg_id}
            className={`rounded-lg border p-3 text-sm transition-colors ${
              highlighted
                ? "border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30"
                : "border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
            }`}
          >
            <div className="mb-1 flex flex-wrap items-center gap-x-2 text-xs text-neutral-500">
              <span className="font-medium text-neutral-700 dark:text-neutral-300">
                {msg.from_name}
              </span>
              <span>→ {recipients(msg, names)}</span>
              {msg.broadcast && (
                <span className="rounded bg-neutral-200 px-1 dark:bg-neutral-700">broadcast</span>
              )}
              <span className="ml-auto tabular-nums">{time(msg.sent_at)}</span>
            </div>

            {msg.in_reply_to && (
              <div className="mb-1 border-l-2 border-neutral-300 pl-2 text-xs text-neutral-500 dark:border-neutral-700">
                ↳ {reply ? `${reply.from_name}: ${reply.content.slice(0, 60)}` : "earlier message"}
              </div>
            )}

            <p className="whitespace-pre-wrap break-words">{msg.content}</p>

            {msg.read_by.length > 0 && (
              <div
                className="mt-1 text-xs text-neutral-400"
                title={msg.read_by.map((id) => names[id] ?? id).join(", ")}
              >
                ✓ read by {msg.read_by.length}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
