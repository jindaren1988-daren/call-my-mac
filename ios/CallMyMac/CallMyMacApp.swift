import SwiftUI

@main
struct CallMyMacApp: App {
    @StateObject private var settings = AppSettings()
    @StateObject private var callClient = CallClient()

    var body: some Scene {
        WindowGroup {
            TabView {
                CallView()
                    .tabItem { Label("通话", systemImage: "phone.fill") }
                SettingsView()
                    .tabItem { Label("设置", systemImage: "gearshape") }
            }
            .environmentObject(settings)
            .environmentObject(callClient)
        }
    }
}
