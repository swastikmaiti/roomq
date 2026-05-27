"use client";

import { useEffect, useRef } from "react";

import { playBeep } from "@/lib/beep";

/**
 * Plays a short beep when the message count grows.
 * - First non-null observation seeds the baseline silently (no beep on load).
 * - Beeps only while `enabled` is true.
 * - Toggling off then on does not retroactively beep for missed messages.
 */
export function useNewMessageBeep(
  messageCount: number | undefined,
  enabled: boolean,
): void {
  const prev = useRef<number | null>(null);
  useEffect(() => {
    if (messageCount === undefined) return;
    if (prev.current !== null && enabled && messageCount > prev.current) {
      playBeep();
    }
    prev.current = messageCount;
  }, [messageCount, enabled]);
}
