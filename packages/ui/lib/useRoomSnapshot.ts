"use client";

/**
 * Polls GET /snapshot every ~5s. Stops once the room has ended (after fetching
 * the final state) and on a 404 (unknown session id). Transient errors back off
 * exponentially (5s → 30s) and reset to 5s on the next success.
 */

import { useEffect, useState } from "react";

import { ApiError, getSnapshot, type Snapshot } from "@/lib/api";

const BASE_DELAY = 5000;
const MAX_DELAY = 30000;

export function useRoomSnapshot(roomId: string) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    let delay = BASE_DELAY;

    async function tick() {
      try {
        const data = await getSnapshot(roomId);
        if (!active) return;
        setSnapshot(data);
        setLastUpdated(Date.now());
        delay = BASE_DELAY;
        if (data.status === "ended") return; // room is read-only; stop polling
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
          return;
        }
        delay = Math.min(delay * 2, MAX_DELAY); // transient — back off
      }
      timer = setTimeout(tick, delay);
    }

    tick();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [roomId]);

  return { snapshot, notFound, lastUpdated };
}
