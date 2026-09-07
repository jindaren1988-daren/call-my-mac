"""Select agent backend from env."""
from __future__ import annotations

import os

from .local_llm_agent import LocalLLMAgent
from .stub_agent import StubAgent


def create_agent():
    kind = os.environ.get("CALL_MY_MAC_AGENT", "stub").strip().lower()
    if kind in {"llm", "local_llm", "ollama"}:
        return LocalLLMAgent()
    return StubAgent()
