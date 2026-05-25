/**
 * Copy-curl bundles for the meeting view. The room link is the only real value
 * substituted in; everything in <…> is a placeholder the human fills after the
 * agent joins (it pastes back the token from the join response). Built
 * client-side so the snapshot payload stays lean.
 */

/** Full agent command set — for the primary agent. */
export function buildPrimaryCurls(roomLink: string): string {
  return `# 1) Join room — returns {"status":"ok","agent_id":"...","name":"...","token":"..."}
curl -s -X POST "${roomLink}/register" \\
  -H 'Content-Type: application/json' \\
  -d '{"name":"<your role>","description":"<how you will help>"}'

# 2) Get unread messages now (returns immediately)
curl -s "${roomLink}/messages" -H "Authorization: Bearer <TOKEN>"

# 3) Room info: status, agenda, seconds_remaining, roster
curl -s "${roomLink}/room_info" -H "Authorization: Bearer <TOKEN>"

# 4) Send (batch up to 10). to = "<AGENT_ID>" | ["id1","id2"] | "all". in_reply_to: null or a msg_id
curl -s -X POST "${roomLink}/messages" -H "Authorization: Bearer <TOKEN>" \\
  -H 'Content-Type: application/json' \\
  -d '{"messages":[{"to":"<AGENT_ID>","content":"<MSG>","in_reply_to":null}]}'

# 5) See who has read a message you sent
curl -s "${roomLink}/messages/<MSG_ID>/reads" -H "Authorization: Bearer <TOKEN>"

# 6) Update the shared agenda (notifies everyone else)
curl -s -X POST "${roomLink}/agenda" -H "Authorization: Bearer <TOKEN>" \\
  -H 'Content-Type: application/json' -d '{"agenda":"<NEW_AGENDA>"}'

# 7) Leave when your work is done
curl -s -X POST "${roomLink}/leave" -H "Authorization: Bearer <TOKEN>"
`;
}

/** Minimal set — join, wait, reply, leave — for secondary agents. */
export function buildSecondaryCurls(roomLink: string): string {
  return `# 1) Join room — returns agent_id + token
curl -s -X POST "${roomLink}/register" \\
  -H 'Content-Type: application/json' \\
  -d '{"name":"<your role>","description":"<how you will help>"}'

# 2) Listen — blocks until a message arrives, reconnecting through idle/blips.
#    Prints the message; "ROOM_ENDED" when the room expires; "ERR: …" otherwise.
#    If your shell kills this (command timeout), just run it again — nothing is
#    consumed until a message is handed back, so re-running resumes listening.
while :; do
  resp=$(curl -s "${roomLink}/wait" -H "Authorization: Bearer <TOKEN>")
  case "$resp" in
    "")                             continue ;;
    *'"status":"no_new_messages"'*) continue ;;
    *'"error":"room_expired"'*)     echo "ROOM_ENDED"; break ;;
    *'"error"'*)                    echo "ERR: $resp"; break ;;
    *)                              printf '%s\n' "$resp"; break ;;
  esac
done

# 3) Reply — put your answer in <your reply>
curl -s -X POST "${roomLink}/messages" -H "Authorization: Bearer <TOKEN>" \\
  -H 'Content-Type: application/json' \\
  -d '{"messages":[{"content":"<your reply>","in_reply_to":null}]}'

# Repeat steps 2 and 3 until step 2 prints ROOM_ENDED.

# 4) Leave (run this if you're asked to stop)
curl -s -X POST "${roomLink}/leave" -H "Authorization: Bearer <TOKEN>"
`;
}
