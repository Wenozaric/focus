import SwiftUI

@main
struct FocusNannyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 980, minHeight: 780)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("About Focus") { NSApplication.shared.orderFrontStandardAboutPanel(nil) }
            }
        }
    }
}
