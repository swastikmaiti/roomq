/**
 * Role-prompt bundles for the meeting view. These are pasted at the start of
 * the agent's conversation — they tell it *who it is*. The curl bundles (see
 * curls.ts) tell it *how to act*. Keep these two complementary.
 *
 * Templates live here so the UI and the README can't drift.
 */

/** Default presets for the secondary role picker. "Custom…" is handled in the UI. */
export const SECONDARY_ROLE_PRESETS = [
  "Code Review",
  "GitHub",
  "DevOps",
  "QA",
  "Research",
  "Docs",
  "Security",
] as const;

export function buildPrimaryPrompt(): string {
  return `You will join the room as Primary Agent.
There will be other agents from which we will take help as and when required.
Do not interact with other agents until I say so.
I will instruct you to communicate with other agents as and when required.
`;
}

export function buildSecondaryPrompt(role: string): string {
  const r = (role || "").trim() || "Secondary";
  return `You will join the Room as ${r} Agent.
Keep Listening for your instructions.
Once you have an instruction, work accordingly and once done provide reply to Primary Agent and keep listening for next instructions.
Always keep listening for instructions until you are asked to leave or room expire.
If listening stops by any reason please restart immediately.
`;
}
