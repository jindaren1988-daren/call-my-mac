# Protocol — Call my Mac

Version: **0.1-draft** (Phase 0 text control plane)

## Transport

| Channel | Use |
|---------|-----|
| HTTPS REST | Health, create session, one-shot utterance, confirm action |
| WSS | Duplex session: utterances, agent replies, session events |
| WebRTC | **Target for Phase 1 audio** (not implemented; see notes) |

Base URL example: `https://100.x.y.z:8742` (Tailscale) or `http://127.0.0.1:8742` (local demo; TLS later).

## Authentication

Every authenticated request:

```
Authorization: Bearer <pairing_token>
```

- Token created once on Mac (`CALL_MY_MAC_TOKEN` or generated at first boot).
- Treat as device secret; rotate by restarting companion with new env.
- Unauthenticated → `401`. Wrong token → `401`.

WebSocket: send token either as `Authorization` header (preferred) or first client message:

```json
{"type": "auth", "token": "<pairing_token>"}
```

## Message types (JSON)

### Common envelope

```json
{
  "type": "<string>",
  "session_id": "<uuid>",
  "ts": "<ISO-8601>",
  "payload": {}
}
```

### Client → Server

| type | payload | meaning |
|------|---------|---------|
| `auth` | `{ "token" }` | WS auth if header unused |
| `session.start` | `{ "client": "ios", "locale": "zh-CN" }` | begin call |
| `session.end` | `{ "reason": "hangup" }` | end call |
| `session.mute` | `{ "muted": true }` | UI mute flag (media P1) |
| `utterance` | `{ "text": "打开 Safari", "source": "text" }` | user speech/text |
| `action.confirm` | `{ "action_id": "...", "accept": true }` | confirm pending action |
| `ping` | `{}` | keepalive |

`source`: `text` (Phase 0) | `stt` (Phase 1) | `sim` (demo script).

### Server → Client

| type | payload | meaning |
|------|---------|---------|
| `auth.ok` / `auth.fail` | `{ "message"? }` | WS auth result |
| `session.started` | `{ "session_id", "dry_run", "agent" }` | session ready |
| `session.ended` | `{ "reason" }` | closed |
| `agent.reply` | see below | model/stub response |
| `action.proposed` | see below | dry-run or needs confirm |
| `action.result` | `{ "action_id", "ok", "detail" }` | execution outcome |
| `error` | `{ "code", "message" }` | recoverable error |
| `pong` | `{}` | keepalive |

### `agent.reply` payload

```json
{
  "text": "好的，将打开 Safari（dry-run）。",
  "locale": "zh-CN",
  "actions": [
    {
      "action_id": "a1",
      "intent": "open_app",
      "args": { "name": "Safari" },
      "needs_confirmation": false,
      "dry_run": true,
      "proposed_cmd": "activate application Safari"
    }
  ],
  "metadata": { "backend": "stub" }
}
```

## REST endpoints

### `GET /health`

No auth. Response:

```json
{ "ok": true, "service": "call-my-mac", "version": "0.1.0", "dry_run": true }
```

### `POST /v1/session`

Auth required. Body optional: `{ "client": "ios", "locale": "zh-CN" }`.  
Response: `{ "session_id", "dry_run", "agent", "ws_path": "/v1/ws" }`.

### `POST /v1/utterance`

Auth required. Body:

```json
{ "session_id": "<uuid>", "text": "现在电量多少", "source": "sim" }
```

Response: same shape as `agent.reply` payload (+ `session_id`).

### `POST /v1/confirm`

Auth required. Body: `{ "session_id", "action_id", "accept": true }`.  
If `accept` and not dry-run → run capability; else cancel.

### `WS /v1/ws`

Auth required. After auth, client sends `session.start`, then `utterance` messages; server pushes `agent.reply`.

## Intent allowlist (Phase 0)

| intent | args | capability |
|--------|------|------------|
| `open_app` | `name` | activate allowlisted app |
| `say` | `text` | speech / say stub |
| `get_battery` | — | battery query stub |
| `screenshot` | `path?` | screenshot path stub |
| `noop` | — | acknowledge only |

Unknown intents → rejected, never executed.

## WebRTC notes (Phase 1 target)

- Signaling can reuse this WS: `webrtc.offer` / `webrtc.answer` / `webrtc.ice`.
- Prefer Opus audio; STT on Mac (or on-device) produces `utterance` with `source: "stt"`.
- TTS of `agent.reply.text` played back on phone or Mac speaker (product choice).
- Phase 0 may optionally stream base64 PCM frames later as a bridge; **not required** for control-plane demo.

## Error codes

| code | meaning |
|------|---------|
| `unauthorized` | missing/bad token |
| `session_not_found` | bad session_id |
| `intent_forbidden` | not on allowlist |
| `confirmation_required` | waiting for confirm |
| `backend_error` | agent/LLM failure |

## Versioning

Bump `version` in `/health` and this doc together. Breaking changes → new major in path (`/v2/...`) when needed.
