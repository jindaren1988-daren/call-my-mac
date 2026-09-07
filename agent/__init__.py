"""Pluggable agent backends for Call my Mac."""
from .base import AgentBackend, AgentContext, AgentReply, ProposedAction
from .stub_agent import StubAgent
from .local_llm_agent import LocalLLMAgent
from .factory import create_agent

__all__ = [
    "AgentBackend", "AgentContext", "AgentReply", "ProposedAction",
    "StubAgent", "LocalLLMAgent", "create_agent",
]
