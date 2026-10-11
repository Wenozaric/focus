import SwiftUI
struct NowCard: View {
    var exe: String; var title: String; var onVision: ()->Void; var onTest: ()->Void
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Сейчас").font(.system(size: 14, weight: .bold)).foregroundColor(DS.fg)
            Text("активное окно").font(.system(size: 11)).foregroundColor(DS.muted)
            Text(exe).font(.system(size: 11, design: .monospaced)).foregroundColor(DS.muted).lineLimit(1)
            Text(title).font(.system(size: 13, weight: .medium)).foregroundColor(DS.fg).lineLimit(2).fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 8) {
                Button(action: onVision) {
                    Text("Скрин сейчас").font(.system(size: 13, weight: .bold)).foregroundColor(.white)
                        .padding(.horizontal, 16).padding(.vertical, 8).background(Capsule().fill(DS.accent))
                }.buttonStyle(.plain)
                Button("Тест баннера", action: onTest).buttonStyle(.bordered).controlSize(.regular).tint(DS.fg)
            }.padding(.top, 6)
        }.card().frame(maxWidth: .infinity, alignment: .leading)
    }
}
