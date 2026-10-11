import SwiftUI

struct CategoryRow: View {
    var cat: Category
    var value: Double
    var pct: Double
    var active: Bool
    var body: some View {
        HStack(spacing: 10) {
            Circle().fill(cat.color).frame(width: 8, height: 8)
            Text(cat.label).font(.system(size: 13, weight: active ? .bold : .regular)).foregroundColor(DS.fg).frame(width: 130, alignment: .leading)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(DS.track).frame(height: 6)
                    Capsule().fill(cat.color).frame(width: max(0, geo.size.width * pct), height: 6)
                }
            }.frame(height: 6)
            Text(value < 60 ? String(format: "%.1fм", value) : String(format: "%.1fч", value/60))
                .font(.system(size: 12, weight: .bold, design: .monospaced)).foregroundColor(active ? DS.fg : DS.muted).frame(width: 52, alignment: .trailing)
            Text(String(format: "%d%%", Int(round(pct*100))))
                .font(.system(size: 12)).foregroundColor(active ? DS.fg : DS.muted).frame(width: 34, alignment: .trailing)
        }
    }
}
