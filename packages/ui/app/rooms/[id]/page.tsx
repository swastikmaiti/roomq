import { RoomView } from "@/components/RoomView";

// Room ids are created at runtime and unguessable, so this route can't be
// statically pre-rendered. On Cloudflare Pages (@cloudflare/next-on-pages) that
// means it runs on the edge runtime, which renders the client viewer on demand.
export const runtime = "edge";

export default function RoomPage({ params }: { params: { id: string } }) {
  return <RoomView roomId={decodeURIComponent(params.id)} />;
}
