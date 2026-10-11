import SwiftUI
struct SettingsCard: View {
    @Binding var game: Double; @Binding var yt: Double; @Binding var nag: Double; @Binding var vol: Double
    @Binding var voice: Bool; @Binding var popup: Bool; @Binding var vision: Bool
    var onChange: ()->Void
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Настройки").font(.system(size: 14, weight: .bold)).foregroundColor(DS.fg)
                Text("лимиты и уведомления").font(.system(size: 11)).foregroundColor(DS.muted)
            }
            VStack(spacing: 14) {
                FluentSliderRow(label: "Лимит игры", value: $game, range: 1...60, fmt: "%.0f мин", onChange: onChange)
                FluentSliderRow(label: "Лимит YouTube", value: $yt, range: 1...90, fmt: "%.0f мин", onChange: onChange)
                FluentSliderRow(label: "Интервал напоминания", value: $nag, range: 1...30, fmt: "%.0f мин", onChange: onChange)
                FluentSliderRow(label: "Громкость", value: $vol, range: 0...100, fmt: "%.0f%", onChange: onChange)
            }
            HStack(spacing: 18) {
                Toggle("Озвучивать лимит", isOn: $voice).toggleStyle(.switch).tint(DS.gWork)
                Toggle("Всплывать окном", isOn: $popup).toggleStyle(.switch).tint(DS.gWork)
                Toggle("Анализировать скрин", isOn: $vision).toggleStyle(.switch).tint(DS.gWork)
            }.font(.system(size: 12)).foregroundColor(DS.fg)
        }.card()
    }
}
