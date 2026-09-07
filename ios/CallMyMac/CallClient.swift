import Foundation

/// Minimal HTTP client for Phase 0 text calls (WebSocket / WebRTC later).
@MainActor
final class CallClient: ObservableObject {
    @Published var inCall = false
    @Published var muted = false
    @Published var statusText = "未连接"
    @Published var transcript = ""

    private var sessionId: String?

    func startCall(settings: AppSettings) async {
        guard let base = settings.baseURL else {
            statusText = "主机地址无效"
            return
        }
        var req = URLRequest(url: base.appendingPathComponent("v1/session"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(settings.token)", forHTTPHeaderField: "Authorization")
        req.httpBody = try? JSONSerialization.data(withJSONObject: [
            "client": "ios",
            "locale": "zh-CN",
        ])
        do {
            let (data, resp) = try await URLSession.shared.data(for: req)
            guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
                statusText = "建连失败"
                return
            }
            let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            sessionId = obj?["session_id"] as? String
            inCall = true
            statusText = "通话中（文本模式）"
            transcript += "— 通话开始 —\n"
        } catch {
            statusText = "错误：\(error.localizedDescription)"
        }
    }

    func hangUp() async {
        inCall = false
        muted = false
        sessionId = nil
        statusText = "已挂断"
        transcript += "— 通话结束 —\n"
    }

    func sendUtterance(_ text: String, settings: AppSettings) async {
        guard let base = settings.baseURL, let sessionId, !text.isEmpty else { return }
        if muted {
            transcript += "(静音，未发送)\n"
            return
        }
        var req = URLRequest(url: base.appendingPathComponent("v1/utterance"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(settings.token)", forHTTPHeaderField: "Authorization")
        req.httpBody = try? JSONSerialization.data(withJSONObject: [
            "session_id": sessionId,
            "text": text,
            "source": "text",
        ])
        transcript += "你：\(text)\n"
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            if let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let reply = obj["text"] as? String {
                transcript += "Mac：\(reply)\n"
            } else {
                transcript += "Mac：(无回复)\n"
            }
        } catch {
            transcript += "错误：\(error.localizedDescription)\n"
        }
    }
}
