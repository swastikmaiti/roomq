"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AgentList } from "@/components/AgentList";
import { EmptyState } from "@/components/EmptyState";
import { MessageFeed } from "@/components/MessageFeed";
import { RoomHeader } from "@/components/RoomHeader";
import type { SnapshotMessage } from "@/lib/api";
import { primeAudio } from "@/lib/beep";
import { useNewMessageBeep } from "@/lib/useNewMessageBeep";
import { useRoomSnapshot } from "@/lib/useRoomSnapshot";

export function RoomView({ roomId }: { roomId: string }) {
  const { snapshot, notFound, lastUpdated } = useRoomSnapshot(roomId);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [soundOn, setSoundOn] = useState(false);

  useNewMessageBeep(snapshot?.messages.length, soundOn);

  const view = useMemo(() => {
    if (!snapshot) return null;
    const names: Record<string, string> = { system: "System" };
    const counts: Record<string, number> = {};
    const byId: Record<string, SnapshotMessage> = {};
    for (const a of snapshot.agents) names[a.agent_id] = a.name;
    for (const m of snapshot.messages) {
      byId[m.msg_id] = m;
      if (m.from_agent_id) counts[m.from_agent_id] = (counts[m.from_agent_id] ?? 0) + 1;
    }
    const q = search.trim().toLowerCase();
    const filtered = snapshot.messages.filter((m) => {
      if (q && !m.content.toLowerCase().includes(q)) return false;
      // Filter = messages the agent is involved in (author, recipient, or broadcast).
      if (filter && !(m.from_agent_id === filter || m.to.includes(filter) || m.broadcast)) {
        return false;
      }
      return true;
    });
    return { names, counts, byId, filtered };
  }, [snapshot, search, filter]);

  if (notFound) {
    return (
      <main className="flex h-screen flex-col items-center justify-center gap-3">
        <EmptyState title="Room not found" hint="Check the session id and try again." />
        <Link href="/" className="text-sm underline">
          ← Back to home
        </Link>
      </main>
    );
  }

  if (!snapshot || !view) {
    return (
      <main className="flex h-screen items-center justify-center">
        <EmptyState title="Loading…" />
      </main>
    );
  }

  return (
    <main className="flex h-screen flex-col">
      <RoomHeader
        roomId={roomId}
        agenda={snapshot.agenda}
        status={snapshot.status}
        expiresAt={snapshot.expires_at}
        lastUpdated={lastUpdated}
        agents={snapshot.agents}
        roomLink={snapshot.room_link}
        search={search}
        onSearch={setSearch}
        filter={filter}
        onFilter={setFilter}
        soundOn={soundOn}
        onToggleSound={() => {
          const next = !soundOn;
          // Toggle-on is the user gesture that unlocks audio in the browser.
          if (next) primeAudio();
          setSoundOn(next);
        }}
      />
      <div className="flex flex-1 overflow-hidden">
        <AgentList
          agents={snapshot.agents}
          counts={view.counts}
          hovered={hovered}
          onHover={setHovered}
          filter={filter}
          onFilter={setFilter}
        />
        <MessageFeed messages={view.filtered} byId={view.byId} names={view.names} hovered={hovered} />
      </div>
    </main>
  );
}
