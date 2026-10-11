import SwiftUI

struct FluentSlider: View {
    var label: String
    @Binding var value: Double
    var range: ClosedRange<Double>
    var fmt: String
    var onChange: () -> Void
    @State private var dragging = false
    var body: some View {
        HStack(spacing: 10) {
            Text(label).font(.system(size: 13)).foregroundColor(DS.fg).frame(width: 150, alignment: .leading)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(DS.track).frame(height: 4)
                    Capsule().fill(dragging ? DS.accent : DS.fg).frame(width: max(0, geo.size.width * progress), height: 4)
                    Circle().fill(Color.white).frame(width: 16, height: 16)
                        .shadow(color: Color.black.opacity(0.15), radius: 4, x: 0, y: 2)
                        .overlay(Circle().stroke(dragging ? DS.accent : Color(hex: 0xCBD5E1), lineWidth: 1.5))
                        .offset(x: max(0, min(geo.size.width - 16, geo.size.width * progress - 8)))
                }
                .contentShape(Rectangle())
                .gesture(DragGesture(minimumDistance: 0).onChanged { g in
                    dragging = true
                    let pct = max(0, min(1, g.location.x / geo.size.width))
                    value = range.lowerBound + pct * (range.upperBound - range.lowerBound)
                    onChange()
                }.onEnded { _ in dragging = false; onChange() })
            }.frame(height: 16)
            StepperControl(value: $value, range: range, fmt: fmt, onChange: onChange)
        }
    }
    var progress: Double { (value - range.lowerBound) / (range.upperBound - range.lowerBound) }
}

struct StepperControl: View {
    @Binding var value: Double
    var range: ClosedRange<Double>
    var fmt: String
    var onChange: () -> Void
    var body: some View {
        HStack(spacing: 6) {
            Button(action: { value = max(range.lowerBound, value - 1); onChange() }) {
                Image(systemName: "minus").font(.system(size: 10, weight: .bold)).frame(width: 26, height: 26)
                    .background(DS.card).overlay(RoundedRectangle(cornerRadius: 6).stroke(DS.border, lineWidth: 1))
            }.buttonStyle(.plain)
            Text(String(format: fmt, value)).font(.system(size: 12, weight: .bold, design: .monospaced)).foregroundColor(DS.fg).frame(width: 62).multilineTextAlignment(.center)
            Button(action: { value = min(range.upperBound, value + 1); onChange() }) {
                Image(systemName: "plus").font(.system(size: 10, weight: .bold)).frame(width: 26, height: 26)
                    .background(DS.card).overlay(RoundedRectangle(cornerRadius: 6).stroke(DS.border, lineWidth: 1))
            }.buttonStyle(.plain)
        }
    }
}

struct FluentSliderRow: View {
    var label: String; @Binding var value: Double; var range: ClosedRange<Double>; var fmt: String; var onChange: ()->Void
    var body: some View { FluentSlider(label: label, value: $value, range: range, fmt: fmt, onChange: onChange) }
}

struct VerdictBlock: View {
    var text: String
    var body: some View {
        Text(text).font(.system(size: 13)).foregroundColor(DS.fg).lineSpacing(2)
            .padding(12).frame(maxWidth: .infinity, alignment: .leading)
            .background(DS.card2).clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(DS.border, lineWidth: 1))
    }
}
