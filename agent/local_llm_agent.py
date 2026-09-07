"""LocalLLMAgent stub — OpenAI-compatible local endpoint slot (Ollama / llama.cpp).

TODO Phase 2:
  - POST {OPENAI_COMPAT_BASE}/v1/chat/completions
  - System prompt listing ONLY allowlisted intents + JSON schema
  - Parse model JSON → intents; reject unknown; never run raw shell from model
  - Fall back to StubAgent on timeout/parse error
"""
from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from .base import AgentContext, AgentReply, ProposedAction
from .capabilities import CONFIRM_INTENTS, execute_capability
from .stub_agent import StubAgent, _aid


class LocalLLMAgent:
    """Skeleton backend. If endpoint unreachable, delegates to StubAgent."""

    name = "local_llm"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        fallback: StubAgent | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OPENAI_COMPAT_BASE", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.environ.get("CALL_MY_MAC_LLM_MODEL", "llama3.2")
        self.fallback = fallback or StubAgent()

    def chat(self, utterance: str, context: AgentContext) -> AgentReply:
        # Phase 0/2 scaffold: attempt optional call; on any failure use stub.
        try:
            parsed = self._try_complete(utterance, context)
            if parsed is None:
                return self._fallback(utterance, context, reason="empty_or_unparsed")
            return self._from_parsed(parsed, context)
        except Exception as e:  # noqa: BLE001
            reply = self._fallback(utterance, context, reason=str(e))
            reply.metadata["llm_error"] = str(e)
            return reply

    def _fallback(self, utterance: str, context: AgentContext, reason: str) -> AgentReply:
        reply = self.fallback.chat(utterance, context)
        reply.metadata = {**reply.metadata, "backend": self.name, "fell_back": True, "reason": reason}
        return reply

    def _try_complete(self, utterance: str, context: AgentContext) -> dict[str, Any] | None:
        """Call OpenAI-compatible chat completions. Returns parsed JSON object or None.

        Disabled unless CALL_MY_MAC_LLM=1 so demos stay offline-friendly.
        """
        if os.environ.get("CALL_MY_MAC_LLM", "0") != "1":
            return None

        system = (
            "You are Call my Mac local brain. Reply ONLY with JSON: "
            '{"text":"...","intent":"open_app|say|get_battery|screenshot|noop",'
            '"args":{}}. Intents outside this set are forbidden. Never invent shell.'
        )
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": utterance},
            ],
            "temperature": 0.2,
        }
        req = request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=8) as resp:  # noqa: S310 — local endpoint
            payload = json.loads(resp.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        # Extract JSON object from content
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end < 0:
            return None
        return json.loads(content[start : end + 1])

    def _from_parsed(self, parsed: dict[str, Any], context: AgentContext) -> AgentReply:
        intent = str(parsed.get("intent") or "noop")
        args = parsed.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        text = str(parsed.get("text") or "")
        result = execute_capability(intent, args, dry_run=context.dry_run)
        if not result.ok:
            return AgentReply(
                text=text or f"拒绝：{result.detail}",
                actions=[],
                locale=context.locale,
                metadata={"backend": self.name, "error": result.detail},
            )
        action = ProposedAction(
            action_id=_aid(),
            intent=intent,
            args=args,
            needs_confirmation=intent in CONFIRM_INTENTS,
            dry_run=context.dry_run,
            proposed_cmd=result.proposed_cmd,
        )
        return AgentReply(
            text=text or result.detail,
            actions=[action],
            locale=context.locale,
            metadata={"backend": self.name, "capability_detail": result.detail},
        )
