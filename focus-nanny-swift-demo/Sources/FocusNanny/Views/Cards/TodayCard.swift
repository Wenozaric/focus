import SwiftUI
struct TodayCard: View {
    var totals: [String: Double]; var currentCat: String
    var totalMins: Double { totals.values.reduce(0, +) }
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Сегодня").font(.system(size: 15, weight: .bold)).foregroundColor(DS.fg)
                Text("·  всего времени").font(.system(size: 11)).foregroundColor(DS.muted)
                Spacer()
                Text(String(format: "%.0fм всего", totalMins)).font(.system(size: 12, weight: .bold, design: .monospaced)).foregroundColor(DS.fg)
            }
            Text(String(format: "%dч %02dм", Int(totalMins)/60, Int(totalMins)%60))
                .font(.system(size: 34, weight: .bold, design: .rounded)).foregroundColor(DS.fg)
                .lineLimit(1).minimumScaleFactor(0.7)
            Text("общее время за сегодня").font(.system(size: 11)).foregroundColor(DS.muted)
            VStack(spacing: 10) {
                ForEach(Category.allCases) { c in
                    let v = totals[c.rawValue] ?? 0
                    let pct = totalMins > 0 ? v/totalMins : 0
                    CategoryRow(cat: c, value: v, pct: pct, active: c.rawValue == currentCat)
                }
            }
        }.card().frame(maxWidth: .infinity, alignment: .leading)
    }
}
