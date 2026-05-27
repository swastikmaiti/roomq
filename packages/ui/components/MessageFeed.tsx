"use client";

import { useEffect, useRef, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import type { SnapshotMessage } from "@/lib/api";

function time(iso: string): string {
  return iso.length >= 19 ? iso.slice(11, 19) : iso;
}

function recipients(msg: SnapshotMessage, names: Record<string, string>): string {
  if (msg.broadcast) return "everyone";
  return msg.to.map((id) => names[id] ?? id).join(", ") || "—";
}

// Within this many px of the bottom, we treat the user as "following" the
// stream. DOM rounding makes exact equality unreliable, so we use a small
// tolerance.
const NEAR_BOTTOM_PX = 60;

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
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoFollow, setAutoFollow] = useState(true);
  const [missed, setMissed] = useState(0);
  const prevLastIdRef = useRef<string | null>(null);
  const hasMountedRef = useRef(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const lastId = messages[messages.length - 1]?.msg_id ?? null;
    const prevLastId = prevLastIdRef.current;
    if (lastId === prevLastId) return;

    if (!hasMountedRef.current && lastId !== null) {
      // First time we have messages — jump to bottom without animation.
      el.scrollTop = el.scrollHeight;
      hasMountedRef.current = true;
      prevLastIdRef.current = lastId;
      return;
    }

    const prevIdx = prevLastId ? messages.findIndex((m) => m.msg_id === prevLastId) : -1;
    if (prevLastId !== null && prevIdx === -1) {
      // List changed non-monotonically (filter/search changed) — reset and
      // pin to bottom of the new view.
      el.scrollTop = el.scrollHeight;
      setAutoFollow(true);
      setMissed(0);
    } else {
      const added = messages.length - 1 - prevIdx;
      if (added > 0) {
        if (autoFollow) {
          el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
        } else {
          setMissed((m) => m + added);
        }
      }
    }
    prevLastIdRef.current = lastId;
  }, [messages, autoFollow]);

  function handleScroll() {
    const el = containerRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX;
    setAutoFollow(nearBottom);
    if (nearBottom) setMissed(0);
  }

  function jumpToBottom() {
    const el = containerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }

  if (messages.length === 0) {
    return <EmptyState title="No messages yet" hint="Agents that join will appear here." />;
  }

  return (
    <div className="relative flex flex-1 flex-col overflow-hidden">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 space-y-3 overflow-y-auto p-4"
      >
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

      {!autoFollow && missed > 0 && (
        <button
          type="button"
          onClick={jumpToBottom}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-3 py-1 text-xs font-medium text-white shadow-lg hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400"
        >
          ↓ {missed} new message{missed > 1 ? "s" : ""}
        </button>
      )}
    </div>
  );
}
