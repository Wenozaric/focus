import SwiftUI
struct SystemCard: View {
    var visionText: String; var verdict: String; var tag: String; var title: String
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Система").font(.system(size: 14, weight: .bold)).foregroundColor(DS.fg)
                Text("moondream  ·  640px  ·  80 токенов  ·  90с").font(.system(size: 11, weight: .semibold)).foregroundColor(DS.muted)
                Spacer()
                Text(Date.now, style: .time).font(.system(size: 11, design: .monospaced)).foregroundColor(DS.muted)
            }
            VStack(alignment: .leading, spacing: 8) {
                Label("Скрин", systemImage: "photo").font(.system(size: 10, weight: .bold)).foregroundColor(DS.muted)
                VerdictBlock(text: visionText)
                Label("Вердикт · \(tag.uppercased())", systemImage: "sparkles").font(.system(size: 10, weight: .bold)).foregroundColor(DS.muted)
                VerdictBlock(text: verdict)
                Text("заголовок: \(title)").font(.system(size: 11, design: .monospaced)).foregroundColor(DS.muted).lineLimit(2)
            }
        }.card()
    }
}
