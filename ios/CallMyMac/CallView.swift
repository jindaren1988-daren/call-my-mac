import SwiftUI

/// 通话主界面：打电话 / 挂断 / 静音
struct CallView: View {
    @EnvironmentObject var settings: AppSettings
    @EnvironmentObject var client: CallClient
    @State private var draft = "打开 Safari"

    var body: some View {
        VStack(spacing: 24) {
            Text("Call my Mac")
                .font(.largeTitle.bold())
            Text(client.statusText)
                .foregroundStyle(.secondary)

            ScrollView {
                Text(client.transcript)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
            }
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))

            TextField("说点什么…", text: $draft)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal)

            HStack(spacing: 20) {
                Button(client.inCall ? "挂断" : "打电话") {
                    Task {
                        if client.inCall {
                            await client.hangUp()
                        } else {
                            await client.startCall(settings: settings)
                        }
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(client.inCall ? .red : .green)

                Button(client.muted ? "取消静音" : "静音") {
                    client.muted.toggle()
                }
                .buttonStyle(.bordered)
                .disabled(!client.inCall)

                Button("发送") {
                    Task { await client.sendUtterance(draft, settings: settings) }
                }
                .buttonStyle(.bordered)
                .disabled(!client.inCall)
            }
        }
        .padding()
        .navigationTitle("通话")
    }
}

#Preview {
    CallView()
        .environmentObject(AppSettings())
        .environmentObject(CallClient())
}
