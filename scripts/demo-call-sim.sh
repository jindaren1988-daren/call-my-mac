#!/usr/bin/env bash
# Phase 0: simulate a text "phone call" against the Mac companion.
set -euo pipefail

BASE="${CALL_MY_MAC_BASE:-http://127.0.0.1:8742}"
TOKEN="${CALL_MY_MAC_TOKEN:?Set CALL_MY_MAC_TOKEN to the companion bearer token}"

echo "== health =="
curl -sf "$BASE/health" | python3 -m json.tool

echo
echo "== start session =="
SESSION_JSON=$(curl -sf -X POST "$BASE/v1/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client":"demo-call-sim","locale":"zh-CN"}')
echo "$SESSION_JSON" | python3 -m json.tool
SESSION_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["session_id"])' <<<"$SESSION_JSON")

utter() {
  local text="$1"
  echo
  echo "-- you: $text"
  curl -sf -X POST "$BASE/v1/utterance" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"session_id":sys.argv[1],"text":sys.argv[2],"source":"sim"}))' "$SESSION_ID" "$text")" \
    | python3 -m json.tool
}

utter "你好"
utter "打开 Safari"
utter "现在电量多少"
utter "说：会议室里有人吗"
utter "帮我截图"
utter "open Notes"
utter "这是一句随便说说"

echo
echo "== done (session $SESSION_ID) =="
