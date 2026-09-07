# iOS skeleton (SwiftUI)

Open these sources in Xcode on a Mac (File → New Project → iOS App, then replace/add files).

Screens:
- `CallView` — 打电话 / 挂断 / 静音 / 文本发送（Phase 0）
- `SettingsView` — Mac host、端口、配对 Token
- `CallClient` — REST `/v1/session` + `/v1/utterance`

Not buildable on Linux. WebSocket + WebRTC come in Phase 1.
