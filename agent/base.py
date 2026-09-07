"""Agent interface contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class AgentContext:
    session_id: str
    locale: str = "zh-CN"
    dry_run: bool = True
    history: list[dict[str, str]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProposedAction:
    action_id: str
    intent: str
    args: dict[str, Any]
    needs_confirmation: bool = False
    dry_run: bool = True
    proposed_cmd: str = ""
    status: str = "proposed"


@dataclass
class AgentReply:
    text: str
    actions: list[ProposedAction] = field(default_factory=list)
    locale: str = "zh-CN"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, session_id: str | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "text": self.text,
            "locale": self.locale,
            "actions": [
                {
                    "action_id": a.action_id,
                    "intent": a.intent,
                    "args": a.args,
                    "needs_confirmation": a.needs_confirmation,
                    "dry_run": a.dry_run,
                    "proposed_cmd": a.proposed_cmd,
                    "status": a.status,
                }
                for a in self.actions
            ],
            "metadata": self.metadata,
        }
        if session_id is not None:
            data["session_id"] = session_id
        return data


@runtime_checkable
class AgentBackend(Protocol):
    name: str

    def chat(self, utterance: str, context: AgentContext) -> AgentReply:
        """Map user utterance to reply text + allowlisted proposed actions."""
        ...
