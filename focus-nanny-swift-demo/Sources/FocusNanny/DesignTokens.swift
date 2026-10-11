import SwiftUI

enum DS {
    static let bg = Color(hex: 0xF1F5F9)
    static let card = Color.white
    static let card2 = Color(hex: 0xF8FAFC)
    static let border = Color(hex: 0xE2E8F0).opacity(0.95)
    static let fg = Color(hex: 0x0F172A)
    static let muted = Color(hex: 0x334155)
    static let sub = Color(hex: 0x64748B)
    static let accent = Color(hex: 0x0EA5E9)
    static let accentHover = Color(hex: 0x0284C7)
    static let track = Color(hex: 0xE2E8F0)
    static let gWork = Color(hex: 0x10B981)
    static let gYtEdu = Color(hex: 0x0EA5E9)
    static let gYt = Color(hex: 0xF59E0B)
    static let gGame = Color(hex: 0xF43F5E)
    static let gOther = Color(hex: 0xCBD5E1)
    static let gIdle = Color(hex: 0x94A3B8)
    static let radius: CGFloat = 12
    static let cardShadow = Color.black.opacity(0.06)
}

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xFF)/255, green: Double((hex >> 8) & 0xFF)/255, blue: Double(hex & 0xFF)/255, opacity: opacity)
    }
}

struct CardModifier: ViewModifier {
    var padding: CGFloat = 18
    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(DS.card)
            .clipShape(RoundedRectangle(cornerRadius: DS.radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: DS.radius, style: .continuous).stroke(DS.border, lineWidth: 1))
            .shadow(color: DS.cardShadow, radius: 14, x: 0, y: 6)
            .shadow(color: DS.cardShadow.opacity(0.6), radius: 2, x: 0, y: 1)
    }
}
extension View { func card(padding: CGFloat = 18) -> some View { modifier(CardModifier(padding: padding)) } }
