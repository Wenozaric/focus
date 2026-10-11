import SwiftUI

enum Category: String, CaseIterable, Codable, Identifiable {
    case work, youtubeEdu = "youtube_edu", youtube, game, idle, other
    var id: String { rawValue }
    var label: String {
        switch self {
        case .work: return "Работа"
        case .youtubeEdu: return "YouTube · учёба"
        case .youtube: return "YouTube"
        case .game: return "Игры"
        case .idle: return "Простой"
        case .other: return "Прочее"
        }
    }
    var color: Color {
        switch self {
        case .work: return DS.gWork
        case .youtubeEdu: return DS.gYtEdu
        case .youtube: return DS.gYt
        case .game: return DS.gGame
        case .idle: return DS.gIdle
        case .other: return DS.gOther
        }
    }
    var icon: String {
        switch self {
        case .work: return "hammer.fill"
        case .youtubeEdu: return "graduationcap.fill"
        case .youtube: return "play.rectangle.fill"
        case .game: return "gamecontroller.fill"
        case .idle: return "moon.fill"
        case .other: return "ellipsis.circle.fill"
        }
    }
}
