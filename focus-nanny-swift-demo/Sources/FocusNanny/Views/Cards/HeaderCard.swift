import SwiftUI
struct HeaderCard: View {
    var cat: String
    var body: some View {
        HStack(spacing: 14) {
            ZStack { RoundedRectangle(cornerRadius: 12, style: .continuous).fill(DS.fg).frame(width: 40, height: 40)
                Text("FN").font(.system(size: 10, weight: .bold, design: .rounded)).foregroundColor(.white)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("FOCUS").font(.system(size: 13, weight: .bold)).foregroundColor(DS.fg)
                Text("Локальный контроль фокуса  ·  moondream  ·  приватно").font(.system(size: 11)).foregroundColor(DS.muted)
            }
            Spacer()
            HStack(spacing: 8) {
                Circle().fill(colorFor(cat)).frame(width: 8, height: 8)
                Text(cat).font(.system(size: 12, weight: .bold, design: .monospaced)).foregroundColor(DS.fg)
                Text(cat.uppercased()).font(.system(size: 10, weight: .bold)).foregroundColor(.white)
                    .padding(.horizontal, 10).padding(.vertical, 4).background(Capsule().fill(colorFor(cat)))
            }.padding(.horizontal, 12).padding(.vertical, 8)
             .background(RoundedRectangle(cornerRadius: 10).fill(DS.card2).overlay(RoundedRectangle(cornerRadius: 10).stroke(DS.border, lineWidth: 1)))
        }.card(padding: 16)
    }
    func colorFor(_ c: String) -> Color {
        switch c { case "work": return DS.gWork; case "youtube_edu": return DS.gYtEdu; case "youtube": return DS.gYt; case "game": return DS.gGame; case "idle": return DS.gIdle; default: return DS.gOther }
    }
}
