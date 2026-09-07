"""Phrase-map StubAgent: Chinese/English → allowlisted intents."""
from __future__ import annotations

import re
import uuid

from .base import AgentContext, AgentReply, ProposedAction
from .capabilities import CONFIRM_INTENTS, execute_capability


def _aid() -> str:
    return uuid.uuid4().hex[:10]


class StubAgent:
    name = "stub"

    def chat(self, utterance: str, context: AgentContext) -> AgentReply:
        text = (utterance or "").strip()
        if not text:
            return AgentReply(
                text="我在听，请再说一次。",
                locale=context.locale,
                metadata={"backend": self.name},
            )

        intent, args, reply = self._match(text)
        result = execute_capability(intent, args, dry_run=context.dry_run)
        needs = intent in CONFIRM_INTENTS
        action = ProposedAction(
            action_id=_aid(),
            intent=intent,
            args=args,
            needs_confirmation=needs,
            dry_run=context.dry_run,
            proposed_cmd=result.proposed_cmd,
            status="proposed",
        )
        if not result.ok:
            return AgentReply(
                text=f"无法执行：{result.detail}",
                actions=[],
                locale=context.locale,
                metadata={"backend": self.name, "error": result.detail},
            )

        suffix = "（dry-run，未真正执行）" if context.dry_run else ""
        body = reply
        if intent == "get_battery":
            body = f"{reply} {result.detail}"
        return AgentReply(
            text=f"{body}{suffix}",
            actions=[action],
            locale=context.locale,
            metadata={"backend": self.name, "capability_detail": result.detail},
        )

    def _match(self, text: str) -> tuple[str, dict, str]:
        lower = text.lower()

        m = re.search(r"(?:打开|開啟|open|launch)\s+(.+)$", text, re.I)
        if m:
            name = m.group(1).strip().strip("。.!！")
            return "open_app", {"name": name}, f"好的，将打开 {name}。"

        m = re.search(r"(?:打开|open)\s*(safari|finder|notes|terminal|music|mail|messages)", lower)
        if m:
            name = m.group(1)
            return "open_app", {"name": name}, f"好的，将打开 {name}."

        m = re.search(r"(?:说|講|say|speak)[：:\s]+(.+)$", text, re.I)
        if m:
            t = m.group(1).strip()
            return "say", {"text": t}, f"好的，将朗读：{t[:40]}"

        if re.search(r"电量|電池|battery|power\s*level", text, re.I):
            return "get_battery", {}, "正在查询电量："

        if re.search(r"截图|截圖|screenshot|screen\s*cap", text, re.I):
            return "screenshot", {}, "准备截图（需确认）。"

        if re.search(r"^(你好|您好|hello|hi|hey)\b", text, re.I):
            return "noop", {}, "你好，我是 Call my Mac 本地助手。可以说：打开 Safari、电量多少、说：你好。"

        if re.search(r"帮助|help|能做什么", text, re.I):
            return (
                "noop",
                {},
                "支持：打开应用、朗读、查电量、截图（白名单 + dry-run）。本地 LLM 稍后接入。",
            )

        return "noop", {}, f"已收到：「{text[:80]}」。暂未匹配到动作；可试「打开 Safari」或「电量」。"
