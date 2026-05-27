"use client";

import { useEffect, useRef, useState } from "react";

import { useToast } from "@/components/ToastProvider";
import { buildPrimaryCurls, buildSecondaryCurls } from "@/lib/curls";
import {
  SECONDARY_ROLE_PRESETS,
  buildPrimaryPrompt,
  buildSecondaryPrompt,
} from "@/lib/prompts";

const CUSTOM = "__custom__";

export function OnboardAgentsMenu({ roomLink }: { roomLink: string }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [roleChoice, setRoleChoice] = useState<string>(SECONDARY_ROLE_PRESETS[0]);
  const [customRole, setCustomRole] = useState<string>("");
  const containerRef = useRef<HTMLDivElement>(null);

  const role = roleChoice === CUSTOM ? customRole : roleChoice;
  const canCopySecondary = role.trim().length > 0;

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function copy(text: string, label: string) {
    await navigator.clipboard.writeText(text);
    toast(`${label} copied`);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        title="Copy role prompts and curl commands for your agents"
        className="rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
      >
        Onboard agents ▾
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-neutral-200 bg-white p-3 shadow-lg dark:border-neutral-800 dark:bg-neutral-900"
        >
          <section className="mb-3">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
              Primary agent
            </h3>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => copy(buildPrimaryPrompt(), "Primary prompt")}
                className="flex-1 rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Copy prompt
              </button>
              <button
                type="button"
                onClick={() => copy(buildPrimaryCurls(roomLink), "Primary curls")}
                className="flex-1 rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Copy curls
              </button>
            </div>
          </section>

          <section className="mb-3">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
              Secondary agent
            </h3>
            <label className="mb-1.5 block text-xs text-neutral-600 dark:text-neutral-400">
              Role
              <select
                value={roleChoice}
                onChange={(e) => setRoleChoice(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800"
              >
                {SECONDARY_ROLE_PRESETS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
                <option value={CUSTOM}>Custom…</option>
              </select>
            </label>
            {roleChoice === CUSTOM && (
              <input
                type="text"
                value={customRole}
                onChange={(e) => setCustomRole(e.target.value)}
                placeholder="e.g. Security, Data, …"
                className="mb-1.5 w-full rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800"
              />
            )}
            <div className="flex gap-2">
              <button
                type="button"
                disabled={!canCopySecondary}
                onClick={() =>
                  copy(buildSecondaryPrompt(role), `${role.trim()} prompt`)
                }
                className="flex-1 rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Copy prompt
              </button>
              <button
                type="button"
                onClick={() => copy(buildSecondaryCurls(roomLink), "Secondary curls")}
                className="flex-1 rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Copy curls
              </button>
            </div>
          </section>

          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Paste the prompt at the start of the agent&apos;s conversation,
            then paste the curls so it can act in the room.
          </p>
        </div>
      )}
    </div>
  );
}
