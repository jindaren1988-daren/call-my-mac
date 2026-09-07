# WebRTC / audio notes (Phase 1)

Target path:

1. Reuse `/v1/ws` for signaling: `webrtc.offer` / `webrtc.answer` / `webrtc.ice`.
2. Duplex Opus audio between iPhone and Mac companion.
3. Mac-side STT → `utterance` with `source: "stt"` → same `AgentBackend.chat()`.
4. TTS of `agent.reply.text` → play on phone or Mac.

Phase 0 bridge (optional, not implemented): base64 PCM frames over WS.  
**Control plane works without audio** via `demo-call-sim.sh` and REST `/v1/utterance`.
