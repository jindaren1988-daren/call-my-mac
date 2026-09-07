import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var settings: AppSettings

    var body: some View {
        Form {
            Section("Mac Companion") {
                TextField("主机（Tailscale IP 或域名）", text: $settings.host)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                TextField("端口", text: $settings.port)
                    .keyboardType(.numberPad)
                SecureField("配对 Token", text: $settings.token)
            }
            Section("说明") {
                Text("请先在 Mac 上启动 Companion，并用 Tailscale 组网。Token 与 Mac 端 CALL_MY_MAC_TOKEN 一致。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("设置")
    }
}

final class AppSettings: ObservableObject {
    @Published var host: String = "127.0.0.1"
    @Published var port: String = "8742"
    @Published var token: String = ""

    var baseURL: URL? {
        URL(string: "http://\(host):\(port)")
    }
}
