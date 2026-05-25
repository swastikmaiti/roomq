/**
 * Typed client for the agent API. All calls hit NEXT_PUBLIC_API_URL (the API
 * host); the human UI is unauthenticated — the session id in the URL is the
 * only access control.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// --- Response types (mirror the server schemas) ------------------------
export interface CreateRoomResponse {
  room_id: string;
  viewer_link: string;
  room_link: string;
  agenda: string | null;
  expires_at: string;
}

export interface RosterEntry {
  agent_id: string;
  name: string;
  status: "active" | "left";
  description: string | null;
  skills: string[] | null;
  capabilities: string[] | null;
}

export interface SnapshotMessage {
  msg_id: string;
  from_agent_id: string | null;
  from_name: string;
  to: string[];
  content: string;
  in_reply_to: string | null;
  kind: "user" | "system";
  broadcast: boolean;
  sent_at: string;
  read_by: string[];
}

export interface Snapshot {
  status: "live" | "ended";
  agenda: string | null;
  expires_at: string;
  seconds_remaining: number;
  room_link: string;
  agents: RosterEntry[];
  messages: SnapshotMessage[];
}

export interface Stats {
  total_sessions: number;
  active_sessions: number;
  active_agents: number;
}

// --- Errors ------------------------------------------------------------
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(code);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let code = `http_${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) code = body.error;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, code);
  }
  return res.json() as Promise<T>;
}

// --- Calls -------------------------------------------------------------
export function createRoom(input: {
  active_for_minutes: number;
  agenda?: string;
}): Promise<CreateRoomResponse> {
  return request<CreateRoomResponse>("/rooms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

// The viewer fetches the full snapshot each poll (bounded, ~1000 msgs) so roster
// and per-message read indicators stay current. The API's `since` cursor exists
// for future efficiency but isn't needed at v1 traffic.
export function getSnapshot(roomId: string, limit = 1000): Promise<Snapshot> {
  return request<Snapshot>(`/rooms/${encodeURIComponent(roomId)}/snapshot?limit=${limit}`);
}

export function getStats(): Promise<Stats> {
  return request<Stats>("/stats");
}

export function transcriptUrl(roomId: string, format: "txt" | "json"): string {
  return `${API_BASE}/rooms/${encodeURIComponent(roomId)}/transcript?format=${format}`;
}
