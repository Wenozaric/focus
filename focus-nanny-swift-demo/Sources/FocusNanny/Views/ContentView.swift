import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = PythonBridge()
    @State private var gameLimit: Double = 30
    @State private var ytLimit: Double = 30
    @State private var nagInterval: Double = 5
    @State private var volume: Double = 35
    @State private var enableVoice = false
    @State private var enablePopup = true
    @State private var enableVision = true

    var body: some View {
        ZStack { DS.bg.ignoresSafeArea()
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 14) {
                    HeaderCard(cat: bridge.currentCat)
                    HStack(alignment: .top, spacing: 12) {
                        TodayCard(totals: bridge.totals, currentCat: bridge.currentCat)
                        NowCard(exe: bridge.exe, title: bridge.title, onVision: { bridge.triggerVision() }, onTest: { bridge.triggerNag() })
                    }
                    SystemCard(visionText: bridge.visionText, verdict: bridge.verdict, tag: bridge.visionTag, title: bridge.title)
                    SettingsCard(game: $gameLimit, yt: $ytLimit, nag: $nagInterval, vol: $volume,
                                 voice: $enableVoice, popup: $enablePopup, vision: $enableVision,
                                 onChange: { bridge.sendLimits(game: Int(gameLimit), youtube: Int(ytLimit), nag: Int(nagInterval), volume: Int(volume)) })
                    HStack {
                        Text("Focus · локально · приватно").font(.system(size: 11, weight: .medium)).foregroundColor(DS.sub)
                        Spacer()
                        Button("Сбросить сегодня") { bridge.totals = [:] }.buttonStyle(.bordered).controlSize(.small)
                    }.padding(.horizontal, 4)
                }.padding(20)
            }
        }
        .toolbar { ToolbarItem(placement: .principal) { Text("Focus").font(.system(size: 13, weight: .bold)).foregroundColor(DS.fg) } }
    }
}
