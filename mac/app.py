"""Call my Mac — Mac Companion (FastAPI).

Phase 0: health, session, utterance, confirm, WebSocket text loop.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Make ../agent importable
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent import AgentContext, create_agent  # noqa: E402
from agent.capabilities import execute_capability  # noqa: E402
from config import Settings, load_settings  # noqa: E402

settings: Settings = load_settings()
agent = create_agent()

app = FastAPI(title="Call my Mac Companion", version=settings.version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> meta
SESSIONS: dict[str, dict[str, Any]] = {}
# action_id -> pending action dict
PENDING: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "missing bearer"})
    token = authorization.split(" ", 1)[1].strip()
    if token != settings.token:
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "bad token"})


class SessionIn(BaseModel):
    client: str = "unknown"
    locale: str = "zh-CN"


class UtteranceIn(BaseModel):
    session_id: str
    text: str
    source: str = "text"


class ConfirmIn(BaseModel):
    session_id: str
    action_id: str
    accept: bool = True


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "call-my-mac",
        "version": settings.version,
        "dry_run": settings.dry_run,
        "agent": getattr(agent, "name", "unknown"),
    }


@app.post("/v1/session")
def start_session(body: SessionIn | None = None, _: None = Depends(require_token)) -> dict[str, Any]:
    body = body or SessionIn()
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "client": body.client,
        "locale": body.locale,
        "created": _now(),
        "history": [],
    }
    return {
        "session_id": sid,
        "dry_run": settings.dry_run,
        "agent": getattr(agent, "name", "unknown"),
        "ws_path": "/v1/ws",
    }


def _handle_utterance(session_id: str, text: str, source: str) -> dict[str, Any]:
    sess = SESSIONS.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": session_id})
    ctx = AgentContext(
        session_id=session_id,
        locale=sess.get("locale", "zh-CN"),
        dry_run=settings.dry_run,
        history=list(sess.get("history") or []),
        extra={"source": source},
    )
    reply = agent.chat(text, ctx)
    sess.setdefault("history", []).append({"role": "user", "content": text})
    sess["history"].append({"role": "assistant", "content": reply.text})
    for action in reply.actions:
        PENDING[action.action_id] = {
            "session_id": session_id,
            "intent": action.intent,
            "args": action.args,
            "needs_confirmation": action.needs_confirmation,
            "proposed_cmd": action.proposed_cmd,
        }
    data = reply.to_dict(session_id=session_id)
    data["source"] = source
    data["ts"] = _now()
    return data


@app.post("/v1/utterance")
def utterance(body: UtteranceIn, _: None = Depends(require_token)) -> dict[str, Any]:
    return _handle_utterance(body.session_id, body.text, body.source)


@app.post("/v1/confirm")
def confirm(body: ConfirmIn, _: None = Depends(require_token)) -> dict[str, Any]:
    if body.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail={"code": "session_not_found"})
    pending = PENDING.get(body.action_id)
    if not pending or pending["session_id"] != body.session_id:
        raise HTTPException(status_code=404, detail={"code": "action_not_found"})
    if not body.accept:
        pending["status"] = "cancelled"
        return {"action_id": body.action_id, "ok": True, "detail": "cancelled", "ts": _now()}
    result = execute_capability(
        pending["intent"],
        pending["args"],
        dry_run=settings.dry_run,
    )
    pending["status"] = "executed" if result.executed else "proposed"
    return {
        "action_id": body.action_id,
        "ok": result.ok,
        "detail": result.detail,
        "executed": result.executed,
        "dry_run": settings.dry_run,
        "proposed_cmd": result.proposed_cmd,
        "ts": _now(),
    }


@app.websocket("/v1/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    authed = False
    session_id: str | None = None

    # Header auth (some clients)
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        if auth.split(" ", 1)[1].strip() == settings.token:
            authed = True
            await websocket.send_json({"type": "auth.ok", "ts": _now(), "payload": {}})

    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type")
            payload = raw.get("payload") or {}

            if not authed:
                if msg_type == "auth" and payload.get("token") == settings.token:
                    authed = True
                    await websocket.send_json({"type": "auth.ok", "ts": _now(), "payload": {}})
                    continue
                await websocket.send_json(
                    {"type": "auth.fail", "ts": _now(), "payload": {"message": "unauthorized"}}
                )
                await websocket.close(code=4401)
                return

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": _now(), "payload": {}})
                continue

            if msg_type == "session.start":
                body = SessionIn(
                    client=payload.get("client", "ws"),
                    locale=payload.get("locale", "zh-CN"),
                )
                # reuse REST logic without Depends
                sid = str(uuid.uuid4())
                SESSIONS[sid] = {
                    "client": body.client,
                    "locale": body.locale,
                    "created": _now(),
                    "history": [],
                }
                session_id = sid
                await websocket.send_json(
                    {
                        "type": "session.started",
                        "session_id": sid,
                        "ts": _now(),
                        "payload": {
                            "session_id": sid,
                            "dry_run": settings.dry_run,
                            "agent": getattr(agent, "name", "unknown"),
                        },
                    }
                )
                continue

            if msg_type == "session.end":
                await websocket.send_json(
                    {
                        "type": "session.ended",
                        "session_id": session_id,
                        "ts": _now(),
                        "payload": {"reason": payload.get("reason", "hangup")},
                    }
                )
                continue

            if msg_type == "utterance":
                sid = raw.get("session_id") or session_id or payload.get("session_id")
                text = payload.get("text") or raw.get("text") or ""
                source = payload.get("source") or "text"
                if not sid:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "ts": _now(),
                            "payload": {"code": "session_not_found", "message": "no session"},
                        }
                    )
                    continue
                try:
                    data = _handle_utterance(sid, text, source)
                except HTTPException as e:
                    await websocket.send_json(
                        {"type": "error", "ts": _now(), "payload": e.detail if isinstance(e.detail, dict) else {"message": str(e.detail)}}
                    )
                    continue
                await websocket.send_json(
                    {
                        "type": "agent.reply",
                        "session_id": sid,
                        "ts": _now(),
                        "payload": data,
                    }
                )
                continue

            await websocket.send_json(
                {
                    "type": "error",
                    "ts": _now(),
                    "payload": {"code": "unknown_type", "message": str(msg_type)},
                }
            )
    except WebSocketDisconnect:
        return


def main() -> None:
    import uvicorn

    # Print token once if auto-generated so local demos can copy it
    print(f"[call-my-mac] token={settings.token}")
    print(f"[call-my-mac] dry_run={settings.dry_run} agent={getattr(agent, 'name', '?')}")
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
