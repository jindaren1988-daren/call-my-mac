# Agent package

- `AgentBackend.chat(utterance, context) -> AgentReply`
- `StubAgent` — phrase → allowlisted intents
- `LocalLLMAgent` — slot for Ollama / llama.cpp OpenAI-compatible API (`CALL_MY_MAC_LLM=1`)
- `capabilities.py` — allowlist + dry-run proposals (live Darwin runner optional via `CALL_MY_MAC_ALLOW_LIVE=1` + future `mac/live_runner.py`)

Safety: no `eval` of model shell; unknown intents rejected.
