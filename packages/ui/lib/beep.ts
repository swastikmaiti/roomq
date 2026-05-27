"use client";

/**
 * Tiny notification ping using the Web Audio API — no audio asset needed.
 *
 * Browsers block audio until the user has interacted with the page, and an
 * AudioContext created outside a gesture starts suspended. So we expose
 * primeAudio() which the caller invokes inside a click handler (e.g. the
 * "enable sound" toggle) — that creates/resumes the context while we still
 * have the gesture. playBeep() is then safe to call from anywhere.
 */

let ctx: AudioContext | null = null;

function getAudioCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (ctx) return ctx;
  const Ctor =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext })
      .webkitAudioContext;
  if (!Ctor) return null;
  ctx = new Ctor();
  return ctx;
}

export function primeAudio(): void {
  const c = getAudioCtx();
  if (c && c.state === "suspended") void c.resume();
}

export function playBeep(): void {
  const c = ctx;
  if (!c) return;
  const t = c.currentTime;
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = "sine";
  osc.frequency.value = 880;
  gain.gain.setValueAtTime(0.0001, t);
  gain.gain.exponentialRampToValueAtTime(0.15, t + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.25);
  osc.connect(gain).connect(c.destination);
  osc.start(t);
  osc.stop(t + 0.3);
}
